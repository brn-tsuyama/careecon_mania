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

### sync で新規コミットが入った場合の追従調査（選定コストをかけない）

`sync_repos.sh` の末尾で `scripts/check_drift.py` が自動実行され、前回チェックポイントから
新規コミットが入っていた場合に対象ドメインを検出する。
「このドメインが影響を受けるか」を判定するコストをかけずに、**該当ドメインの BE/FE 調査は無条件でやり直す**。
BE/FE のコード調査だけなら1ドメインあたり高々数万〜十数万トークン程度で、判定コストをかける方が高くつく。

- チェックポイント: `.sync_checkpoint.json`（gitignore済み・ローカル状態）に各リポジトリの最終同期コミットSHAを
  記録し、そこからの `git diff --name-only` でファイルを洗い出す
- 差分ファイルが `knowledge/domains/*` の `code_sources` に含まれていれば該当ドメインを
  「BE/FE再調査対象」としてターミナル出力に表示する（`scripts/check_drift.py` が自動判定）
- 新規ディレクトリ・新規コントローラ/モデルなど既存どのdomainにも属さない差分は、新規ドメインとして
  `knowledge/domains/` に追加を検討する（出力の「新規ドメイン候補」欄を確認）

**DOM調査（実画面キャプチャ）だけは無条件にしない。** ログイン＋スクリーンショットは失敗しやすく
コストの分散も大きいため、以下のヒューリスティクスで「見た目が構造的に変わった疑いがある」ときだけ発動する
（FEの実装言語・フレームワークは将来変わりうる／`careecon_work_frontend`以外のFEリポジトリが対象に
加わる可能性もあるため、特定のテンプレート構文に依存しない書き方にする）：

- UIコンポーネントファイル（`.vue`/`.tsx`/`.jsx`や`pages/`配下）の diff に、ボタン・条件分岐表示・
  ルーティングに該当する構造的な変更（`<button`, `v-if=`, `v-show=`, `v-for=`, `router-link`,
  `<Link`, `useNavigate`, `<Route`等）が含まれる場合
- 上記に該当しなくても、そのファイルの diff 行数が一定量（目安: 20行, `check_drift.py`内
  `DIFF_LINE_THRESHOLD`）を超える場合

`check_drift.py` の出力で対象ドメインに「※DOM再検証も推奨」と付いた場合のみ実画面キャプチャを行う。
それ以外は BE/FE のコード調査結果だけを knowledge に反映し、`ui_status` は既存の値
（`done`/`pending`等）を変えずに残す（DOM調査未実施のまま古いUI情報が正だと誤解されないよう、
UIセクションを変更した場合のみ status を更新する）。

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

`capture.py login` は `.env`（gitignore済み）の `CAREECON_EMAIL` / `CAREECON_PASSWORD` を読めば非対話（headless）で実行できる。実行前に `set -a && source .env && set +a` で読み込むこと。

### ⚠️ careecon work は WAF が Playwright/Puppeteer の headless UA をブロックする

`sekou.work.careecon.jp` / `oauth.careecon.jp` は AWS ELB レベルの WAF が動いており、
User-Agent に `HeadlessChrome` という文字列が含まれるリクエストを **`403 Forbidden` で問答無用にブロックする**
（IPホワイトリストではない。`curl` で UA だけ変えて検証済み）。

Playwright の headless Chromium は既定でこの UA を使うため、`capture.py` に限らず
**この対象ドメインへの新しいブラウザ自動化スクリプトを書くときは必ず、通常のデスクトップ Chrome の
User-Agent を明示的にセットすること**（`capture.py` の `USER_AGENT` 定数を参照・流用する）。
これをやらずに 403 やタイムアウトで詰まったら、まず UA を疑うこと。

併せて `capture.py` にある以下の既知の落とし穴も踏まないよう注意：
- ログインフォームの email/password は `<label>` に紐づいていないため `get_by_label` は使えない。
  `input[name="user[email]"]` / `input[name="user[password]"]` を使う。
- ログイン後の SPA 画面はバックグラウンドポーリングがあり `wait_until="networkidle"` はタイムアウトしやすい。
  `domcontentloaded` + 固定 `wait_for_timeout` にフォールバックする。

---

## ⚠️ ドメイン調査は BE → FE → DOM の順で必ず一気通貫させる（例外なし）

**「コードを読んだだけ」でドメイン調査を終えてはいけない。DOM調査（実画面のキャプチャ）は任意ではなくマスト。**

理由: コード解析だけでは「実際に画面でどう出し分けられているか」「本当にその通り動いているか」が検証できない。
BE（モデル・Service・Policy）→ FE（Vue/GraphQLコンポーネント）→ DOM（実画面キャプチャ）の3段を
すべて走査し、**三者の対応関係（どのDBカラムがどのUI要素に対応するか、どのPolicyがどのUI出し分けに
対応するか）をセマンティックに記述して knowledge に残す**こと。DOM調査を省略した状態を `status: draft` の
まま放置しない（少なくとも1周は実画面を見てから `draft` を確定させる）。

**メイン機能だけでなく周辺機能も無駄なくいじって知識を貯めること。** 例えば掲示板なら投稿一覧だけでなく、
新規作成フォーム、詳細画面の既読/未読ダイアログ、コメント欄、添付ファイル一覧まで一通り操作し、
それぞれの画面が呼ぶAPI・参照するテーブル・権限分岐までセットで記録する。「聞かれた画面だけ」を
調べて終わりにしない。

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

## rdd_ideation/ — 壁打ち・設計作業のための作業ディレクトリ

新機能の設計・要件定義・デザイナー指示・もやもや整理など、**まだ knowledge に昇華されていない雑多なドキュメント**はすべてここに置く。

```
rdd_ideation/
├── 工事台帳_設計もやもや整理.md     # 設計議論の生ログ
├── 工事台帳_設計雨降って地固まる.md  # 決定事項の整理
├── デザイナーMTG_論点整理_*.md     # MTG メモ
└── ...
```

**ルール**
- gitignore 済み。commit しない（セッション間でローカルに残るが git 管理外）
- 設計の「プロセス」「生ログ」「もやもや」はここに溜める
- knowledge/ には昇華済みのものだけ入れる（2層ルール参照）

---

## セッション終了時のルール（必須）

**作業が終わったら、必ず以下を実行すること。**

### 0. rdd_ideation/ の後処理をユーザーに確認する

セッション中に rdd_ideation/ にファイルを作成・更新した場合、**終了前に必ずユーザーに以下を確認すること。**

```
「rdd_ideation/ に以下のファイルがあります：
  - {ファイル名}: {一行サマリー}
  ...

それぞれについて、どうしますか？
  [A] knowledge/ に抽象化して移動する（設計思想・トレードオフだけ抽出）
  [B] このまま rdd_ideation/ に置いておく（次セッションも壁打ちで使う）
  [C] 不要なので削除する」
```

ユーザーが [A] を選んだファイルについては、2層ルール（[ドメイン知識] のみ）に従って knowledge/ へ変換し、commit する。

### 1. knowledge/ を更新する

調査・設計・QA など何をやったとしても、学んだことを knowledge/ に残す。

```
新しいドメインを調査した    → knowledge/domains/{domain}/{aspect}.md を作成
既存ドメインに知見が増えた  → 該当ファイルを更新
コーディングパターンを発見  → knowledge/patterns/ に追記
DOM調査・画面キャプチャを行った → UI セクションを更新（上記SOP参照）
```

### 2. ファイルのフォーマットを守る

フロントマター schema・`[Claude生成]`/`[Human]` の使い分けは `knowledge/README.md` 参照。

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

**禁止**: 設計ドキュメント（rdd_ideation/ 以下）をそのまま knowledge/ にコピーしない。  
設計プロセスのノイズが混入し、リリース後に実コードと競合する。

### 5. リリース済みドメインの読み方

knowledge ファイルに `superseded_by_code` が付いた実装メモセクションがある場合:
- **実装の詳細はコードを読むこと**。知識ファイルの実装メモは信頼しない。
- `[ドメイン知識]` セクションは引き続き有効。「なぜ」の文脈として使う。

---

## knowledge/ の構成

→ `knowledge/README.md` 参照

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
