---
domain: schedule/print
generated_at: 2026-06-29
code_sources:
  - careecon_work/app/models/published_schedule.rb
  - careecon_work/app/models/published_large_process.rb
  - careecon_work/app/models/published_small_process.rb
  - careecon_work/app/controllers/api/v2/published_large_processes_controller.rb
  - careecon_work/app/services/published_large_process/search_service.rb
  - careecon_work/app/services/published_schedule/search_service.rb
  - careecon_work_frontend/src/pages/companies/_company_id/projects/_id/schedule/print/index.vue
  - careecon_work_frontend/src/components/print/molecules/schedule-print-setting-dialog.vue
  - careecon_work_frontend/src/components/schedule/templates/print/preview.vue
  - careecon_work_frontend/src/mixins/schedule/fetch-published-schedule-mixin.ts
  - careecon_work_frontend/src/plugins/apis/v2/schedule-api-client.ts
status: draft
last_reviewed_by: ~
---

# 工程表印刷

## 概要

工程表の公開済みスケジュール（PublishedSchedule）をガントチャート形式で印刷・PDF出力する機能。
「現場に渡す1枚の紙」として使われる。

ナビゲーション: `案件 > 工程表 > 印刷`  
URL: `/companies/:company_id/projects/:project_id/schedule/print`

---

## データモデル

### PublishedSchedule（公開済みスケジュール）

工程表の「公開（スナップショット）」状態を保持するモデル。

| フィールド | 型 | 説明 |
|---|---|---|
| `project_id` | FK | 案件 |
| `company_id` | FK | 会社 |
| `user_id` | FK | 最終更新者 |
| `print_settings` | JSON | 印刷設定（後述） |

`print_settings` の構造:
```json
{
  "id": "設定ID",
  "date_range": ["2026-01-01", "2026-03-31"],
  "is_coloring": false,
  "is_company_logo": false,
  "is_small_process": false,
  "large_process_ids": ["id1", "id2"],
  "note": "注意事項テキスト（最大150文字）"
}
```

### PublishedLargeProcess（公開済み大工程）

| フィールド | 型 | 説明 |
|---|---|---|
| `published_schedule_id` | FK | 所属スケジュール |
| `name` | string | 工程名 |
| `color` | string | 色コード（`#RRGGBB`形式） |
| `sort_num` | integer | 並び順 |
| `status` | enum | `not_started`（未着工）/ `in_progress`（施工中）/ `completed`（施工完了） |
| `progress_type` | enum | `percentage`（割合）/ `actual_value`（実数値）/ `refer_to_small_process`（小工程参照） |

リレーション:
- `belongs_to :published_schedule`
- `has_many :published_small_processes`
- `has_many :published_process_users`

### PublishedSmallProcess（公開済み小工程）

| フィールド | 型 | 説明 |
|---|---|---|
| `published_large_process_id` | FK | 所属大工程 |
| `published_schedule_id` | FK | 所属スケジュール |
| `name` | string | **必須** |
| `start_date` | date | **必須** |
| `end_date` | date | **必須** |
| `row_position` | integer | **必須** 行の位置 |
| `status` | enum | `not_started` / `in_progress` / `completed` |
| `row_position_display` | virtual | 表示用行番号（SearchServiceが実行時にセット） |

---

## APIフロー

印刷画面はREST API（v2）を使用。

```
FE: fetch-published-schedule-mixin.ts
  → schedule-api-client.ts

  並列実行:
    GET /api/v2/.../published_schedule              → PublishedSchedule取得
    GET /api/v2/.../published_large_processes       → 大工程一覧
    GET /api/v2/.../published_schedule_plans        → スケジュールプラン
    GET /api/v2/.../published_small_processes       → 小工程一覧

  → Vuex Store（schedule モジュール）に格納
  → print/preview.vue で描画
```

### PublishedLargeProcessesController#index

```
GET /api/v2/companies/:company_id/projects/:project_id/
    published_schedules/published_large_processes

params:
  - published_schedule_id: ID（必須）
  - start_date: フィルタ開始日（任意）
  - end_date: フィルタ終了日（任意）
  - include_small_processes: boolean（デフォルト true）
  - ids: 大工程IDの配列（任意）
  - name: 名前検索（任意）
```

---

## ビジネスロジック（PublishedLargeProcess::SearchService）

### フィルタの処理順序

1. `apply_base_filters` — `published_schedule_id` で絞り込み → IDs指定 → 日付範囲
2. `apply_search_filters` — 名前検索
3. `order_by_sort_num_asc` — sort_num 昇順ソート
4. `preload_associations` — N+1対策のプリロード
5. `apply_post_preload_filters` — 小工程のフィルタリング・行番号セット

### ⚠️ 既知バグ：小工程のない大工程が消える（Bug #⑥）

`search_by_date` の実装:
```ruby
def search_by_date
  @resource = resource.eager_load(:published_small_processes)
  # ↓ LEFT JOIN後にWHEREをかけると、小工程がNULL（= 小工程なし）の大工程が全てフィルタされる
  @resource = resource.where('published_small_processes.end_date >= ?', params[:start_date])
  @resource = resource.where('published_small_processes.start_date <= ?', params[:end_date])
end
```

**根本原因**: `eager_load` は LEFT OUTER JOIN を生成するが、
後続の WHERE 句が `published_small_processes.*` カラムを参照するため、
小工程を持たない大工程（NULL行）が WHERE 条件でフィルタされ消える。

**修正方針**: NULL を許容する条件を追加する。
```ruby
@resource = resource.where(
  'published_small_processes.end_date >= ? OR published_small_processes.id IS NULL',
  params[:start_date]
)
```

---

## FEコンポーネント構成

```
pages/schedule/print/index.vue
  └─ components/schedule/templates/print/preview.vue
       ├─ components/print/molecules/schedule-print-setting-dialog.vue（印刷設定）
       └─ components/print/organisms/print-schedule-gantt-chart-list.vue（ガントチャート）
            └─ components/print/organisms/print-schedule-gantt-chart/
                 print-schedule-gantt-chart.vue
```

### schedule-print-setting-dialog.vue の設定項目

| 設定項目 | UI要素 | フィールド |
|---|---|---|
| 期間を選択 | DateRangePicker | `form.date_range` |
| 大工程を選択 | CheckboxGroup | `form.large_process_ids` |
| 小工程の表示 | RadioGroup（表示する/しない） | `form.is_small_process` |
| 会社ロゴ | RadioGroup（表示する/しない） | `form.is_company_logo` |
| 色設定 | RadioGroup（反映する/しない） | `form.is_coloring` |
| 注意事項 | Textarea（最大150文字） | `form.note` |

設定は `PublishedSchedule.print_settings`（JSON）に保存される。

---

## 未解決バグ・改善項目

| # | 種別 | 内容 | 重要度 | 難易度 |
|---|---|---|---|---|
| ① | バグ | 後から追加した工程が印刷設定でデフォルト非表示 | 高 | 低 |
| ② | 改善 | 印刷が1枚に収まらない → 表示粒度の自動選択 | 高 | 中 |
| ③ | 改善 | 印刷設定UIをモーダルからサイドバーに変更（リアルタイムプレビュー） | 高 | 低 |
| ④ | バグ | 工程名が見切れる（全箇所） | 中 | 低 |
| ⑤ | バグ | 色設定の「反映する」が機能していない | 高 | 低 |
| ⑥ | バグ | 小工程のない大工程が印刷されない | 高 | 低 |

詳細要件: 別途要件定義ドキュメントを参照。

---

## [Human] 背景・意図
<!-- 人間が追記するセクション。Claudeは上書きしない -->


## [Human] 注意事項・例外・経緯
<!-- 人間が追記するセクション。Claudeは上書きしない -->


## [Human] 未解決の疑問・TODO
<!-- 人間が追記するセクション。Claudeは上書きしない -->

