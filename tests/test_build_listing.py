import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location("listing", Path(__file__).resolve().parents[1] / "scripts/build_listing.py")
listing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(listing)


class ListingTests(unittest.TestCase):
    def setUp(self):
        self.source = {"name": "Tools", "id": "net.vviw.test", "url": "https://example.com/index.json", "author": {"name": "Author"}, "githubRepos": ["owner/a", "owner/b"], "packages": []}
        self.data = {}
        for repo in self.source["githubRepos"]:
            releases = []
            for version in ("0.2.1", "0.2.2", "0.3.0-beta.1"):
                name = "net.vviw." + repo.split("/")[1]
                manifest = {"name": name, "version": version, "license": "MIT"}
                base = f"https://example.com/{repo}/{version}/"
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w") as archive:
                    archive.writestr("package.json", json.dumps(manifest))
                self.data[base + "package.json"] = json.dumps(manifest).encode()
                self.data[base + "package.zip"] = buf.getvalue()
                releases.append({"tag_name": version, "assets": [{"name": "package.json", "browser_download_url": base + "package.json"}, {"name": f"{name}-{version}.zip", "browser_download_url": base + "package.zip"}]})
            self.data[f"https://api.github.com/repos/{repo}/releases?per_page=100&page=1"] = json.dumps(releases).encode()

    def collect(self):
        return listing.collect(self.source, self.data.__getitem__)

    def test_multiple_packages_and_all_versions_are_retained(self):
        result = self.collect()
        self.assertEqual(set(result["packages"]), {"net.vviw.a", "net.vviw.b"})
        self.assertEqual(len(result["packages"]["net.vviw.a"]["versions"]), 3)
        self.assertEqual(len(result["packages"]["net.vviw.a"]["versions"]["0.2.2"]["zipSHA256"]), 64)

    def test_missing_zip_does_not_publish_partial_listing(self):
        key = "https://api.github.com/repos/owner/a/releases?per_page=100&page=1"
        releases = json.loads(self.data[key])
        releases[0]["assets"].pop()
        self.data[key] = json.dumps(releases).encode()
        with self.assertRaisesRegex(ValueError, "Missing"):
            self.collect()

    def test_metadata_must_match_zip(self):
        self.data["https://example.com/owner/a/0.2.1/package.json"] = json.dumps({"name": "net.vviw.a", "version": "0.2.1", "license": "other"}).encode()
        with self.assertRaisesRegex(ValueError, "differ"):
            self.collect()

    def test_explicit_zip_source(self):
        self.source["githubRepos"] = []
        self.source["packages"] = [{"name": "net.vviw.a", "releases": ["https://example.com/owner/a/0.2.1/package.zip"]}]
        self.assertIn("net.vviw.a", self.collect()["packages"])

    def test_html_escapes_package_text_and_shows_stable_version(self):
        result = self.collect()
        result["packages"]["net.vviw.a"]["versions"]["0.2.2"]["displayName"] = '<script>alert("x")</script>'
        with tempfile.TemporaryDirectory() as directory:
            listing.write_listing(result, directory)
            html = (Path(directory) / "index.html").read_text(encoding="utf-8")
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn("<script>", html)
            self.assertIn("0.2.2", html)
            self.assertEqual(json.loads((Path(directory) / "index.json").read_text(encoding="utf-8")), result)

    def test_empty_repository_is_an_error(self):
        self.data["https://api.github.com/repos/owner/a/releases?per_page=100&page=1"] = b"[]"
        with self.assertRaisesRegex(ValueError, "No compatible"):
            self.collect()

    def test_zip_with_parent_traversal_is_rejected(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as archive:
            archive.writestr("package.json", '{"name":"net.vviw.a","version":"1.0.0"}')
            archive.writestr("../outside.txt", "unexpected")
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            listing.manifest_from_zip("https://example.com/package.zip", lambda _: buf.getvalue())


if __name__ == "__main__":
    unittest.main()
