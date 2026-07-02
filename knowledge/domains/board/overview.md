---
domain: board/overview
generated_at: 2026-07-02
code_sources:
  - careecon_work/app/models/board_post.rb
  - careecon_work/app/models/board_post_comment.rb
  - careecon_work/app/models/board_category.rb
  - careecon_work/Schemafile (board_posts, board_categories, board_post_users, board_post_comment_confirmed_users)
  - careecon_work/app/policies/board_post_policy.rb
  - careecon_work/app/policies/board_post_comment_policy.rb
  - careecon_work/app/services/board_post/create_service.rb
  - careecon_work/app/services/board_post/update_service.rb
  - careecon_work/app/services/board_post/read_service.rb
  - careecon_work/app/services/board_post/confirm_service.rb
  - careecon_work/app/services/board_post/mute_service.rb
  - careecon_work/app/services/board_post/search_service.rb
  - careecon_work/app/services/board_post_comment/create_service.rb
  - careecon_work/app/services/notification/create_board_post_service.rb
  - careecon_work/app/services/notification/create_board_post_comment_service.rb
  - careecon_work/app/controllers/api/v1/board_posts_controller.rb
  - careecon_work/app/controllers/api/v1/board_post_comments_controller.rb
  - careecon_work/config/routes.rb (board_posts nested routes)
  - careecon_work/app/graphql/types/object_types/board_post_type.rb
  - careecon_work/app/graphql/resolvers/board_post_collection_resolver.rb
  - careecon_work_frontend/src/pages/companies/_company_id/projects/_id/board_posts/index.vue
  - careecon_work_frontend/src/pages/companies/_company_id/projects/_id/board_posts/posts/index.vue
  - careecon_work_frontend/src/pages/companies/_company_id/projects/_id/board_posts/new.vue
  - careecon_work_frontend/src/pages/companies/_company_id/projects/_id/board_posts/_board_id/index.vue
  - careecon_work_frontend/src/pages/companies/_company_id/projects/_id/board_posts/_board_id/edit.vue
  - careecon_work_frontend/src/components/board/templates/home.vue
  - careecon_work_frontend/src/components/board/templates/post-list.vue
  - careecon_work_frontend/src/components/board/organisms/post-form.vue
  - careecon_work_frontend/src/components/board/organisms/post-comments.vue
  - careecon_work_frontend/src/components/board/molecules/post-card.vue
  - careecon_work_frontend/src/components/board/molecules/post-detail-header.vue
  - careecon_work_frontend/src/store/board.ts
  - careecon_work_frontend/src/types/board.ts
  - careecon_work_frontend/src/plugins/apis/board-api-client.ts
status: draft
last_reviewed_by: ~
---

# 掲示板（Board Post）

## 概要

案件（プロジェクト）単位のお知らせ・連絡機能。内部名は `BoardPost`。
カテゴリ別に投稿を分類でき、コメント・添付ファイル・既読管理・通知（全員 or 個別指定）・
「必読」フラグ・「了解（confirm）」機能を持つ。日報（daily_report）から生成される投稿は
掲示板側では削除できず、日報編集モーダル経由でのみ編集・削除される特殊系統がある。

ナビゲーション: `案件 > 掲示板`
URL:
- `/companies/:company_id/projects/:project_id/board_posts` — トップ（カテゴリ別ホーム）
- `.../board_posts/posts` — 全件/カテゴリ絞り込みリスト
- `.../board_posts/new` — 新規作成
- `.../board_posts/:board_id` — 詳細（コメント欄含む）
- `.../board_posts/:board_id/edit` — 編集
- `.../board_posts/:board_id/files` — 添付ファイル一覧

---

## データモデル

### BoardPost（投稿）

| フィールド | 型 | 説明 |
|---|---|---|
| `project_id` | FK | 案件 |
| `board_category_id` | FK | カテゴリ |
| `company_id` | FK | 会社 |
| `created_user_id` / `last_updated_user_id` | FK | 投稿者・最終更新者 |
| `daily_report_id` | FK（nullable, unique） | 日報から生成された投稿の場合のみセット |
| `title` | string | 必須 |
| `body` | text | 本文 |
| `upload_content_id` | string | 同時アップロードした添付をグルーピングするID |
| `read_required` | boolean | 「必読」フラグ |
| `notice_target_type` | enum | `project_all_users`(1, デフォルト) / `selected_users`(2) |
| `notice_target_uids` | serialized array | レガシー。旧クライアント互換のため残存（FIXME: 削除予定） |
| `read_users` / `confirmed_users` | serialized array | レガシー。`board_post_users` に置き換え済みの旧デノーマライズ列 |
| `activity_type` | enum | `created`(0) / `updated`(1) / `commented`(2) / `comment_deleted`(3) |
| `acted_at` | timestamp | 「〇〇さんが投稿しました」等アクティビティ表示用の日時 |
| `edited_at` | timestamp | 編集日時 |
| `process_group_id` | - | 同時アップロードした `Content` バッチとの紐付け |

リレーション: `belongs_to :project, :board_category, :company, :created_user, :last_updated_user, :daily_report`／
`has_many :board_post_comments, :content_resources（添付, polymorphic）, :board_post_users`

### BoardPostUser（既読・了解・通知対象の中間テーブル）

| フィールド | 説明 |
|---|---|
| `board_post_id` / `user_id` | 複合キー的に機能 |
| `read_at` | 既読日時（nullable = 未読） |
| `confirmed_at` | 「了解」した日時（nullable = 未了解） |
| `notice_target` | 通知対象かどうか |

旧来 `board_posts.read_users` / `confirmed_users`（配列）で管理していたものを
ユーザー単位のレコードに正規化したテーブル。**現行の既読・通知管理はこちらが正**。

### BoardPostComment（コメント）

| フィールド | 説明 |
|---|---|
| `board_post_id` / `user_id` | 投稿・コメント者 |
| `body` | 保存時にサニタイズ |
| `mentioned_uids` | serialized array（@メンション対象） |
| `confirmed_users` | レガシー serialized array（「いいね」的な確認） |
| `edited_at` | 編集日時 |

`has_many :board_post_comment_confirmed_users`（コメント単位の「了解」実体テーブル）、
添付は `content_resources`。

### BoardCategory（カテゴリ）

| フィールド | 説明 |
|---|---|
| `company_id` | 会社単位で定義 |
| `name` | カテゴリ名 |
| `template_body` | 投稿作成時に本文へ自動挿入されるテンプレート |
| `annotation` | 補足説明 |

「日報」カテゴリは特別扱い（工程・日報フローが存在するプロジェクトでは非表示になる）。

---

## API / GraphQL

REST（`api/v1/companies/:company_id/projects/:project_id/board_posts`）:

```
GET/POST      /board_posts
GET/PATCH/DELETE /board_posts/:id
PATCH         /board_posts/:id/confirm            # 「了解」トグル
GET           /board_posts/:id/board_post_users    # 既読/未読ユーザー一覧
PATCH         /board_posts/:id/notice_unread_users # 未読者へ再通知
PATCH         /board_posts/:id/mute                # 実質未使用（下記参照）
GET           /board_posts/:id/mentionable_users

GET/POST      /board_posts/:board_post_id/board_post_comments
PATCH/DELETE  /board_posts/:board_post_id/board_post_comments/:id
PATCH         .../:id/confirm
GET           .../:id/confirmed_users

GET /api/v1/companies/:company_id/board_posts   # 会社横断（プロジェクト非指定）
GET /api/v1/.../board_categories
```

GraphQL: `Types::ObjectTypes::BoardPostType`（`current_user_confirmed`, `confirmed_users_count`,
`current_user_read`, `comment_count`, `activity`（整形済みリッチテキスト配列）, `policies` 等を公開）。
`Resolvers::BoardPostCollectionResolver`（引数: `web_home_response, project_id, board_category_id, text`）は
**REST と同じ `BoardPost::SearchService` を呼び出す** — サービス層共有パターンの実例。

---

## ビジネスロジック（Service層）

- **`CreateService`** — 投稿作成、添付を `content_resources` に紐付け、通知対象全員分の
  `BoardPostUser` を作成（`project_all_users` ならプロジェクト全メンバー、`selected_users` なら指定uidのみ）、
  Firestore通知ジョブを enqueue（添付アップロード未完了時は完了までスキップ）。
- **`UpdateService`** — タイトル/本文/必読フラグ変更時に `activity_type` を `updated` に変更。
  通知対象の差分を `board_post_users.notice_target` に反映（旧クライアント向けにuid差分から
  `notice_target_type` を推測するFIXMEロジックあり）。
- **`ReadService`** — 詳細画面表示時に冪等に `read_at` をセット。既読バッジ更新ジョブとFirestore状態更新を発火。
- **`ConfirmService`** — `confirmed_at` のトグル（「了解」ボタン）。
- **`MuteService`** — コード内コメントで「Mute機能が今ないので無視」と明記。**実質未使用**。
- **`SearchService`** — `project_id` / `board_category_id` / フリーテキスト（title・body LIKE）検索。
  `web_home_response: true` でホーム画面用（カテゴリごとに直近更新5件、`ROW_NUMBER`パーティション）を返す特殊モード。
- **`BoardPostComment::CreateService`** — コメント作成、親投稿の `activity_type` を `commented` に、
  `acted_at` を更新、Firestore状態更新後に `Notification::CreateBoardPostCommentService` を呼び出す。
- **`Notification::CreateBoardPostService` / `...CommentService`** — 通知はSQLの専用テーブルではなく
  Firebase/Firestore経由（`Firebase::Firestore::UpsertUserBadgeJob`）でpush/アプリ内通知を送信。
  通知対象は投稿の場合 `notice_target` ユーザー、コメントの場合は投稿の通知対象からコメント者自身を除いたもの。
  `notice_unread_users` は現在未読のユーザーだけに再通知する。

---

## 権限（認可）

Policy: `board_post_policy.rb` / `board_post_comment_policy.rb`（Action Policy）。

| アクション | ルール |
|---|---|
| index | 常にtrue（scopeで絞り込み。guestは自分がアサインされた案件のみ） |
| show | over_member（guest以外）は同一会社なら可。guestは同一会社かつ案件アサイン必須 |
| create | super_admin、または案件にアサインされたユーザー |
| update | 日報非紐付け: 投稿者本人のみ／日報紐付け: `DailyReportPolicy#update?` に委譲（掲示板UIは日報編集モーダルへ誘導するだけ） |
| destroy | 日報非紐付け: admin または投稿者本人／**日報紐付け: 常にfalse**（削除は日報編集モーダル経由のみ） |
| confirm / mute | `board_post_users` に自分が対象として登録されている場合のみ |
| notice_unread_users | admin または投稿者、かつ日報非紐付けの投稿のみ |
| コメント create | 投稿のcreateと同条件 |
| コメント update/destroy | コメント投稿者本人（destroyは会社admin も可） |

---

## FEコンポーネント構成

```
pages/board_posts/
├── index.vue        → templates/home.vue（カテゴリごとに直近5件、web_home_response）
├── posts/index.vue   → templates/post-list.vue（カテゴリ/テキストで絞り込み全件リスト）
├── new.vue           → organisms/post-form.vue
├── _board_id/
│   ├── index.vue     → 詳細（post-detail-header.vue + post-comments.vue）
│   ├── edit.vue       → post-form.vue（isEdit）
│   └── files/index.vue
```

Store: `src/store/board.ts`（Vuexモジュール `board`）が fetch/create/update/delete/confirm/mute/notice
アクションを集約。API呼び出しは `board-api-client.ts` 経由。

### 新規作成・編集フォーム（post-form.vue）

| 項目 | UI要素 | 備考 |
|---|---|---|
| カテゴリ | セレクト | 変更時「テンプレート本文を使用するか」ダイアログ→ `template_body` を差し込める |
| タイトル | テキスト（必須） | |
| 添付 | ファイル選択 / 過去アップロード済みから選択 | プレビューダイアログあり |
| 通知先 | ラジオ（全員に通知 / 指定して通知） | 指定時はメンバーピッカーで `notice_target_uids` を選択 |
| 必読 | トグル | `read_required` |
| 本文 | テキストエリア | カテゴリテンプレートで自動プリフィル |

### 一覧カード（post-card.vue）

必読タグ、タイトル、本文抜粋（3行 or 文字数で省略）、添付サムネイル、
フッター（投稿者名・投稿/編集日時・了解数アイコン・コメント数アイコン）。

### 詳細画面（post-detail-header.vue / post-detail.vue / post-comments.vue）

- パンくず、必読タグ、タイトル、「…」メニュー（`policies.update`/`destroy` が true の場合のみ編集/削除表示。
  日報紐付け投稿は削除不可のためメニューから外れる）
- 既読数表示 → クリックで既読/未読タブ付きダイアログ（ユーザーごとの既読時刻）。
  `policies.notice_unread_users` が true かつ未読者がいる場合のみ「未読のユーザーへお知らせする」ボタンを表示
- コメント数 → コメント欄へスクロール／添付ファイル数 → ファイル一覧ページへ遷移
- コメント欄はページネーション（前へ/次へ）、@メンション対応（`mentionable_users` から取得）、
  添付可能、コメントへの「了解」トグルあり。コメントフォームは `policies.board_post_comments.create` が
  true の場合のみ表示

### 既読/通知フロー

- 詳細画面を開くと BE `ReadService` が呼ばれ自動的に既読になる
- 投稿作成・コメント作成時に Firebase 経由でアプリ内通知＋push通知（対象は `notice_target` ユーザー）
- 「未読のユーザーへお知らせする」ボタンで未読者だけに再通知可能

---

## [Human] 背景・意図
<!-- 人間が追記するセクション。Claudeは上書きしない -->


## [Human] 注意事項・例外・経緯
<!-- 人間が追記するセクション。Claudeは上書きしない -->


## [Human] 未解決の疑問・TODO
<!-- 人間が追記するセクション。Claudeは上書きしない -->
