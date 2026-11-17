# Third-party licenses and service terms

確認日: 2026-11-17。

自作コードは所有者の指定によりMIT Licenseです。第三者の許諾・サービス条件を置き換えるものではありません。

## GitHub / Actions / Pages / GitHub API

ソース保管、配布ZIPの公開、公開リリース情報の読み取り、VPM Listingの生成とGitHub Pagesへの公開に利用します。ツール内の個人設定、背景素材、認証情報は公開しません。自作プロジェクトのビルド・検証・公開という用途について、現在の実装では条件を満たして利用可能と判断しています。アカウントのプラン、実行時間・容量・API制限など、GitHubの現行条件には引き続き従います。

- https://docs.github.com/en/site-policy/github-terms/github-terms-of-service
- https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features
- https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api

認証にはActionsが各実行へ発行するGITHUB_TOKENだけを使います。Listing側はcontents:read、Pages公開にpages:write/id-token:writeを使用します。本体側は自身のRelease作成のためcontents:writeを使用します。リポジトリ間の通知用PATや追加の永続キーは作成しません。

## GitHub公式Actions

各workflowのusesで参照しCI環境内で実行します。Actions本体をUnityパッケージへ同梱しません。該当するMITライセンス原文と著作権表示はlicenses/に保持しています。

- actions/checkout v4: https://github.com/actions/checkout/blob/v4/LICENSE
- actions/configure-pages v5: https://github.com/actions/configure-pages/blob/v5/LICENSE
- actions/upload-pages-artifact v3: https://github.com/actions/upload-pages-artifact/blob/v3/LICENSE
- actions/deploy-pages v4: https://github.com/actions/deploy-pages/blob/v4/LICENSE

Release作成にはGitHubホストランナーに既設のGitHub CLIを使います。Pythonとその標準ライブラリ、GitHub CLIのバイナリやソースは再配布しません。

## 構成の参考とVPM仕様

https://github.com/Azukimochi/vpm-repos のsource.jsonとListing専用リポジトリという構造を参考にしています。参考先のコード・画像は複製していません。独自のPython標準ライブラリによる実装で、公式VPMリポジトリ仕様に従いJSONを生成します。

- https://vcc.docs.vrchat.com/vpm/repos/
- https://vcc.docs.vrchat.com/vpm/packages/

外部CDN・UIライブラリ・素材は配布ページに使用しません。各ツールが利用するライブラリや利用者の背景素材は、それぞれの条件に従います。

