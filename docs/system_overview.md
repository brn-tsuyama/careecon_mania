# システム概要

## 対象SaaS

**careecon work** — 施工管理SaaS  
サイト: https://sekou.work.careecon.jp/companies

| | リポジトリ | 技術スタック |
|---|---|---|
| Backend | `careecon_work` | Ruby on Rails + GraphQL（graphql-ruby） |
| Frontend | `careecon_work_frontend` | Vue.js + Atomic Design（atoms/molecules/organisms/templates） |

---

## 根源的な問い

> ClaudeがDOMを毎回走査するのは高コスト・低精度。  
> 事前に構造化されたナレッジがあれば、Claudeは「地図を持った状態」で動ける。  
> その地図をどう作り・維持するか。

---

## 実証済みのこと

MCP経由でClaudeにDOMを走査させ、以下を実際に行えた：

- 新機能のリリース用プレゼン資料作成
- デモ用データ登録
- UAT的な検証作業
- 顧客起票のバグを再現確認し、要件定義として整理（→ [実例](use_cases.md#バグ調査の実例)）

**課題：** 毎回「施工管理 > 工程表 > 印刷に行って」のように細かくストーリーを渡さないと動けなかった。地図があればハンズオフでできる。

---

## なぜFE知識だけでは足りないか

UIだけ見ると「表示バグ」に見えるものが、BEのコードを見ると「SQLレベルの問題」とわかる実例がある。

```
【UIのみの判断】                    【FE + BE の判断】
「小工程のない大工程が               PublishedLargeProcess::SearchService の
 印刷されない」                      search_by_date が LEFT JOIN + WHERE で
  → 原因不明                         NULL（小工程なし）の大工程を落としている
  → 再現確認が都度必要                → 根本原因まで即特定
```

BEがGraphQLであることは知識抽出に非常に都合が良い。  
GraphQL スキーマは自己文書化されており、Resolver → Service → Model の繋がりがコードから静的に全量抽出できる。

---

## 両リポジトリの統合知識ツリー

FEとBEを別々に理解するのではなく、**一つの繋がったツリー**として持つ。

```
FE: pages/schedule/print.vue
  └─ GraphQL query: publishedLargeProcesses
       └─ BE Resolver: PublishedLargeProcessCollectionResolver
            └─ Service: PublishedLargeProcess::SearchService
                 └─ Model: PublishedLargeProcess
                      └─ DB: published_large_processes table
```

このツリーがあれば：

- **バグ調査** → 「この画面がおかしい」→ ツリーを下に辿って根本原因まで特定
- **新規機能開発** → 「工程表にX機能を追加したい」→ 既存パターンを参照して全スタック生成
- **要件定義** → 影響範囲（FE/BE/DB）を正確に把握してドキュメント化
