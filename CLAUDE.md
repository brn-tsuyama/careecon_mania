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

## スクリプト

| コマンド | 用途 |
|---|---|
| `uv run scripts/knowledge.py status` | カバレッジ確認 |
| `uv run scripts/knowledge.py new <domain> <aspect>` | 知識ファイルのテンプレート作成 |
| `uv run scripts/knowledge.py find <domain>` | 両リポジトリから関連ファイルを検索 |
| `uv run scripts/capture.py login` | ブラウザ認証（初回のみ） |
| `uv run scripts/capture.py snap <url>` | 1画面のスクショ + AOM を captures/ に保存 |
| `uv run scripts/capture.py batch` | routes.md の全画面を一括キャプチャ |

captures/ は gitignore 済み。AOM を読んで knowledge/ に変換したものだけ commit する。

---

## セッション終了時のルール（必須）

**作業が終わったら、必ず以下を実行すること。**

### 1. knowledge/ を更新する

調査・設計・QA など何をやったとしても、学んだことを knowledge/ に残す。

```
新しいドメインを調査した    → knowledge/domains/{domain}/{aspect}.md を作成
既存ドメインに知見が増えた  → 該当ファイルを更新
コーディングパターンを発見  → knowledge/patterns/ に追記
```

### 2. ファイルのフォーマットを守る

```yaml
---
domain: {ドメイン名}
type: code_analysis | requirements | bug | pattern
generated_at: {YYYY-MM-DD}
code_sources:
  - {参照したファイルパス}
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

新規作成は必ず `draft` から始める。

---

## knowledge/ の構成

```
knowledge/
├── navigation/routes.md        # 全画面マップ
├── domains/
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
