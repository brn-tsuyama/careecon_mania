# ナレッジベース設計

## 設計の核心

> **ClaudeがたたきAIを作り、人間が修正・追記する。**  
> その結果をClaudeがまた読む。このループが回り続けること。

ナレッジベースは「Claudeの出力置き場」ではなく、**人間とAIの共同作業スペース**として設計する。

---

## 要件

| 要件 | 理由 |
|---|---|
| 人間が読み書きしやすい | 人員が少ない中で修正コストを最小化するため |
| Claudeが構造的に読める | タスク実行時にコンテキストとして使うため |
| バージョン管理できる | 「誰がいつ何を修正したか」が追跡できること |
| コード変更に追従できる | 実装が変わったとき、ナレッジが自動的に古くなったことがわかること |
| 生成部分と人間の追記が混在できる | Claudeが再生成しても人間の記述が消えないこと |

**→ Markdownファイル × Git管理** が最も条件を満たす。

---

## ファイル構造

```
knowledge/
├── README.md                    ← 使い方・更新ルール
├── navigation/
│   └── routes.md                ← 全画面のURL・遷移マップ（63画面）
├── domains/                     ← 業務ドメインごとのナレッジ
│   ├── schedule/                ← 工程表（優先度1）
│   │   ├── print.md             ← 印刷機能（生成済み）
│   │   ├── index.md             ← メイン画面（未作成）
│   │   ├── large-process.md     ← 大工程（未作成）
│   │   └── small-process.md     ← 小工程（未作成）
│   ├── daily-report/            ← 日報（優先度2）
│   ├── attendance/              ← 勤怠（優先度3）
│   ├── board/                   ← 掲示板（優先度4）
│   └── project/                 ← 案件管理（優先度5）
└── patterns/                    ← コーディングパターン
    ├── service-layer.md         ← Serviceクラスの書き方（生成済み）
    ├── graphql-mutation.md      ← Mutationの書き方（未作成）
    └── vue-component.md         ← Vueコンポーネントの書き方（未作成）
```

---

## ファイルフォーマット

各ファイルは frontmatter + `[Claude生成]` セクション + `[Human]` セクションの構成。  
**`[Human]` セクションは Claude が絶対に上書きしない。**

```markdown
---
domain: schedule/print
type: code_analysis          # code_analysis | requirements | bug | pattern
generated_at: 2026-06-29
code_sources:
  - careecon_work/app/services/published_large_process/search_service.rb
  - careecon_work_frontend/src/components/print/molecules/schedule-print-setting-dialog.vue
status: draft                # draft | reviewed | approved
last_reviewed_by: ~
---

# ドメイン名

## 概要
<!-- Claude が生成 -->

## データモデル
<!-- Claude が生成 -->

## APIフロー
<!-- Claude が生成 -->

## ビジネスロジック
<!-- Claude が生成 -->

---

## [Human] 背景・意図
<!-- 人間が追記。Claudeは上書きしない -->

## [Human] 注意事項・例外・経緯
<!-- 人間が追記。Claudeは上書きしない -->

## [Human] 未解決の疑問・TODO
<!-- 人間が追記。Claudeは上書きしない -->
```

---

## 知識生成の2経路

### 経路1: 静的コードスキャン

コードを読んで構造・ロジックを抽出する。

```bash
uv run scripts/knowledge.py find <domain>
# → 両リポジトリの関連ファイルを列挙
# → Claude がコードを読んで knowledge/ に書く
```

カバーできる知識:

| 知りたいこと | ソース |
|---|---|
| 画面一覧・URL | `pages/` ディレクトリ |
| フォーム項目・ラベル | Vue コンポーネント |
| API エンドポイント | `*-api-client.ts` + Controller |
| ビジネスロジック・SQL | Service クラス |
| データ構造 | Model + Serializer |
| DB スキーマ | Migration + Schema |

### 経路2: Playwright UIキャプチャ

実際の画面を撮影して、動的な状態・実データを取得する。

```bash
uv run scripts/capture.py login          # 初回認証
uv run scripts/capture.py snap <url>     # 1画面キャプチャ
uv run scripts/capture.py batch          # 全画面一括
```

出力:
- `captures/screenshots/{slug}.png` — 視覚確認用（gitignore）
- `captures/aom/{slug}.yaml` — Playwright ariaSnapshot（gitignore）

Claude が `captures/aom/*.yaml` を読んで knowledge/ の UI セクションに変換する。  
**生データは gitignore。意味に変換したものだけ commit する。**

静的スキャンでは得られない知識:

| 知りたいこと | 理由 |
|---|---|
| 実際のデータ（大工程名等） | DB の中身はコードに出ない |
| 条件分岐後の UI 状態 | 実行しないとわからない |
| バグの実際の再現 | 動かさないと確認できない |

---

## 更新ルール

### Claude が更新するタイミング

- セッション中に新しいドメインを調査したとき → 新規ファイルを作成
- 既存ドメインに知見が増えたとき → 該当ファイルの `[Claude生成]` セクションを更新
- code_sources のファイルがコード変更されたとき → 再生成して `status: draft` に戻す

**`[Human]` セクションは絶対に上書きしない。**

### 人間が更新するタイミング

- `status: draft` のファイルをレビューするとき → `reviewed` / `approved` に変更
- Claude の内容が誤っているとき → `[Claude生成]` セクションを直接修正してOK
- 背景・経緯・例外を知っているとき → `[Human]` セクションに追記

### status の意味

| status | 意味 | Claude の扱い |
|---|---|---|
| `draft` | 生成済み・未レビュー | 参考程度に使用 |
| `reviewed` | 人間がレビュー済み | 信頼して使用 |
| `approved` | 人間が承認・追記済み | 優先参照 |

---

## セッション終了時のルール

**作業が終わったら必ず knowledge/ に書く。** これが蓄積の唯一のルール。

```
バグ調査した    → knowledge/domains/{domain}/bugs.md に知見を追記
新機能を設計した → knowledge/domains/{domain}/requirements.md に要件を追記
画面を調査した  → captures/aom/*.yaml を読んで UI セクションを追記
パターン発見    → knowledge/patterns/ に追記
```

CLAUDE.md の「セッション終了時のルール」セクションも参照。

---

## careecon work の資産：なぜ知識化しやすいか

### HTML 命名が業務用語そのまま

```yaml
# Playwright ariaSnapshot の出力例
- button "設定を保存"
- checkbox "大工程を選択 > すべて"
- radio "小工程の表示 > 表示する"
- textbox "注意事項"
```

AOM が直接ビジネス仕様になる。ARIA 属性が不十分な SaaS では `button "btn-1"` になるが careecon はならない。

### Service 層がビジネスロジックの唯一の場所

```
REST Controller  ──→┐
                     ├──→ Service ──→ Model ──→ DB
GraphQL Resolver ──→┘
```

REST/GraphQL どちらのパスを辿っても Service に行き着く。  
知識抽出の中心は Service クラスに絞れる。

### REST v1/v2 + GraphQL の二層構造

どちらの API 経由でも同じ Service を呼ぶので、抽出した知識が両方に適用できる。

---

## Phase 0 の着手順

| 優先度 | ドメイン | 理由 |
|---|---|---|
| 1 | schedule（工程表・印刷） | バグが集中・効果が見えやすい |
| 2 | daily-report（日報） | 利用頻度が高い |
| 3 | attendance（勤怠） | CS 問い合わせが多い |
| 4 | board（掲示板） | 機能がシンプルで知識化しやすい |
| 5 | project（案件管理） | 影響範囲が広いため後回し |
