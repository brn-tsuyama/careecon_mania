---
generated_at: 2026-06-29
code_sources:
  - careecon_work_frontend/src/pages/
status: draft
---

# 画面ナビゲーションマップ

ベースURL: `/companies/:company_id`

## ui_status の凡例

| 値 | 意味 |
|---|---|
| `pending` | UI knowledge 未取得 |
| `done` | knowledge ファイルに UI セクションあり |
| `outdated` | 画面変更あり・再キャプチャ必要 |

---

## 認証・初期設定

| URL | ページ | 説明 | ui_status |
|---|---|---|---|
| `/sign_in` | ログイン | - | pending |
| `/logout` | ログアウト | - | pending |
| `/sessions/callback` | 認証コールバック | - | pending |
| `/sessions/invitation` | 招待からの参加 | - | pending |
| `/initial-settings/user-profile` | 初期設定：ユーザープロフィール | - | pending |
| `/initial-settings/company-profile` | 初期設定：会社プロフィール | member/admin のみ | pending |
| `/initial-settings/guest-company-profile` | 初期設定：所属会社（ゲスト用） | guest のみ・新規設計 | pending |
| `/initial-settings/invite-members` | 初期設定：メンバー招待 | - | pending |
| `/companies` | 会社一覧 | 複数会社に所属する場合の切り替え | pending |

## 会社トップ

| URL | ページ | 説明 | ui_status |
|---|---|---|---|
| `/companies/:id/projects` | 案件一覧（トップ） | ログイン後のホーム画面 | pending |
| `/companies/:id/projects/index` | 案件一覧 | - | pending |
| `/companies/:id/projects/new` | 案件作成 | - | pending |
| `/companies/:id/projects/calendar` | カレンダービュー | 案件をカレンダーで表示 | pending |
| `/companies/:id/projects/gantt-chart` | ガントチャート（会社全体） | 全案件の工程を俯瞰 | pending |
| `/companies/:id/projects/member-allocation` | メンバーアサイン | メンバーごとの工程割り当て管理 | pending |
| `/companies/:id/members` | メンバー管理 | - | pending |
| `/companies/:id/profile` | 会社プロフィール | - | pending |
| `/companies/:id/setting` | 設定 | - | pending |
| `/companies/:id/construction-kinds` | 工種一覧 | - | pending |
| `/companies/:id/construction-kinds/new` | 工種作成 | - | pending |
| `/companies/:id/customers` | 顧客一覧 | - | pending |
| `/companies/:id/customers/new` | 顧客作成 | - | pending |
| `/companies/:id/customers/:id` | 顧客詳細 | - | pending |
| `/companies/:id/customers/:id/edit` | 顧客編集 | - | pending |
| `/companies/:id/user-profile` | ユーザープロフィール | - | pending |
| `/companies/:id/unavailability` | 休暇・不在設定 | - | pending |
| `/companies/:id/expiration` | 有効期限 | プラン期限切れ時 | pending |
| `/companies/:id/sharing-contents` | 共有コンテンツ | - | pending |
| `/companies/:id/files/:id` | ファイル詳細 | - | pending |
| `/companies/:id/files/:id/edit` | ファイル編集 | - | pending |
| `/companies/:id/files/:id/preview` | ファイルプレビュー | - | pending |

## 案件（project）配下

| URL | ページ | 説明 | ui_status |
|---|---|---|---|
| `/projects/:id` | 案件トップ | - | pending |
| `/projects/:id/index` | 案件トップ（別）| - | pending |
| `/projects/:id/detail` | 案件詳細 | - | pending |
| `/projects/:id/member` | 案件メンバー管理 | - | pending |
| `/projects/:id/card` | カード（タスクボード）| - | pending |

### 工程表

| URL | ページ | 説明 | ui_status |
|---|---|---|---|
| `/projects/:id/schedule` | 工程表（メイン） | ガントチャート編集画面 | pending |
| `/projects/:id/schedule/fullscreen` | 工程表（全画面） | - | pending |
| `/projects/:id/schedule/preview` | 工程表プレビュー | 公開前の確認 | pending |
| `/projects/:id/schedule/print` | **工程表印刷** | 印刷設定・印刷プレビュー | pending |
| `/projects/:id/schedule/view` | 工程表（閲覧モード） | 共有相手向け | pending |
| `/projects/:id/schedule/view/fullscreen` | 工程表（閲覧・全画面） | - | pending |
| `/project/:id/schedule/pdf` | 工程表PDF | PDF出力 | pending |

### 掲示板

| URL | ページ | 説明 | ui_status |
|---|---|---|---|
| `/projects/:id/board_posts` | 掲示板トップ | - | pending |
| `/projects/:id/board_posts/index` | 掲示板一覧 | - | pending |
| `/projects/:id/board_posts/new` | 投稿作成 | - | pending |
| `/projects/:id/board_posts/posts` | 投稿一覧（別ビュー） | - | pending |
| `/projects/:id/board_posts/:board_id` | 投稿詳細 | - | pending |
| `/projects/:id/board_posts/:board_id/edit` | 投稿編集 | - | pending |
| `/projects/:id/board_posts/:board_id/files` | 投稿添付ファイル一覧 | - | pending |

### 日報

| URL | ページ | 説明 | ui_status |
|---|---|---|---|
| `/projects/:id/reports` | 日報一覧 | - | pending |
| `/projects/:id/reports/select-daily-reports` | 日報選択 | 日報から工事報告書を作成する際の選択画面 | pending |
| `/projects/:id/reports/:report_id/form` | 日報作成・編集 | - | pending |
| `/projects/:id/reports/:report_id/preview` | 日報プレビュー | - | pending |

### 勤怠

| URL | ページ | 説明 | ui_status |
|---|---|---|---|
| `/projects/:id/attendance` | 勤怠管理 | - | pending |
| `/projects/:id/attendance/summary` | 勤怠サマリー | - | pending |
| `/projects/:id/attendance/user-list` | ユーザー別勤怠一覧 | - | pending |
| `/projects/:id/attendance/user-records` | ユーザー別勤怠記録 | - | pending |

### ファイル

| URL | ページ | 説明 | ui_status |
|---|---|---|---|
| `/projects/:id/files/:file_id` | ファイル詳細 | - | pending |
| `/projects/:id/files/:file_id/edit` | ファイル編集 | - | pending |
| `/projects/:id/files/:file_id/preview` | ファイルプレビュー | - | pending |

## その他

| URL | ページ | 説明 | ui_status |
|---|---|---|---|
| `/contents/:uuid` | コンテンツ（共有リンク） | ログイン不要の共有コンテンツ閲覧 | pending |
| `/companies/:id/reports/:id` | 工事報告書詳細 | - | pending |
| `/companies/:id/reports/:id/edit` | 工事報告書編集 | - | pending |
| `/companies/:id/reports/:id/pdf` | 工事報告書PDF | - | pending |
| `/companies/:id/reports/:id/ai_pdf` | 工事報告書AI PDF | - | pending |

---

## [Human] 補足・注意事項
<!-- 人間が追記するセクション -->
