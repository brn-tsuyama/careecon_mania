# 設計: cost_price マイグレーション
作成: 2026-06-30

---

## 背景・目的

工程テーブルに `unit_price`（売上・契約金額）しかなく、原価フィールドがない。
工事台帳で粗利（= 売上 - 原価）を計算するために `cost_price`（原価見積）を追加する。

**労務費は対象外**: 労務費の原価は `actual_labor_price`（出面計算）が担うため追加不要。

---

## 追加するカラム

### large_processes / small_processes テーブル

```ruby
# migration
add_column :large_processes, :cost_price, :integer, default: nil, comment: '原価見積（円）'
add_column :large_processes, :cost_price_source, :integer, default: 0, null: false,
           comment: '0:calculated 1:manual 2:ocr_pending 3:ocr_confirmed'

add_column :small_processes, :cost_price, :integer, default: nil, comment: '原価見積（円）'
add_column :small_processes, :cost_price_source, :integer, default: 0, null: false,
           comment: '0:calculated 1:manual 2:ocr_pending 3:ocr_confirmed'
```

### company_overtime_settings テーブル（新規）

```ruby
create_table :company_overtime_settings do |t|
  t.references :company, null: false, foreign_key: true
  t.boolean :overtime_enabled,        default: false, null: false
  t.integer :overtime_rate,            default: 25,   null: false, comment: '時間外割増率(%)'
  t.boolean :night_overtime_enabled,  default: false, null: false
  t.integer :night_overtime_rate,      default: 25,   null: false, comment: '深夜割増率(%)'
  t.boolean :holiday_overtime_enabled, default: false, null: false
  t.integer :holiday_overtime_rate,    default: 35,   null: false, comment: '休日割増率(%)'
  t.boolean :sixty_hour_enabled,       default: false, null: false
  t.integer :sixty_hour_rate,          default: 25,   null: false, comment: '月60h超割増率(%)'
  t.timestamps
end
add_index :company_overtime_settings, :company_id, unique: true
```

### project_users テーブル（追加カラム）

```ruby
# 個別社員が会社設定を上書きするフラグ
add_column :project_users, :overtime_override_enabled, :boolean, default: false, null: false
# override_enabled = true のときのみ参照する個別設定（JSON）
add_column :project_users, :overtime_override_settings, :jsonb, default: {}, null: false
```

`overtime_override_settings` の構造:
```json
{
  "overtime_enabled": false,
  "overtime_rate": 25,
  "night_overtime_enabled": false,
  "night_overtime_rate": 25,
  "holiday_overtime_enabled": false,
  "holiday_overtime_rate": 35,
  "sixty_hour_enabled": false,
  "sixty_hour_rate": 25
}
```

---

## モデル設計

### LargeProcess / SmallProcess

```ruby
enum cost_price_source: {
  calculated: 0,   # 計算値（将来AI）
  manual: 1,       # 手動入力（Lock済み）
  ocr_pending: 2,  # OCR読み取り・未確認
  ocr_confirmed: 3 # OCR読み取り・確認済み
}

# FEに返すバッジ情報
def cost_price_badge
  case cost_price_source
  when 'manual'       then { type: 'manual',       label: '✏️ 手動入力' }
  when 'ocr_pending'  then { type: 'ocr_pending',  label: '📄 OCR（確認待）' }
  when 'ocr_confirmed' then { type: 'ocr_confirmed', label: '📄 OCR（確認済）' }
  else nil  # calculated は将来実装まで表示しない
  end
end
```

### CompanyOvertimeSetting

```ruby
class CompanyOvertimeSetting < ApplicationRecord
  belongs_to :company

  # 設定が有効かつ割増率を返す（割増なしなら nil）
  def effective_rate_for(type)
    enabled = send(:"#{type}_enabled")
    return nil unless enabled
    send(:"#{type}_rate").to_f / 100.0
  end
end
```

### 優先度ロジック（サービス層）

```ruby
# app/services/process_labor_cost/overtime_rate_resolver.rb
class ProcessLaborCost::OvertimeRateResolver
  def initialize(project_user)
    @project_user = project_user
    @company = project_user.company
  end

  def settings
    if @project_user.overtime_override_enabled?
      @project_user.overtime_override_settings  # 個別設定
    else
      @company.company_overtime_setting         # 会社設定
    end
  end
end
```

---

## 既存データへの影響

| テーブル | 影響 | 対処 |
|---|---|---|
| large_processes | cost_price = NULL で追加 | NULL許容・FEでは「未設定」表示 |
| small_processes | 同上 | 同上 |
| project_users | overtime_override_enabled = false | 全社員は会社設定を参照 |
| company_overtime_settings | 全社enabled=false で初期レコード作成 | バッチで全会社分を作成 |

---

## 実装順序

```
1. cost_price カラム追加（大工程・小工程）
2. company_overtime_settings テーブル作成
3. project_users に overtime_override カラム追加
4. OvertimeRateResolver サービス実装
5. ProcessLaborCost::AllocationMath に割増率を乗せる改修
6. FE: cost_price 入力フォーム追加
7. FE: 割増設定画面
```
