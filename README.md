# VIWTools VPM Repository

複数のUnityパッケージをALCOM/VCCへ配布する、**Listing生成専用**リポジトリです。ツール本体のソース・ビルド・Releasesは各ツールのリポジトリで管理します。

登録URL: **https://mia2viw.github.io/vpm-repos/index.json**

配布ページ: https://mia2viw.github.io/vpm-repos/

## 構成

```text
mia2viw/vpm-repos                    配布一覧だけを生成・公開
  source.json                       掲載するリポジトリを列挙
  scripts/build_listing.py           ReleasesのmanifestとZIPを検証して一覧を生成
  .github/workflows/build-listing.yml

mia2viw/net.vviw.scene-changer        Scene changer本体
  Packages/net.vviw.scene-changer/    Unityパッケージ
  scripts/build_package.py           配布ZIPを生成・検証
  .github/workflows/release.yml      GitHub Releasesへ公開
```

## 掲載するツールを増やす

1. 新しいツールの専用GitHubリポジトリを作り、パッケージIDとフォルダーを `net.vviw.<package-name>` に統一します。
2. 専用リポジトリのReleasesへ `<package-id>-<version>.zip` と `package.json` を同じリリースの添付ファイルとして公開します。ZIP直下にpackage.jsonを含め、添付manifestと一致させてください。
3. このリポジトリのsource.jsonのgithubReposに `mia2viw/新しいリポジトリ名` を追加してmainへ反映します。
4. Actionsの **Build Repo Listing** の成功を確認します。

```json
"githubRepos": [
  "mia2viw/net.vviw.scene-changer",
  "mia2viw/net.vviw.another-tool"
]
```

`packages` 配列には、GitHub Releases以外に置いたZIPを `{ "name": "net.vviw.example", "releases": ["https://example.com/package.zip"] }` の形式で指定できます。URLはHTTPSに限ります。

## 一覧の更新

- source.jsonや生成処理を変更したときは自動実行します。
- 各ツールの新しいリリースは約15分間隔の定期実行で検出します。GitHub側の混雑などで遅れることがあります。
- すぐに反映したい場合は **Actions > Build Repo Listing > Run workflow** を実行します。
- 将来の外部通知用にrepository_dispatchの `build-listing` も受け付けます。現在は通知用PATや追加Secretsを作成・使用しません。

GitHub PagesのSourceは **GitHub Actions** に設定します。内容の取得や検証に失敗した場合は公開処理を止め、前回成功したPagesの内容を保持します。公開済みのバージョンとZIPは各ツール側で保持してください。GitHubで削除された過去リリースを自動復元する機能はありません。

## 検証と権利

Python 3の標準ライブラリだけを使用します。`python3 -m unittest discover -s tests -v` で一覧生成のテストを実行できます。CIでは各ZIPのルートmanifest、添付manifestとの一致、ZIPパス、SHA256も確認します。

自作コードはMIT Licenseです。[LICENSE.md](LICENSE.md)、[利用条件・第三者の権利表示](THIRD_PARTY_NOTICES.md)を参照してください。

[Azukimochi/vpm-repos](https://github.com/Azukimochi/vpm-repos) の「Listing専用リポジトリとsource.json」の構成を参考にしました。参考リポジトリのコード・画像・ブランド素材は複製していません。一覧データは [VRChat公式のVPMリポジトリ形式](https://vcc.docs.vrchat.com/vpm/repos/) に従って生成します。
