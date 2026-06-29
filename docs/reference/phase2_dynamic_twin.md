# Phase 2: フルスタック動的デジタルツインとGraphRAGによるシステム挙動の自律的抽出

## このドキュメントの使い方

実装時の技術リファレンス。各節がロードマップのどのPhaseで使えるかを示す。

| 節 | 技術 | 使うPhase |
|---|---|---|
| §1 RL + PersonaTester | PersonaTesterのペルソナ設計 | Phase 1〜2 |
| §1 RL + PersonaTester | ICM + PPO（強化学習） | **現時点では不採用** |
| §2 eBPF + CDC | eBPF / Debezium | **現時点では不採用** |
| §3 データ蒸留 | SimHash（LSH）→ 重複画面の排除 | **Phase 0** |
| §3 データ蒸留 | Tail-based Sampling → エラートレース収集 | Phase 1 |
| §3 データ蒸留 | LLM による複数トレースの抽象化 | Phase 1〜2 |
| §4 GraphRAG | Nested JSON-LD + @id + Neo4j GRAPH TYPE | Phase 2〜3 |

> **不採用の技術について**: eBPFはインフラ要件が高くマネージドサービスで使えない。  
> RLはPersonaTester単体で十分なカバレッジが得られるかを先に検証する。  
> 「不採用」は「永久に使わない」ではなく「今は使わない」。

---

## 概要

Phase 1で完成した静的解析と基本GraphRAGを起点に、実稼働環境で頻発する障害やエッジケースを **「動的かつ有機的なシステムの振る舞い」** として抽出・構造化する。  
自律的AIエージェントがFEを探索し、カオスエンジニアリングで引き起こした異常がBE・DBへどのように伝播するかを分散トレーシングで統合し、フルスタックの動的デジタルツインをGraphRAGに蓄積する。

```
FE自律探索（RL + ペルソナ）
  → FE-BEフルスタックトレーシング（W3C Trace Context + eBPF）
  → DB差分抽出（Debezium CDC）
  → データ蒸留（SimHash + Tail-based Sampling + LLM）
  → GraphRAG更新（フルスタック・トポロジー）
```

---

## 1. 自律的フロントエンド探索とカオス・エンジニアリング

### 課題

ランダムなモンキーテストでは意味のあるアクション組み合わせを引く確率が極めて低く、認証の壁や複雑なフォームを突破できない。

### 推奨アプローチ：RL + ペルソナのハイブリッド探索

#### コアエンジン：ICM + PPO / GRPO（強化学習）

**Intrinsic Curiosity Module（ICM）** を基盤に、未知のDOM状態への到達を内発的報酬として学習させる。

- エージェントが「次の状態をどれだけ正確に予測できるか」の予測誤差を報酬として与える
- スパースな報酬環境でも未踏の画面遷移に強い好奇心を持ち、システムの深部へ到達
- 複数エージェント協調の場合は **CERMIC**（Context-Aware Exploration via Robust Multi-agent Intrinsic Curiosity）フレームワークを適用
- ε-グリーディ法よりも高度な **PPO / GRPO + RLVR（Verifiable Rewards）** の組み合わせを推奨

#### ペルソナ層：PersonaTester（3次元ペルソナ）

3つの直交する軸でLLMにペルソナを注入し、多様なバグを引き出す：

| 次元 | 例 |
|---|---|
| テストの思考プロセス | 「悪意あるハッカー」→ フォーム境界値テスト・戻るボタン多用でシステムを破壊 |
| 探索戦略 | 「新規ユーザー」→ ヘルプを多用・エラーメッセージを読まずに再送信 |
| インタラクションの癖 | 「リテラシーの低いユーザー」→ 送信ボタン連打・ローディング中に別クリック |

研究結果：ペルソナ間の行動ばらつきをベースライン比117〜126%向上させ、クラッシュ100件以上を安定して引き起こすことが実証済み。

#### ネットワークカオス層：Playwright Network Intercept

`page.route()` を使い、FE-BE間通信に意図的なカオスを注入する：

```typescript
// Race Condition を誘発（レスポンスの順序逆転シミュレーション）
await page.route('**/api/**', async (route) => {
  const response = await route.fetch();
  await new Promise((f) => setTimeout(f, 500)); // 500ms遅延でレスポンス順序をずらす
  await route.fulfill({ response });
});

// タイムアウト処理の検証（ハングアップシミュレーション）
await page.route('**/api/critical/**', async (route) => {
  await page.waitForTimeout(60_000); // 永遠に解決しない
});
```

**補足** — Playwright の自動リトライアサーション（`expect(heading).toHaveText()`）は最大5秒ポーリング待機する。この待機時間を逆手に取り、待機中に別操作を発火させて **Unmounted component state update** 等の脆弱性を突くことができる。

### 比較検討

| 手法 | メリット | デメリット | 採否 |
|---|---|---|---|
| ランダムモンキーテスト | 実装容易・コストゼロ | カバレッジ極低・認証突破不可 | 不採用 |
| PersonaTester（LLMペルソナ） | 論理バグ・UX欠陥の発見に優れる | API呼び出しコスト・推論レイテンシ依存 | 採用（戦略的探索層） |
| ICM / PPO（強化学習） | 未知状態空間への到達効率が圧倒的 | 報酬関数設計・学習パイプライン構築が複雑 | 採用（コアエンジン） |
| Playwright ネットワークインターセプト | ブラウザレベルで通信を完全制御可能 | アプリ内インメモリ競合は直接制御不可 | 採用（ネットワークカオス） |

---

## 2. フルスタック分散トレーシングとDB状態の差分抽出

### FE-BE統合トレース：W3C Trace Context + eBPF

#### Context Propagation（文脈伝播）

Playwright から発信するリクエストに **W3C traceparent ヘッダー** を注入し、FE操作をトレースの起点にする：

```typescript
import { context, propagation } from '@opentelemetry/api';

const headers: Record<string, string> = {};
propagation.inject(context.active(), headers);
// headers に traceparent: 00-cccd19c3a2d10e589f01bfe2dc896dc2-...-01 が格納される
```

または Tracetest のようなツールで自動注入も可能。

#### eBPF によるゼロコードバックエンドトレーシング（OBI）

**OpenTelemetry eBPF Instrumentation（OBI）** をLinuxカーネルレベルで稼働させ、アプリコードの改修なしに以下を自動キャプチャする：

- HTTPリクエスト・gRPC通信のスパン
- PostgreSQL / MySQL 等のDBドライバー通信（クエリ・レイテンシ・ペイロード）
- アプリケーションログへの `trace_id` / `span_id` の透過的注入（write syscallをフック）

```
FE Agent (Playwright)
  ↓ [traceparent ヘッダー注入]
Backend OS Kernel (eBPF / OBI)
  ├─ ネットワーク入線を傍受 → HTTP Span を生成
  ├─ write syscall を傍受 → アプリログの JSON に trace_id を注入
  └─ DB Driver 通信を傍受 → DB Span を生成（db.system, db.query.text）
  ↓
Database (PostgreSQL) — Execute SQL Query
```

同一 Trace ID 配下に「FEのボタンクリック → APIコール → SQL発行」が親子Spanとして連なり、フルスタックの因果関係が可視化される。

### DB差分抽出：Debezium CDC

**Debezium** の PostgreSQL WAL（Write-Ahead Log）から論理デコーディング（pgoutput）でリアルタイムに変更イベントをストリーミングする。  
Dual-writes（二重書き込み）の不整合リスクを根本から排除し、変更前後の厳密な差分を保証する。

#### LLMによるビジネスロジックの逆コンパイル

CDCの生ペイロードは抽象度が低すぎてGraphRAGには直接使えない。LLMに以下を渡して意味的に変換する：

**入力（CDCペイロード + トレース情報）：**
```json
{
  "table": "orders",
  "before": { "status_id": 1 },
  "after": { "status_id": 3, "updated_at": "2026-06-29T12:00:00Z" }
}
// 紐づくトレース: POST /api/orders/fulfill
```

**プロンプト：**
```
提供されたDBの行レベルの更新と、バックエンドAPIのエンドポイント構造から、
ユーザーがフロントエンドで行った「ビジネス上の意味」を推論し、
自然言語で抽象化されたルールとして出力せよ。
```

**LLM出力（GraphRAGに格納）：**
> ユーザーが出荷処理（Fulfill）を実行すると、オーダーのステータスが PENDING(1) から SHIPPED(3) に遷移し、更新タイムスタンプが記録される。

### 比較検討

| 手法 | メリット | デメリット | 採否 |
|---|---|---|---|
| 手動SDKインスツルメンテーション | カスタム属性を柔軟に追加可能 | 大規模なコード改修が必要・言語ごとに実装差異あり | 部分採用（ビジネス固有属性の追加時のみ） |
| eBPF（OBI） | ゼロコード・言語非依存・ネットワーク+ログを自動紐付け | メモリ内の特定関数コール追跡には限界 | 採用（主力トレーシング基盤） |
| DBスナップショット比較 | 実装容易・全体差分をSQLで確認 | 並行テスト環境では原因と結果の特定が不可能 | 不採用 |
| Debezium CDC | WAL直接取得で抜け漏れなし・変更前後を厳密に保証 | Kafka等のブローカー構築・運用コストが発生 | 採用（副作用抽出基盤） |

---

## 3. 膨大な動的データの蒸留とノイズ排除

### FEノイズ排除：AOM + SimHash（LSH）

探索中に大量発生する「時刻の秒数更新だけ」「同一エラーの無限ループ」「テンプレートで生成された類似ページ」等の無意味な状態遷移をフィルタリングする。

#### 重複排除アルゴリズム

1. 新しい画面状態に到達したら DOM → AOMツリーへ変換・正規化（装飾用ノードを除去）
2. 各ノードの `role`・`name`・`state` 属性を文字列化し、階層構造（深さ）を加味した **64-bit SimHash フィンガープリント** を計算
3. Redis / Kvrocks で過去のハッシュ群と **ハミング距離** を照合
4. ハミング距離が閾値（例：$k \le 3$）以下 → 「既知のUI状態」と判定
5. 既知と判定された場合：新規ノード追加をスキップし、既存ノードへの再訪問レコードのみ更新

**SimHash の特性** — 「類似したドキュメントはハッシュ値のビット配列のハミング距離が小さい」。64-bit フィンガープリントで数十億ページのクロールも実証済み。

### BEノイズ排除：Tail-based Sampling

OpenTelemetry Collector の **Tail-based Sampling プロセッサ** でヘルスチェック等の無関係トレースを排除する。

Head-based Sampling（確率的間引き）とは異なり、全スパンが到着してトレースが完了してから保持/破棄を判定するため、**カオステストで引き起こしたエラーや異常レイテンシを100%捕捉**できる。

```yaml
processors:
  tail_sampling:
    decision_wait: 10s  # 全スパン収集を待つ時間
    policies:
      # エラーを含むトレースは100%保持
      - name: error-policy
        type: status_code
        status_code: { status_codes: [ERROR] }
      # ヘルスチェックはドロップ
      - name: health-check-filter
        type: string_attribute
        string_attribute:
          key: http.route
          values: [/health, /metrics]
          invert_match: true
      # 1000ms超のレイテンシは保持
      - name: latency-policy
        type: latency
        latency: { threshold_ms: 1000 }
```

### LLMによる複数トレースの抽象化・蒸留

フィルタリング後も依然として巨大なJSONのトレース群を、LLMで「抽象化された仕様」へ圧縮する。

**プロンプト例：**
```
以下の3件のトレースログとFEのAOM状態遷移から、共通する根本原因を帰納的に推論せよ。
ユーザーIDやセッショントークン等の具体値を排除し、以下の形式の再利用可能な抽象化ルールとして出力せよ：
「特定条件下の入力（A）と通信遅延（B）が重なった際、APIエンドポイント（C）において
DBのカラム（D）がNull許容されていないために例外（E）が発生する」
```

数百KBの生ログが数行の構造化推論ルールに圧縮され、GraphRAGの検索効率と回答精度が飛躍的に向上する。

### 比較検討

| 手法 | メリット | デメリット | 採否 |
|---|---|---|---|
| DOMツリー全体での単純重複排除 | 実装が単純 | CSSクラスの差異だけで別状態と判定・重複が爆発 | 不採用 |
| AOM + SimHash（LSH） | 意味的な要素のみで状態判定・ハミング距離で高速照合 | AOMパース・ハッシュ計算のコンピュートリソースが必要 | 採用 |
| Head-based Sampling | ネットワーク通信量とメモリを大幅削減 | エラー・異常レイテンシを含む重要トレースを確率的に破棄 | 不採用 |
| Tail-based Sampling | エラー・異常レイテンシを100%捕捉 | Collectorに全スパンを保持する大容量メモリが必要 | 採用（OOM対策を施した上で） |

---

## 4. 究極のGraphRAGモデリング（フルスタック・トポロジー）

### Nested JSON-LD + @id アンカリング

フラットなJSON（Flat Schema）はエンティティ間の関係性が曖昧になり、LLMがベクトル類似度だけで無関係な要素を結びつけるハルシネーションの温床となる。  
**言語的包含関係（Linguistic Containment）** と **@id アンカリング** で依存関係を明示的に定義する：

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@id": "ui:cart-payment-button",
      "@type": "WebPageElement",
      "name": "決済ボタン",
      "sameAs": "https://issues.internal/CART-123",
      "BLOCKED_BY": {
        "@id": "api:checkout",
        "@type": "EntryPoint",
        "httpMethod": "POST",
        "urlTemplate": "/api/v1/checkout",
        "CAUSED_BY": {
          "@id": "db:orders.payment_token",
          "@type": "PropertyValue",
          "name": "payment_token",
          "description": "Null制約違反により決済処理がハングアップする"
        }
      }
    }
  ]
}
```

`sameAs` プロパティで外部システム（Issue Tracker等）へグラウンディングし、エンティティのアイデンティティ衝突を防ぐ。

### エッジの分類：正常系 vs 異常系

Neo4j にてエッジ（Relationship）のセマンティクスを厳格に区別する：

| 種別 | リレーション例 | 説明 |
|---|---|---|
| **正常系** | `TRANSITIONS_TO`・`CALLS`・`READS`・`WRITES` | システムが本来意図した振る舞い・静的設計仕様 |
| **異常系** | `CAUSED_BY`・`BLOCKED_BY`・`RACE_CONDITION_WITH` | 動的探索・カオステストによってのみ発見された副作用的な振る舞い |

**Neo4j GRAPH TYPE**（2026.02 プレビュー）でスキーマ全体を宣言的に強制する：
```
DBカラムノードは必ず APIノードから READS / WRITES / CAUSED_BY のいずれかで関係づけられなければならない
```

従来の個別 `CREATE CONSTRAINT` 方式と異なり、データモデル全体を一つの宣言的構造として統合できる。

### AI不具合調査の推論フロー

CSから「カート画面で決済ボタンを押すと無限ロードになる」というクエリが来た際：

```
1. ベクトル検索 → ui:cart-payment-button ノードを特定

2. 異常系エッジ（BLOCKED_BY / CAUSED_BY）を優先探索
   ui:cart-payment-button --[BLOCKED_BY]--> api:checkout

3. api:checkout ノード + 蒸留済み Tail-sampled エラーログを参照
   api:checkout --[CAUSED_BY]--> db:orders.payment_token

4. db:orders.payment_token ノードに到達
   Debeziumから抽出したCDC差分の逆コンパイル結果を確認

出力（ハルシネーションなし）：
「この無限ロードは、決済APIにおける非同期リクエストの順序逆転（Race Condition）に起因し、
 最終的に orders.payment_token カラムのNull制約違反により処理がハングしています。」
```

### 比較検討

| アーキテクチャ | メリット | デメリット | 採否 |
|---|---|---|---|
| Flat JSON-LD Schema | 出力実装が単純 | エッジが曖昧・LLMがハルシネーションを起こす温床 | 不採用 |
| Nested JSON-LD + @id アンカリング | 依存関係が決定論的に定まり・LLMが迷わずグラフをトラバース | スキーマ設計・@id 管理の難易度が高い | 採用 |
| Neo4j 個別 Constraints（旧方式） | ピンポイントでルール追加可能 | スキーマ肥大化で全体像が把握不可能になる | 不採用 |
| Neo4j GRAPH TYPE | グラフ全体のデータモデルを包括的かつ宣言的に強制 | プレビュー機能（2026年時点）・例外ハンドリング設計が新たに必要 | 採用 |

---

## 総合結論

| レイヤー | 採用技術スタック |
|---|---|
| FE探索エンジン | ICM + PPO / GRPO（強化学習）+ PersonaTester 3次元ペルソナ |
| ネットワークカオス | Playwright `page.route()` による確率的遅延・ハングアップ注入 |
| FE-BEトレーシング | W3C Trace Context + eBPF（OBI）ゼロコード計装 |
| DB差分抽出 | Debezium pgoutput → Trace ID 紐付け → LLM逆コンパイル |
| FEノイズ排除 | AOM正規化 + SimHash（ハミング距離 $k \le 3$） |
| BEノイズ排除 | OTel Collector Tail-based Sampling |
| GraphRAGモデリング | Nested JSON-LD + @id + Neo4j GRAPH TYPE |

強化学習エージェントがシステムの耐久境界を暴き、eBPFとCDCが因果の糸を紡ぎ出し、LLMが蒸留した知識基盤から **いかなる複雑な障害も即座に根本原因を特定する知能** が生まれる。
