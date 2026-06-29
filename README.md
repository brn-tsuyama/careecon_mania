# careecon_mania

careecon work（施工管理SaaS）の開発・CS対応を AI で自動化するための知識基盤リポジトリ。

Claude がコードを読み、実際の画面を見て、業務知識を `knowledge/` に蓄積していく。
蓄積した知識を使って、バグ調査・要件定義・新機能開発をハンズオフで進めることが目標。

## 対象

| リポジトリ | 役割 |
|---|---|
| `careecon_work` | Rails + GraphQL バックエンド |
| `careecon_work_frontend` | Vue.js フロントエンド |

## 使い方

### ナレッジの確認

```bash
# 現在のカバレッジを確認
uv run scripts/knowledge.py status

# 新しいドメインのテンプレートを作成
uv run scripts/knowledge.py new <domain> <aspect>

# 両リポジトリから関連ファイルを検索
uv run scripts/knowledge.py find <domain>
```

### UIキャプチャ（Playwright）

```bash
# 初回のみ: ブラウザでログイン → 認証情報を保存
uv run scripts/capture.py login

# 特定画面のスクショ + AOM を撮る
uv run scripts/capture.py snap <url>

# routes.md の全画面を一括キャプチャ
uv run scripts/capture.py batch
```

キャプチャした生データ（`captures/`）は gitignore 済み。  
Claude が AOM を読んで `knowledge/` に変換したものだけ commit する。

### Claude Code での作業

このリポジトリを Claude Code で開くと `CLAUDE.md` が自動で読み込まれ、  
既存の knowledge を把握した状態でセッションが始まる。

## ロードマップ

| Phase | 内容 | 状態 |
|---|---|---|
| Phase 0 | コードスキャン + UIキャプチャで knowledge 構築 | 進行中 |
| Phase 1 | バグ調査・要件定義の自動化 | 一部実証済み |
| Phase 2 | 新規機能開発への応用 | 未着手 |
| Phase 3 | careecon work を MCP サーバーとして公開 | 未着手 |

詳細 → [docs/roadmap.md](docs/roadmap.md)
