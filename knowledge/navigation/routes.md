---
generated_at: 2026-06-29
code_sources:
  - careecon_work_frontend/src/pages/
status: draft
---

# 画面ナビゲーションマップ

ベースURL: `/companies/:company_id`

## 認証・初期設定

| URL | ページ | 説明 |
|---|---|---|
| `/sign_in` | ログイン | - |
| `/logout` | ログアウト | - |
| `/sessions/callback` | 認証コールバック | - |
| `/sessions/invitation` | 招待からの参加 | - |
| `/initial-settings/company-profile` | 初期設定：会社プロフィール | - |
| `/initial-settings/invite-members` | 初期設定：メンバー招待 | - |
| `/initial-settings/user-profile` | 初期設定：ユーザープロフィール | - |
| `/companies` | 会社一覧 | 複数会社に所属する場合の切り替え |

## 会社トップ

| URL | ページ | 説明 |
|---|---|---|
| `/companies/:id/projects` | 案件一覧（トップ） | ログイン後のホーム画面 |
| `/companies/:id/projects/index` | 案件一覧 | - |
| `/companies/:id/projects/new` | 案件作成 | - |
| `/companies/:id/projects/calendar` | カレンダービュー | 案件をカレンダーで表示 |
| `/companies/:id/projects/gantt-chart` | ガントチャート（会社全体） | 全案件の工程を俯瞰 |
| `/companies/:id/projects/member-allocation` | メンバーアサイン | メンバーごとの工程割り当て管理 |
| `/companies/:id/members` | メンバー管理 | - |
| `/companies/:id/profile` | 会社プロフィール | - |
| `/companies/:id/setting` | 設定 | - |
| `/companies/:id/construction-kinds` | 工種一覧 | - |
| `/companies/:id/construction-kinds/new` | 工種作成 | - |
| `/companies/:id/customers` | 顧客一覧 | - |
| `/companies/:id/customers/new` | 顧客作成 | - |
| `/companies/:id/customers/:id` | 顧客詳細 | - |
| `/companies/:id/customers/:id/edit` | 顧客編集 | - |
| `/companies/:id/user-profile` | ユーザープロフィール | - |
| `/companies/:id/unavailability` | 休暇・不在設定 | - |
| `/companies/:id/expiration` | 有効期限 | プラン期限切れ時 |
| `/companies/:id/sharing-contents` | 共有コンテンツ | - |
| `/companies/:id/files/:id` | ファイル詳細 | - |
| `/companies/:id/files/:id/edit` | ファイル編集 | - |
| `/companies/:id/files/:id/preview` | ファイルプレビュー | - |

## 案件（project）配下

| URL | ページ | 説明 |
|---|---|---|
| `/projects/:id` | 案件トップ | - |
| `/projects/:id/index` | 案件トップ（別）| - |
| `/projects/:id/detail` | 案件詳細 | - |
| `/projects/:id/member` | 案件メンバー管理 | - |
| `/projects/:id/card` | カード（タスクボード）| - |

### 工程表

| URL | ページ | 説明 |
|---|---|---|
| `/projects/:id/schedule` | 工程表（メイン） | ガントチャート編集画面 |
| `/projects/:id/schedule/fullscreen` | 工程表（全画面） | - |
| `/projects/:id/schedule/preview` | 工程表プレビュー | 公開前の確認 |
| `/projects/:id/schedule/print` | **工程表印刷** | 印刷設定・印刷プレビュー |
| `/projects/:id/schedule/view` | 工程表（閲覧モード） | 共有相手向け |
| `/projects/:id/schedule/view/fullscreen` | 工程表（閲覧・全画面） | - |
| `/project/:id/schedule/pdf` | 工程表PDF | PDF出力 |

### 掲示板

| URL | ページ | 説明 |
|---|---|---|
| `/projects/:id/board_posts` | 掲示板トップ | - |
| `/projects/:id/board_posts/index` | 掲示板一覧 | - |
| `/projects/:id/board_posts/new` | 投稿作成 | - |
| `/projects/:id/board_posts/posts` | 投稿一覧（別ビュー） | - |
| `/projects/:id/board_posts/:board_id` | 投稿詳細 | - |
| `/projects/:id/board_posts/:board_id/edit` | 投稿編集 | - |
| `/projects/:id/board_posts/:board_id/files` | 投稿添付ファイル一覧 | - |

### 日報

| URL | ページ | 説明 |
|---|---|---|
| `/projects/:id/reports` | 日報一覧 | - |
| `/projects/:id/reports/select-daily-reports` | 日報選択 | 日報から工事報告書を作成する際の選択画面 |
| `/projects/:id/reports/:report_id/form` | 日報作成・編集 | - |
| `/projects/:id/reports/:report_id/preview` | 日報プレビュー | - |

### 勤怠

| URL | ページ | 説明 |
|---|---|---|
| `/projects/:id/attendance` | 勤怠管理 | - |
| `/projects/:id/attendance/summary` | 勤怠サマリー | - |
| `/projects/:id/attendance/user-list` | ユーザー別勤怠一覧 | - |
| `/projects/:id/attendance/user-records` | ユーザー別勤怠記録 | - |

### ファイル

| URL | ページ | 説明 |
|---|---|---|
| `/projects/:id/files/:file_id` | ファイル詳細 | - |
| `/projects/:id/files/:file_id/edit` | ファイル編集 | - |
| `/projects/:id/files/:file_id/preview` | ファイルプレビュー | - |

## その他

| URL | ページ | 説明 |
|---|---|---|
| `/contents/:uuid` | コンテンツ（共有リンク） | ログイン不要の共有コンテンツ閲覧 |
| `/companies/:id/reports/:id` | 工事報告書詳細 | - |
| `/companies/:id/reports/:id/edit` | 工事報告書編集 | - |
| `/companies/:id/reports/:id/pdf` | 工事報告書PDF | - |
| `/companies/:id/reports/:id/ai_pdf` | 工事報告書AI PDF | - |

---

## [Human] 補足・注意事項
<!-- 人間が追記するセクション -->

