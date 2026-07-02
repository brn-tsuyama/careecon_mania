# careecon_mania — Claude エージェント設定

## このリポジトリの目的

careecon work（施工管理SaaS）の AI 知識基盤。
Claude がコードを読み、作業し、知識を蓄積し続けるためのベースキャンプ。

対象リポジトリ:
- BE: `/home/ttsuyama/proj/careecon_work`
- FE: `/home/ttsuyama/proj/careecon_work_frontend`

---

## セッション開始時に必ず読む

1. `knowledge/README.md` — 構成と使い方
2. `knowledge/navigation/routes.md` — 全画面マップ
3. 作業対象のドメインファイル（例: `knowledge/domains/schedule/print.md`）

---

## ⚠️ knowledge 更新前に必ず実行する（例外なし）

**knowledge/ を新規作成・更新する前に、参照先リポジトリを最新状態にすること。**  
古いコードを読んで knowledge を生成しても無意味。

```bash
bash /home/ttsuyama/proj/careecon_mania/scripts/sync_repos.sh
```

または `/sync-repos` スキルを使う。

- リポジトリが存在しない → 自動で `git clone`
- リポジトリが存在する → `master` pull（存在すれば）→ `staging` checkout & pull
- 完了後に knowledge 作業を開始する

---

## スクリプト

| コマンド | 用途 |
|---|---|
| `uv run scripts/knowledge.py status` | カバレッジ確認 |
| `uv run scripts/knowledge.py new <domain> <aspect>` | 知識ファイルのテンプレート作成 |
| `uv run scripts/knowledge.py find <domain>` | 両リポジトリから関連ファイルを検索 |
| `uv run scripts/knowledge.py export-nblm` | `knowledge/` をフラット化して `knowledge_nblm/` へ出力（NotebookLM に一括アップロード用。gitignore 済み・再生成可能） |
| `uv run scripts/capture.py login` | ブラウザ認証（初回のみ） |
| `uv run scripts/capture.py snap <url>` | 1画面のスクショ + AOM を captures/ に保存 |
| `uv run scripts/capture.py batch` | routes.md の全画面を一括キャプチャ |

captures/ は gitignore 済み。**AOM・画像は必ず knowledge/ に変換してから commit する。captures/ のままでは知識として機能しない。**

---

## ⚠️ DOM調査 → knowledge 変換 SOP（必須・例外なし）

**Phase 1 実験・バグ調査・要件定義・DOM調査を行った場合、セッション終了前に必ずこの手順を完了すること。**

画像・AOM は一時ファイルであり、次のセッションでは消えている。調査結果を knowledge に変換しない限り、知識は蓄積されない。**変換なしにセッションを終えることは禁止。**

### 手順

```
Step 1: DOM情報を取得する
  capture.py snap <url>  → captures/aom/{page}.yaml に AOM 保存
  または
  ユーザーから画像を受け取る（Claude はマルチモーダルで読める）

Step 2: knowledge ファイルの UI セクションを上書きする
  **古い UI 情報はパージして最新で丸ごと置き換える。**
  バージョン管理は git 履歴に任せる。追記・マージはしない。
  AOM / 画像 + コード静的解析を組み合わせて以下を抽出：
    - 画面に存在するフィールド名・ラベル・必須/任意
    - 動的な表示切り替え（user_type・権限・状態による出し分け）
    - エラーメッセージ・バリデーション
    - ユーザーの操作フロー
  フロントマターの ui_sources.captured_at を現在日付に更新する。

Step 3: routes.md の ui_status を更新する
  対象画面の ui_status を `done` にする（重複調査防止）
  再キャプチャが必要な場合は `outdated` にする。

Step 4: captures/ の一時ファイルを確認・削除
  knowledge/ に変換済みであれば captures/aom/ の該当ファイルは不要
  （gitignore 済みのため commit には含まれないが、明示的に整理する）

Step 5: knowledge/ を commit する
```

### UI セクションのフォーマット（knowledge ファイルに追記）

```markdown
### UI（画面構造）

**取得元**
- URL: {画面のURL}
- 取得方法: AOM / スクリーンショット / コード解析
- 取得日: {YYYY-MM-DD}

**フィールド一覧**

| フィールド名 | ラベル | 必須 | 型 | 備考 |
|---|---|---|---|---|
| {field_name} | {表示ラベル} | ✓/- | text/select/... | {user_type制限など} |

**出し分けロジック**

| 条件 | 表示内容 |
|---|---|
| user_type = guest | {表示されるもの} |
| user_type = member/admin | {表示されるもの} |

**ユーザー操作フロー**

{番号付きで操作の流れを記述}
```

### フロントマターへの追加（UI 取得済みの場合）

```yaml
---
domain: {ドメイン名}
type: code_analysis | requirements | bug | pattern
generated_at: {YYYY-MM-DD}
code_sources:
  - {参照したファイルパス}
ui_sources:
  - url: {画面URL}
    captured_at: {YYYY-MM-DD}
    method: aom | screenshot | code_analysis
status: draft
---
```

---

## セッション終了時のルール（必須）

**作業が終わったら、必ず以下を実行すること。**

### 1. knowledge/ を更新する

調査・設計・QA など何をやったとしても、学んだことを knowledge/ に残す。

```
新しいドメインを調査した    → knowledge/domains/{domain}/{aspect}.md を作成
既存ドメインに知見が増えた  → 該当ファイルを更新
コーディングパターンを発見  → knowledge/patterns/ に追記
DOM調査・画面キャプチャを行った → UI セクションを更新（上記SOP参照）
```

### 2. ファイルのフォーマットを守る

```yaml
---
domain: {ドメイン名}
type: code_analysis | requirements | bug | pattern
generated_at: {YYYY-MM-DD}
code_sources:
  - {参照したファイルパス}
ui_sources:           # DOM調査を行った場合のみ追加
  - url: {画面URL}
    captured_at: {YYYY-MM-DD}
    method: aom | screenshot | code_analysis
status: draft
---
```

- `[Claude生成]` セクション — Claude が書く
- `[Human]` セクション — 人間が追記する。**Claude は絶対に上書きしない**

### 3. status のルール

| status | 意味 |
|---|---|
| `draft` | 生成済み・未レビュー |
| `reviewed` | 人間がレビュー済み |
| `approved` | 追記・承認済み |
| `superseded_by_code` | 実装済み。実装詳細はコードを見ること |

新規作成は必ず `draft` から始める。  
機能がリリースされたら実装メモセクションの status を `superseded_by_code` に更新する。

### 4. knowledge ファイルの2層ルール（新機能開発・設計作業後）

新機能の設計・要件定義を行ったとき、knowledge に残す内容を必ず2層に分けること。

```
## [ドメイン知識] ← リリース後も有効・コードに現れない
  - なぜその設計を選んだか（業界慣行・トレードオフ）
  - MVP から外したもの・その理由
  - 将来の拡張で考慮すべき制約

## [実装メモ] ← リリース後は superseded_by_code で封印
  - テーブル設計・計算式・API 仕様
  - migration 詳細
```

**禁止**: 設計ドキュメント（temp/ 以下）をそのまま knowledge/ にコピーしない。  
設計プロセスのノイズが混入し、リリース後に実コードと競合する。

### 5. リリース済みドメインの読み方

knowledge ファイルに `superseded_by_code` が付いた実装メモセクションがある場合:
- **実装の詳細はコードを読むこと**。知識ファイルの実装メモは信頼しない。
- `[ドメイン知識]` セクションは引き続き有効。「なぜ」の文脈として使う。

---

## knowledge/ の構成

```
knowledge/
├── navigation/routes.md        # 全画面マップ
├── domains/
│   ├── auth/                   # 認証・登録フロー
│   ├── schedule/               # 工程表（優先度1）
│   ├── daily-report/           # 日報（優先度2）
│   ├── attendance/             # 勤怠（優先度3）
│   ├── board/                  # 掲示板（優先度4）
│   └── project/                # 案件管理（優先度5）
└── patterns/                   # コーディングパターン
```

---

## コーディング規約（careecon_work に変更を加える場合）

- ビジネスロジックは必ず Service 層に書く（Controller/Resolver に書かない）
- REST v1/v2 と GraphQL は同じ Service を共有する
- LEFT JOIN 後に WHERE をかけるときは NULL を許容する条件を追加する
- 詳細: `knowledge/patterns/service-layer.md`

---

## ロードマップ

| Phase | 内容 | 状態 |
|---|---|---|
| Phase 0 | コードスキャンによる knowledge 構築 | 進行中 |
| Phase 1 | DOM調査・要件定義・バグ検証の自動化 | 一部実証済み |
| Phase 2 | 新機能開発への応用・cross-domain 連携 | 未着手 |
| Phase 3 | careecon work を MCP サーバーとして公開 | 未着手 |

詳細: `docs/roadmap.md`
