# ロードマップ

## 全体像

```
Phase 0  両リポジトリの静的知識構築 + UIキャプチャ基盤
  ↓
Phase 1  バグ調査・要件定義の自動化（実証済み）
  ↓
Phase 2  新規機能開発への応用
  ↓
Phase 3  careecon 自体を MCP サーバーとして公開
```

---

## Phase 0: ナレッジベースの構築

**目的**: Claude がコードを読んで knowledge/ を生成し、人間が追記できる共同作業スペースを作る

**ステータス**: 着手中（基盤完成・schedule ドメイン生成済み）

### 完成済みの成果物

| ファイル | 内容 |
|---|---|
| `knowledge/navigation/routes.md` | 全63画面のURLマップ |
| `knowledge/domains/schedule/print.md` | 工程表印刷（モデル・API・バグ含む） |
| `knowledge/patterns/service-layer.md` | サービス層パターン |
| `scripts/knowledge.py` | status確認・テンプレート生成・ファイル検索 |
| `scripts/capture.py` | Playwright スクショ + AOM キャプチャ |
| `CLAUDE.md` | Claudeへの自動指示（セッション開始時に自動読み込み） |

### 知識生成の2経路

```
【静的】コードスキャン
  scripts/knowledge.py find <domain>
    → 両リポジトリの関連ファイルを列挙
    → Claude がコードを読んで knowledge/ に書く

【動的】UIキャプチャ
  scripts/capture.py snap <url>
    → captures/aom/{page}.yaml（gitignore）
    → Claude が AOM を読んで knowledge/ の UI セクションに追記
```

### 残タスク（着手順）

1. `schedule/index`（工程表メイン画面）
2. `schedule/large-process` / `schedule/small-process`
3. `daily-report/`
4. `attendance/`
5. `board/` / `project/`

**完了の定義**: 主要5ドメインの knowledge ファイルが `status: draft` 以上で存在し、人間が1つ以上 `reviewed` にした状態

---

## Phase 1: バグ調査・要件定義の自動化

**目的**: 顧客バグ報告 → 要件定義ドキュメント生成までを半自動化する

**ステータス**: 一部実証済み

### 実証済みのこと

- 工程表印刷画面で DOM 調査 + Vuex ストア確認 + DOM操作プロトタイプ
- 「小工程の人工進捗を大工程にリンクする」要件定義を自動生成
- FR-01〜FR-06・非機能要件・実装箇所まで特定
- `[Human]` の確認待ち事項3つだけが人間の作業として残った

### やること

- 顧客バグ報告のテキストから対象機能を特定するルーティング
- knowledge/ を参照して BE の根本原因まで特定
- 要件定義フォーマット（FR / 非機能要件 / 実装箇所）への自動整形

**完了の定義**: 顧客バグ報告を渡すだけで、ストーリー誘導なしに要件定義が生成できる

---

## Phase 2: 新規機能開発への応用

**目的**: 「この機能を追加したい」という依頼から、既存パターンに沿った実装コードを生成する

### やること

- 既存コードパターンの知識化（Service・Vue コンポーネントの書き方）
- 機能追加の影響範囲を自動リストアップ
- BE（Migration → Model → Controller/Resolver）の雛形生成
- FE（API クライアント → Vuex → コンポーネント）の雛形生成
- cross-domain の連携設計（GraphRAG 検討）

**完了の定義**: 既存機能に類似した機能追加のドラフトを Claude が生成できる

---

## Phase 3: careecon を MCP サーバーとして公開

**目的**: careecon 自体を MCP サーバーとして外部 AI から利用可能にする

**前提**: Phase 0〜2 の knowledge が MCP のスキーマ・コンテキストとして機能する

### やること

- GraphQL スキーマから MCP ツール定義を自動生成
- 認証・認可の MCP 対応
- 外部 AI エージェントへの公開

**ステータス**: ロードマップ記載のみ・現時点での実装対象外

---

## 優先順位の根拠

```
Phase 0 を先に完成させる理由:
  → Phase 1〜3 全てが knowledge の質に依存するため

Phase 1 で価値を証明する理由:
  → バグ調査は発生頻度が高く ROI が測定しやすい
  → 「顧客報告 → 要件定義」の自動化は開発者と CS 両方にメリットがある
  → 既に実証済み（DOM 調査 + 要件定義生成）

Phase 2 を Phase 1 の後にする理由:
  → 新規機能開発は既存パターンの理解が必要 = Phase 0 の知識の質が高くないと機能しない
  → Phase 1 で knowledge の精度を実証してから着手する
```
