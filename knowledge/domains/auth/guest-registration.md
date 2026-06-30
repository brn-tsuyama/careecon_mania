---
domain: auth/guest-registration
type: requirements
generated_at: 2026-06-29
code_sources:
  - careecon_work_frontend/src/pages/sessions/callback.vue
  - careecon_work_frontend/src/pages/sessions/invitation.vue
  - careecon_work_frontend/src/pages/initial-settings/user-profile.vue
  - careecon_work_frontend/src/pages/initial-settings/company-profile.vue
  - careecon_work_frontend/src/components/containers/company-profile-form.vue
  - careecon_work_frontend/src/components/containers/user-profile-form.vue
  - careecon_work/app/controllers/api/v1/sessions_controller.rb
  - careecon_work/app/services/company/create_service.rb
  - careecon_work/app/services/company/update_service.rb
  - careecon_work/app/services/company/invite_members_service.rb
  - careecon_work/app/services/invited_user/check_invitation_service.rb
  - careecon_work/app/models/invited_user.rb
  - careecon_work/app/models/companies_user.rb
status: draft
last_reviewed_by: ~
---

# ゲスト招待時の登録フロー設計

## 概要

ゲスト（外部業者）として招待されたユーザーが、**自分の所属会社名・住所**を登録するフローの設計。

招待元の会社（Company テーブル）とゲストの所属会社は別物であるため、専用ページ・専用保存先が必要。

---

## [Claude生成]

### 現状コードの把握

#### 現在の登録ルーティング（callback.vue）

```
CAS認証完了
  ↓
user_initialized = false  →  /initial-settings/user-profile
user_initialized = true   →  company.initialized = false  →  /initial-settings/company-profile
                           →  company.initialized = true   →  /companies/{id}/projects
```

**重要：現時点で user_type（guest/member/admin）による分岐は存在しない。**

#### user_type enum（companies_user.rb）

```ruby
enum user_type: { guest: 1, member: 2, admin: 3 }
```

#### CheckInvitationService（accept_invitation の実体）

- `CompaniesUser.create!(user_type: invited_user.user_type)` でゲストとして登録
- **guest の場合のみ**：同一メールに複数案件招待がある場合は全て一括処理
- company の新規作成は行わない（Sessions#create が担当）

#### Company::UpdateService が更新するフィールド

`name, cid, account_type, zip, prefecture_id, city, address, tel, fax, contact_name, initialized`

→ `/initial-settings/company-profile` から送信した値がそのまま **招待元 Company レコードを上書きする**。

---

### なぜ既存の company-profile をゲストに使わせてはいけないか

ゲストが招待される時点で `company.persisted? == true`（招待元会社は既存）のため、
Sessions#create は必ず `Company::UpdateService` を実行する。

```
ゲストが /initial-settings/company-profile に到達
  → Company::UpdateService が走る
  → ゲストの入力値（例:「○○建設」）で招待元の Company 名が上書きされる ← 事故
```

**したがってゲスト専用の別ページに隔離する必要がある。**

---

### 設計：新しい登録フロー

#### 全 user_type のフロー比較

```
CAS認証完了 → callback.vue
  ↓
[user_initialized = false]
  → /initial-settings/user-profile（全ユーザー共通・変更なし）
  ↓ 完了
  ├─ [guest] guest_company_initialized = false
  │    → /initial-settings/guest-company-profile（新規）
  │
  ├─ [member/admin] company.initialized = false
  │    → /initial-settings/company-profile（変更なし）
  │
  └─ いずれも完了 → /companies/{id}/projects
```

#### callback.vue の変更イメージ

```typescript
// 変更後
if (!company.user_initialized) {
  router.push('/initial-settings/user-profile')
} else if (!company.initialized) {
  // member/admin のみここに来る（guestは company.initialized = true のため来ない）
  router.push('/initial-settings/company-profile')
} else if (userType === 'guest' && !guestCompanyInitialized) {
  // 新規追加：ゲスト専用
  router.push('/initial-settings/guest-company-profile')
} else {
  router.push(ProjectListPage)
}
```

`guestCompanyInitialized` は Sessions#create のレスポンスへの追加が必要（後述）。

---

### 新規画面：`/initial-settings/guest-company-profile`

#### フィールド定義

| フィールド | 必須 | 備考 |
|---|---|---|
| 会社名 | ✓ | プレースホルダー「例：〇〇建設株式会社」 |
| 郵便番号 | - | 7桁入力で都道府県・市区町村を自動補完（zipcloud API） |
| 都道府県 | ✓ | 自動補完後も手動編集可 |
| 市区町村 | ✓ | 自動補完後も手動編集可 |
| 以降住所 | - | 番地・建物名 |

#### ワイヤーフレーム

```
┌──────────────────────────────────────────┐
│         所属会社を登録してください            │
│                                           │
│  作業を始めるために、あなたの会社情報を         │
│  教えてください。                            │
├──────────────────────────────────────────┤
│  会社名 *                                 │
│  [ 例：〇〇建設株式会社                    ]  │
│                                           │
│  住所 *                                   │
│  〒 郵便番号（ハイフンなし可）               │
│  [ 1000001   ] → 入力で自動補完             │
│  郵便番号が分からない場合は直接入力 ▼        │  ← トグル
│                                           │
│  都道府県          市区町村                 │
│  [ 東京都    ]  [ 千代田区          ]      │
│                                           │
│  以降住所                                 │
│  [ 丸の内1-1-1                         ]  │
│                                           │
│  [ 登録して始める ]                         │
└──────────────────────────────────────────┘
```

---

### 住所入力 UX 設計

**方針：「郵便番号を覚えている人には最速で、覚えていない人にも自然に」**

#### 2レーン構成

**レーン A（メイン）：郵便番号 → 自動補完**
- 7桁入力完了で zipcloud API を呼び出し
- 都道府県・市区町村を自動補完
- ユーザーは「以降住所」のみ手入力
- 全角・半角・ハイフン有無すべてフロントで正規化して受け付ける

**レーン B（代替）：住所を直打ち**
- 「郵便番号が分からない場合は直接入力」リンクをクリック
- 郵便番号フィールドが折りたたまれ、都道府県（ドロップダウン）＋市区町村＋以降住所を手入力

#### API 選定：zipcloud（無料）を推奨

| 項目 | zipcloud | Google Places |
|---|---|---|
| コスト | 無料 | 従量課金 |
| 実装難易度 | 低 | 中 |
| 精度 | 郵便番号→住所は高精度 | 住所補完は中程度 |
| B2B会社住所用途 | 十分 | やや大げさ |

郵便番号が複数住所に紐づくケースはモーダルで選択させる。

---

### user_type 別の現状 vs 変更後まとめ

| 項目 | guest | member | admin |
|---|---|---|---|
| CompaniesUser.user_type | 1 | 2 | 3 |
| user_initialized=false 時 | → user-profile（共通・変更なし） | 同左 | 同左 |
| company.initialized=false 時 | **来ない**（常に true） | → company-profile | → company-profile |
| 新規分岐 | **→ guest-company-profile** | なし | なし |
| 所属会社の保存先 | **CompaniesUser or 専用テーブル（未決定）** | Company テーブル | Company テーブル |
| accept_invitation の変更 | 基本不要（デフォルト値で対応） | 不要 | 不要 |

---

### リスク評価

| リスク | 内容 | 対策 |
|---|---|---|
| 招待元 Company の上書き | ゲスト入力で発注会社の社名・住所が書き変わる | 保存先を Company テーブル外にすることで完全回避 |
| member/admin フロー変更 | 既存ユーザーへの影響 | callback.vue の分岐を user_type で限定。既存フローは無変更 |
| 既存ゲストへの対応 | すでに登録済みのゲストの扱い | `guest_company_initialized: false` がデフォルト → 次ログイン時に登録を促す or スキップ可能にする（要検討） |
| company-profile への誤ルーティング | ゲストが company-profile に届いてしまう | ゲストは `company.initialized = true` のため、コード上このルートには**絶対に来ない** |
| zipcloud レート制限 | アクセス過多での制限 | 本番前に制限確認、キャッシュで対応 |

---

### FE 実装の確定・未確定まとめ

| 項目 | 状態 | 根拠 |
|---|---|---|
| callback.vue の `user_type` 分岐 | ✅ 追加実装不要 | `SessionsSerializer` がすでに `user_type` を返す。store の `company.user_type` から参照可能 |
| `guestCompanyInitialized` フラグの取得 | ⚠️ BE 保存先決定待ち | 選択肢 A なら `companies_users.guest_company_initialized`、選択肢 B なら `guest_company_profiles` レコードの有無 |
| 新規ページ実装 | ✅ 確定 | BE 依存なし |
| 郵便番号自動補完 | ✅ `searchAddressWithZip()` を再利用 | `company-profile-form.vue` に実装済み |
| 「直打ち」トグル UI | ✅ 確定 | 純粋な FE 実装 |
| 既存フロー（member/admin）への影響 | ✅ なし | routing 分岐を user_type で限定 |

**FE の着手ブロッカーは BE の保存先選択（A か B か）の 1 点のみ。**

#### 関連ファイル（FE）

| ファイル | 役割 |
|---|---|
| `src/pages/sessions/callback.vue:163` | ルーティング分岐（変更箇所） |
| `src/store/initial-setting.ts:50` | `company.user_type` の保持（変更不要） |
| `src/serializers/api/v1/sessions_serializer.rb:4` | `user_type` をレスポンスに含める（変更不要） |
| `src/components/containers/company-profile-form.vue` | `searchAddressWithZip()` の参照元 |

---

## [Human]

<!-- 決定事項・レビューコメントをここに追記してください -->

