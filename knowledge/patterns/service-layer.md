---
generated_at: 2026-06-29
code_sources:
  - careecon_work/app/services/application_service.rb
  - careecon_work/app/services/base_service.rb
  - careecon_work/app/services/published_large_process/search_service.rb
status: draft
---

# サービス層パターン

careecon work のビジネスロジックはすべてサービス層に集約されている。
REST v1/v2 と GraphQL の両方がこのサービス層を共有する。

## 継承階層

```
ApplicationService          params の DI
  └─ BaseService            resource + ページネーション + ソート
       └─ (各ドメイン)/SearchService
       └─ (各ドメイン)/CreateService
       └─ (各ドメイン)/UpdateService
       └─ (各ドメイン)/DeleteService
```

## 命名規則

```
app/services/{domain}/{action}_service.rb
```

| アクション | クラス名 | 主な責務 |
|---|---|---|
| `search_service` | 一覧・検索 | フィルタ・ソート・ページネーション |
| `create_service` | 作成 | バリデーション・保存・通知 |
| `update_service` | 更新 | バリデーション・保存・通知 |
| `delete_service` | 削除 | 論理削除 or 物理削除 |
| `show_service` | 詳細取得 | 単一リソース取得 |

## 呼び出しパターン

```ruby
# Controller / Resolver の共通パターン
search_params = params.merge(current_user: current_user)
result = Domain::SearchService.new(search_params, resource).do!
```

- 第1引数 `params`: ActionController::Parameters（または Hash）
- 第2引数 `resource`: ActiveRecord::Relation or Class（ベースクエリ）
- `.do!`: メイン実行メソッド

## SearchService のフィルタ構造

`search_by_date` で日付フィルタをかける場合の注意点:

```ruby
# NG: LEFT JOIN後にWHEREをかけると、関連なしのレコードが消える
eager_load(:related).where('related.date >= ?', date)

# OK: NULLを許容する
eager_load(:related).where('related.date >= ? OR related.id IS NULL', date)
```

## ページネーション

`BaseService` が自動処理。

| param | デフォルト | 最大 |
|---|---|---|
| `limit` | Settings.paginate.default.limit | 500 |
| `offset` | 0 | - |

カスタムデフォルトは `Settings.paginate.{model_name_plural}.limit` で設定。

## REST と GraphQL の共存

```
REST    Api::V2::DomainController#index → Domain::SearchService.do!
GraphQL Resolvers::DomainResolver         → Domain::SearchService.do!
```

**同じ SearchService を呼ぶ**。ロジックの分岐はサービス層の外に出ない。

---

## [Human] 例外・特殊なパターン
<!-- 人間が追記するセクション。Claudeは上書きしない -->


## [Human] 注意事項
<!-- 人間が追記するセクション。Claudeは上書きしない -->
