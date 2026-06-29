---
domain: schedule/progress-link
type: requirements
generated_at: 2026-06-29
code_sources:
  - careecon_work/app/models/large_process.rb
  - careecon_work/app/models/small_process.rb
  - careecon_work/app/serializers/api/v2/large_processes/base_serializer.rb
  - careecon_work/app/serializers/concerns/actual_progress_helper.rb
  - careecon_work_frontend/src/mixins/schedule/base-mixin.ts
  - careecon_work_frontend/src/utils/unit-types.ts
  - careecon_work_frontend/src/types/schedule.ts
status: draft
last_reviewed_by: ~
---

# 小工程の人工進捗を大工程にリンクする

## 概要

大工程の `progress_type = refer_to_small_process`（小工程を参照）モードで、  
小工程が `progress_type = actual_value` かつ `unit_type = 人工` の場合、  
小工程の人工進捗を合計して大工程の進捗として表示する機能。

**現状**: 集計ロジックは % の平均のみ。実数値・単位の引き継ぎが未実装。

---

## データモデル

### LargeProcess

```ruby
enum progress_type: {
  percentage: 1,           # 割合
  actual_value: 2,         # 実数値
  refer_to_small_process: 3  # 小工程を参照
}

belongs_to :unit_type, optional: true  # refer_to_small_process 時は null になっている
```

### SmallProcess

```ruby
enum progress_type: {
  percentage: 1,   # 割合
  actual_value: 2  # 実数値（人工はここ）
}

belongs_to :unit_type, optional: true  # 人工 = unit_type_id が特定の値
```

---

## 現状の実装と問題点

### 問題1: `getUnitName()` が null を m² として扱う（FEバグ）

```typescript
// src/mixins/schedule/base-mixin.ts L375
getUnitName(unitType?: number): string {
  const unitKey = Number(unitType) || 1  // ← Number(null) = 0, 0 || 1 = 1 → key=1 が返る
  const unitOptions = getUnitTypesSync()  // localStorage から取得
  return unitOptions.find(item => item.key === unitKey)?.value || unitOptions[0]?.value || ''
}
```

`unit_type_id: null`（= refer_to_small_process で単位未設定）のとき、key=1（通常 m²）を返す。

なお、`validateUnitTypeId()` という正しいバリデーション関数が `utils/unit-types.ts` に存在している:
```typescript
export function validateUnitTypeId(unitTypeId?: number | null): number | null {
  if (!unitTypeId) return null  // ← null を正しくハンドリングしている
  ...
}
```

### 問題2: 集計ロジックが % 平均のみ（FE・BE共通）

**FE（base-mixin.ts L393）:**
```typescript
// REFER_TO_SMALL_PROCESS の集計
const totalProgress = smallProcesses.reduce((sum, sp) => {
  if (sp.progress_type === ProgressType.PERCENTAGE) {
    return sum + Number(sp.progress)  // % をそのまま加算
  } else if (sp.progress_type === ProgressType.ACTUAL_VALUE) {
    // ← 実数値を % に変換して平均を取る（単位は無視）
    return sum + Math.min(Math.round((sp.progress / sp.target) * 100), 100)
  }
  return sum
}, 0)
return Math.min(Math.round(totalProgress / smallProcesses.length), 100)  // ← % の平均
```

**BE（actual_progress_helper.rb）:**
```ruby
def refer_to_small_process_progress_percentage(process)
  percents = process.small_processes.map { |sp| small_process_progress_percentage(sp) }.compact
  return 0 if percents.empty?
  avg = percents.sum / percents.size.to_f
  avg.ceil  # ← % の平均を返すだけ
end
```

どちらも「単位が人工であっても %に変換して平均」するため、`3.5 人工 / 8.0 人工（44%）` ではなく `44%` だけが表示される。

---

## 修正方針

### FR-01: 単位の一致判定

`refer_to_small_process` の大工程に紐づく全小工程を取得し:
- 全小工程が `progress_type = actual_value` かつ `unit_type_id` が同一 → 集計有効
- 混在 or 全小工程が `percentage` → % 平均にフォールバック

### FR-02: 集計有効時の計算式

```
大工程の表示進捗値 = sum(小工程.progress)
大工程の表示目標値 = sum(小工程.target)
大工程の表示単位   = 小工程の共通 unit_type_id
達成率(%)         = 表示進捗値 / 表示目標値 × 100
```

### FR-03: `getUnitName()` の修正

```typescript
// 修正案
getUnitNameForLargeProcess(largeProcess: LargeProcess): string {
  if (largeProcess.progress_type === ProgressType.REFER_TO_SMALL_PROCESS) {
    // 小工程の unit_type_id が統一されていれば引き継ぐ
    const smallProcesses = this.getSmallProcessesByLargeProcessId(largeProcess.id)
    const unitIds = [...new Set(smallProcesses.map(sp => sp.unit_type_id))]
    if (unitIds.length === 1 && unitIds[0]) {
      return this.getUnitName(unitIds[0])
    }
    return ''  // 混在時は単位を表示しない
  }
  return this.getUnitName(largeProcess.unit_type_id)
}
```

### 修正が必要なファイル

| ファイル | 変更内容 |
|---|---|
| `src/mixins/schedule/base-mixin.ts` | `getUnitName()` のフォールバック修正 + 実数値集計ロジック追加 |
| `src/mixins/schedule/base-mixin.ts` | `getProgressRealNumbers()` に単位統一判定を追加 |
| `app/serializers/concerns/actual_progress_helper.rb` | 単位統一時の実数値集計モードを追加 |
| 出来高入力ダイアログ | `refer_to_small_process` + 集計有効時は入力 disabled + 内訳表示 |
| 大工程行コンポーネント | 単位表示の動的切り替え |

### 非機能要件

- 既存の `percentage` / `actual_value` モードに影響を与えない
- `unit_type_id` が null の場合は集計しない（安全側）
- 小工程更新後、大工程の再計算を即時反映（画面リロード不要）

---

## 未解決・確認待ち事項

- [ ] `planned_value` と `target` のどちらを目標値として使うか（シリアライザには両方ある）
- [ ] 小工程の一部のみ `actual_value・人工`、残りが `percentage` の場合の挙動
- [ ] 出来高ダイアログで「手動入力に切り替える」オプションを設けるか

---

## [Human] 背景・意図
<!-- 人間が追記するセクション。Claudeは上書きしない -->


## [Human] 注意事項・例外・経緯
<!-- 人間が追記するセクション。Claudeは上書きしない -->


## [Human] 未解決の疑問・TODO
<!-- 人間が追記するセクション。Claudeは上書きしない -->
