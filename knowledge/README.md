# Knowledge Base

careecon work の業務知識・システム挙動を Claude と人間が共同で管理するナレッジベース。

## 使い方

- `[Claude生成]` セクション — コードスキャン・UIキャプチャから自動生成
- `[Human]` セクション — 人間が追記する。**Claude は絶対に上書きしない**
- `status` — `draft`（未レビュー）→ `reviewed`（確認済み）→ `approved`（追記完了）

## ディレクトリ構成

```
knowledge/
├── navigation/
│   └── routes.md               # 全63画面のURLマップ ✅
├── domains/
│   ├── auth/                   # 認証・登録フロー
│   │   └── guest-registration.md  # ゲスト招待時の登録設計 ✅ [BE判断待ち]
│   ├── schedule/               # 工程表（優先度1）
│   │   └── print.md            # 印刷機能 ✅
│   ├── daily-report/           # 日報（優先度2）
│   ├── attendance/             # 勤怠（優先度3）
│   ├── board/                  # 掲示板（優先度4）
│   └── project/                # 案件管理（優先度5）
└── patterns/
    └── service-layer.md        # サービス層パターン ✅
```

## 知識を追加するには

### コードスキャン（静的）

```bash
uv run scripts/knowledge.py find <domain>   # 関連ファイルを探す
uv run scripts/knowledge.py new <domain> <aspect>  # テンプレート作成
# → Claude がコードを読んで書く
```

### UIキャプチャ（動的）

```bash
uv run scripts/capture.py snap <url>   # AOM を captures/ に保存
# → Claude が captures/aom/*.yaml を読んで knowledge/ に追記
# → captures/ は gitignore。knowledge/ だけ commit
```

## status の意味

| status | 意味 | Claude の扱い |
|---|---|---|
| `draft` | 生成済み・未レビュー | 参考程度 |
| `reviewed` | 人間がレビュー済み | 信頼して使用 |
| `approved` | 追記・承認済み | 優先参照 |
| `superseded_by_code` | 実装済み。実装詳細はコードを見ること | [ドメイン知識] セクションのみ参照。実装メモは無視 |

## カバレッジ確認

```bash
uv run scripts/knowledge.py status
```

## NotebookLM 用にまとめて出力する

`knowledge/` は `domains/schedule/print.md` のように階層化されているため、NotebookLM の
ソース追加（複数ファイル選択）に1つずつしか拾えず面倒。以下で `knowledge_nblm/`
（1階層のフラットな複製、gitignore 済み・再生成可能）に書き出せる。

```bash
uv run scripts/knowledge.py export-nblm
# → knowledge_nblm/domains__schedule__print.md のようにパスをファイル名に埋め込んでフラット化
# → knowledge_nblm/ を開いて全選択 → NotebookLM の「ソースを追加」にドラッグ&ドロップ
```
