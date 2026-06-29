# Careecon Mania — ドキュメント

careecon work（施工管理SaaS）の開発・CS対応をAIで自動化するための知識抽出システム。

## まず読むべきドキュメント

| ドキュメント | 内容 |
|---|---|
| [vision.md](vision.md) | **最初に読む** — なぜ作るのか・どこへ向かうのか |
| [roadmap.md](roadmap.md) | Phase 0〜3 の実装ロードマップ |

## 設計ドキュメント

| ドキュメント | 内容 |
|---|---|
| [system_overview.md](system_overview.md) | 対象SaaSの技術スタック・統合知識ツリーの概念 |
| [use_cases.md](use_cases.md) | バグ調査・新規開発・MCP公開の具体的なユースケース |
| [knowledge_base_design.md](knowledge_base_design.md) | ナレッジベースの設計・フォーマット・更新ルール |

## 技術リファレンス（Phase 別実装参照）

`docs/reference/` に配置。実装フェーズが来たときに参照する。

| ドキュメント | 内容 | 使うPhase |
|---|---|---|
| [reference/phase1_frontend_extraction.md](reference/phase1_frontend_extraction.md) | 静的解析・AOMキャプチャ・GraphRAG設計 | Phase 0〜3 |
| [reference/phase2_dynamic_twin.md](reference/phase2_dynamic_twin.md) | RL探索・分散トレーシング・CDC | Phase 1〜3 |

### Phase 別の技術マッピング

| 技術 | 参照先 | 使うPhase |
|---|---|---|
| `pages/` ディレクトリ解析 → ルートマップ生成 | phase1 §1 | **Phase 0** |
| Playwright `ariaSnapshot()` → AOM知識化 | phase1 §2 | **Phase 0** |
| SimHash（LSH）→ 重複画面の排除 | phase2 §3 | **Phase 0** |
| Midscene.js / UI-Tars → 自動UX評価 | phase1 §3 | Phase 1 |
| PersonaTester → バグ検証の網羅性向上 | phase2 §1 | Phase 1〜2 |
| Tail-based Sampling → エラートレース収集 | phase2 §3 | Phase 1 |
| Nested JSON-LD + GraphRAG（Neo4j） | phase1 §4, phase2 §4 | Phase 2〜3 |
| eBPF / Debezium CDC | phase2 §2 | 現時点では不採用 |
| RL（ICM + PPO） | phase2 §1 | 現時点では不採用 |

---

## 実際のナレッジベース

コードとドキュメントは別管理。ナレッジの実体は `knowledge/` にある。

```
knowledge/
├── README.md                    ← 使い方・更新ルール
├── navigation/routes.md         ← 全画面URLマップ（63画面）
├── domains/schedule/print.md    ← 工程表印刷（生成済み）
└── patterns/service-layer.md    ← サービス層パターン（生成済み）
```

## スクリプト

```bash
# ナレッジ管理
uv run scripts/knowledge.py status              # カバレッジ確認
uv run scripts/knowledge.py new schedule index  # テンプレート作成
uv run scripts/knowledge.py find attendance     # 関連ファイル検索

# UIキャプチャ（Playwright）
uv run scripts/capture.py login                 # 初回ログイン・認証保存
uv run scripts/capture.py snap <url>            # 1画面キャプチャ
uv run scripts/capture.py batch                 # 全画面一括キャプチャ
```

`captures/` はgitignore済み。AOMを読んで `knowledge/` に変換したものだけcommitする。

---

## 知識蓄積のフロー

```
【コードスキャン（静的）】
  scripts/knowledge.py find → 両リポジトリの関連ファイルを特定
  Claude がコードを読んで knowledge/ を生成
          ↓
【UIキャプチャ（動的）】
  scripts/capture.py snap → captures/aom/{page}.yaml
  Claude が AOM を読んで knowledge/ の UI セクションを追記
          ↓
【人間がレビュー・追記】
  [Human] セクションに背景・意図・例外を書く
  status: draft → reviewed / approved
          ↓
【Claudeがナレッジを参照してタスクを実行】
  バグ調査・要件定義生成・新規機能設計
          ↓（実作業で知識が増えたら knowledge/ に追記 → ループ）
```
