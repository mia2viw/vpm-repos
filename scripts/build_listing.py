"""Build a multi-package VPM listing from GitHub release assets; no external libraries."""
import hashlib
from html import escape
import io
import json
import os
from pathlib import Path
import re
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
import zipfile


SEMVER = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?")


def read_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Only HTTPS URLs are accepted")
    headers = {"User-Agent": "VIWTools-VPM-Listing", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN", "")
    if token and parsed.hostname == "api.github.com":
        headers["Authorization"] = "Bearer " + token
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return response.read()


def manifest_from_zip(url, read=read_url):
    data = read(url)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        if "package.json" not in names:
            raise ValueError("package.json must be at the ZIP root")
        if len(names) != len(set(names)) or any(n.startswith(("/", "\\")) or ".." in n.replace("\\", "/").split("/") for n in names):
            raise ValueError("Unsafe or duplicate ZIP paths")
        manifest = json.loads(archive.read("package.json"))
    manifest["url"] = url
    manifest["zipSHA256"] = hashlib.sha256(data).hexdigest()
    return manifest


def collect(source, read=read_url):
    for required in ("name", "id", "url", "author"):
        if not source.get(required):
            raise ValueError(f"Missing listing field: {required}")
    if urlparse(source["url"]).scheme != "https":
        raise ValueError("Listing URL must use HTTPS")
    result = {k: source[k] for k in ("name", "id", "url", "author", "description", "infoLink") if k in source}
    result["packages"] = {}

    def add(manifest):
        name, version = manifest.get("name", ""), manifest.get("version", "")
        if not re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)+", name) or not SEMVER.fullmatch(version):
            raise ValueError("Invalid package ID or version")
        versions = result["packages"].setdefault(name, {"versions": {}})["versions"]
        if version in versions and versions[version] != manifest:
            raise ValueError(f"Conflicting release for {name} {version}")
        versions[version] = manifest

    for repo in source.get("githubRepos", []):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError(f"Invalid repository: {repo}")
        count = 0
        page = 1
        while True:
            releases = json.loads(read(f"https://api.github.com/repos/{repo}/releases?per_page=100&page={page}"))
            if not isinstance(releases, list):
                raise ValueError(f"Invalid GitHub API response for {repo}")
            for release in releases:
                if release.get("draft"):
                    continue
                assets = {a["name"]: a for a in release.get("assets", [])}
                metadata = assets.get("package.json")
                if metadata is None:
                    continue
                manifest = json.loads(read(metadata["browser_download_url"]))
                expected = f"{manifest.get('name')}-{manifest.get('version')}.zip"
                if expected not in assets:
                    raise ValueError(f"Missing {expected} in {repo} release {release.get('tag_name')}")
                package = manifest_from_zip(assets[expected]["browser_download_url"], read)
                # The published metadata and ZIP must describe the same package.
                if {k: v for k, v in package.items() if k not in ("url", "zipSHA256")} != {k: v for k, v in manifest.items() if k not in ("url", "zipSHA256")}:
                    raise ValueError(f"Release metadata and ZIP differ: {repo}")
                add(package)
                count += 1
            if len(releases) < 100:
                break
            page += 1
        if not count:
            raise ValueError(f"No compatible releases found: {repo}")

    for package in source.get("packages", []):
        for url in package.get("releases", []):
            manifest = manifest_from_zip(url, read)
            if manifest["name"] != package["name"]:
                raise ValueError("Explicit package name differs from ZIP")
            add(manifest)
    if not result["packages"]:
        raise ValueError("Refusing to publish an empty listing")
    return result


def write_listing(listing, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.json").write_text(json.dumps(listing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    listing_url = listing["url"]
    cards = []
    for name, package in sorted(listing["packages"].items()):
        manifests = list(package["versions"].values())
        # Listing contains all versions; the page displays a stable version when available.
        stable = [m for m in manifests if "-" not in m["version"].split("+")[0]]
        manifest = max(stable or manifests, key=lambda m: tuple(int(n) for n in m["version"].split("-")[0].split("+")[0].split(".")))
        cards.append(f'<article><h2>{escape(manifest.get("displayName", name))}</h2><p>{escape(manifest.get("description", ""))}</p><p><code>{escape(name)}</code> · {escape(manifest["version"])}</p><a href="{escape(manifest["url"], quote=True)}">Download ZIP</a></article>')
    html = ('<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(listing["name"])}</title><style>body{{font-family:system-ui,sans-serif;max-width:900px;margin:60px auto;padding:0 24px;background:#111827;color:#e5e7eb;line-height:1.8}}a{{color:#93c5fd}}article{{background:#1f2937;padding:20px 28px;margin:20px 0;border-radius:12px}}code{{overflow-wrap:anywhere}}.add{{display:inline-block;padding:10px 20px;background:#2563eb;color:white;border-radius:8px;text-decoration:none}}</style>'
            f'<h1>{escape(listing["name"])}</h1><p>ALCOM / VCC の「リポジトリ追加」に次の URL を登録してください。</p><p><code>{escape(listing_url)}</code></p>'
            f'<p><a class="add" href="vcc://vpm/addRepo?url={quote(listing_url, safe="")}">ALCOM / VCC に追加</a></p>'
            + ''.join(cards) + '<p><a href="https://github.com/mia2viw/vpm-repos">GitHub · 掲載ツールの追加方法</a></p></html>')
    (output / "index.html").write_text(html, encoding="utf-8")


def main():
    root = Path(__file__).resolve().parents[1]
    listing = collect(json.loads((root / "source.json").read_text(encoding="utf-8")))
    write_listing(listing, root / "Website")
    print(f"Validated listing: {len(listing['packages'])} packages, "
          f"{sum(len(p['versions']) for p in listing['packages'].values())} versions")


if __name__ == "__main__":
    main()
