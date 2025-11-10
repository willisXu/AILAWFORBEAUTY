# 使用者指南 User Guide

## 歡迎 Welcome

歡迎使用跨國化妝品法規自動稽核系統！

Welcome to the Cross-Border Cosmetics Regulation Compliance Audit System!

本系統幫助您快速檢查化妝品配方成分是否符合 EU/JP/CN/CA/ASEAN 市場的法規要求。

This system helps you quickly check if your cosmetic formulation complies with regulations in EU/JP/CN/CA/ASEAN markets.

## 主要功能 Main Features

### 1. 成分合規比對 Ingredient Compliance Check

**步驟 Steps:**

1. **選擇產品類型 Select Product Type**
   - 沖洗型 Rinse-off：如洗髮精、沐浴乳
   - 停留型 Leave-on：如乳液、面霜
   - 髮類 Hair Care
   - 口腔 Oral Care
   - 眼部 Eye Area

2. **選擇目標市場 Select Target Markets**
   - 勾選您想檢查的市場
   - 可同時選擇多個市場進行比對

3. **上傳成分表 Upload Ingredient List**
   - 支援格式 Supported formats: CSV, Excel (.xlsx, .xls)
   - 必要欄位 Required columns:
     - `ingredient_name` 或 `name` 或 `INCI`: 成分名稱
   - 選用欄位 Optional columns:
     - `concentration` 或 `percentage`: 濃度 (%)
     - `role` 或 `function`: 功能

4. **查看結果 View Results**
   - 系統會在幾秒內完成比對
   - 顯示多市場合規矩陣

### 2. 多市場合規矩陣 Multi-Market Compliance Matrix

**結果狀態 Result Status:**

- ✓ **合規 Compliant**
  - 成分符合該市場法規要求
  - 綠色標示

- ⚠ **限用-合規 Restricted-Compliant**
  - 成分受限制但在允許條件下使用
  - 黃色標示
  - 請注意警語與限制條件

- ✗ **不合規 Non-Compliant**
  - 成分超出允許濃度或違反使用條件
  - 紅色標示
  - 需要調整配方

- ⊗ **禁用 Banned**
  - 成分在該市場被禁用
  - 深紅色標示
  - 必須移除該成分

- ? **資訊不足 Insufficient Info**
  - 需要更多資訊才能判定
  - 灰色標示
  - 請補充濃度或產品類型等資訊

**操作 Actions:**

- **匯出 CSV Export CSV**: 下載矩陣資料為 CSV 檔案
- **匯出 PDF Export PDF**: 生成完整的合規報告 PDF

### 3. 法規更新中心 Regulation Update Center

**功能 Features:**

- 查看近期法規變更
- 自動每週更新
- 手動觸發更新

**變更類型 Change Types:**

- ➕ 新增 Added: 新增的法規條款
- ➖ 移除 Removed: 移除的法規條款
- ✏️ 修改 Modified: 修改的法規條款

## 檔案格式範例 File Format Examples

### CSV 範例 CSV Example

```csv
ingredient_name,concentration,role
Aqua,75.5,Solvent
Glycerin,5.0,Humectant
Salicylic Acid,1.5,Exfoliant
Benzoic Acid,0.5,Preservative
```

### Excel 範例 Excel Example

| ingredient_name | concentration | role |
|----------------|---------------|------|
| Aqua | 75.5 | Solvent |
| Glycerin | 5.0 | Humectant |
| Salicylic Acid | 1.5 | Exfoliant |
| Benzoic Acid | 0.5 | Preservative |

## 常見問題 FAQ

### Q1: 系統會上傳我的配方資料嗎？

**A:** 不會。所有比對均在您的瀏覽器本地端完成，不會上傳任何資料到伺服器。

### Q1: Does the system upload my formulation data?

**A:** No. All compliance checks are performed locally in your browser. No data is uploaded to servers.

---

### Q2: 為什麼某些成分顯示「資訊不足」？

**A:** 有些法規限制需要額外資訊（如濃度、產品類型）才能判定。請在上傳檔案中補充這些資訊。

### Q2: Why do some ingredients show "Insufficient Info"?

**A:** Some regulations require additional information (like concentration, product type) for compliance determination. Please provide this information in your uploaded file.

---

### Q3: 法規資料多久更新一次？

**A:** 系統每週一自動更新。您也可以手動觸發更新。

### Q3: How often is regulation data updated?

**A:** The system automatically updates every Monday. You can also trigger manual updates.

---

### Q4: 檢查結果可以作為官方合規證明嗎？

**A:** 本系統結果僅供參考。實際應用請諮詢專業法規顧問，並以各國官方法規為準。

### Q4: Can the check results be used as official compliance proof?

**A:** Results are for reference only. Please consult professional regulatory advisors and refer to official regulations for actual applications.

---

### Q5: 支援哪些成分命名格式？

**A:** 主要支援 INCI (International Nomenclature of Cosmetic Ingredients) 命名。系統也能識別常見的同義詞和 CAS 號碼。

### Q5: What ingredient naming formats are supported?

**A:** Primarily supports INCI (International Nomenclature of Cosmetic Ingredients) naming. The system can also recognize common synonyms and CAS numbers.

---

### Q6: 如何解讀限用條件？

**A:** 點擊矩陣中的單元格可查看詳細說明，包括：
- 最大允許濃度
- 適用產品類型
- 使用限制
- 警語要求

### Q6: How to interpret restriction conditions?

**A:** Click on cells in the matrix to view detailed information, including:
- Maximum allowed concentration
- Applicable product types
- Usage restrictions
- Warning requirements

## 最佳實踐 Best Practices

### 1. 準備成分表 Preparing Ingredient List

- ✅ 使用標準 INCI 命名
- ✅ 提供準確的濃度資訊
- ✅ 明確產品類型
- ✅ 包含所有成分（包括水和防腐劑）

### 2. 解讀結果 Interpreting Results

- ⚠️ 注意所有警語和限制條件
- ⚠️ 檢查是否有「資訊不足」狀態
- ⚠️ 比對多個市場時注意差異
- ⚠️ 特別關注禁用和不合規成分

### 3. 配方調整 Formulation Adjustment

- 🔄 移除禁用成分
- 🔄 調整超標成分濃度
- 🔄 考慮替代成分
- 🔄 重新檢查修改後的配方

## 技術支援 Technical Support

### 回報問題 Report Issues

如遇到問題，請在 GitHub 開啟 Issue：
https://github.com/willisXu/AILAWFORBEAUTY/issues

If you encounter issues, please open a GitHub Issue:
https://github.com/willisXu/AILAWFORBEAUTY/issues

### 功能建議 Feature Requests

歡迎提出改進建議！請透過 GitHub Issues 提交。

Feature suggestions are welcome! Please submit via GitHub Issues.

## 更新日誌 Changelog

### Version 1.0.0 (2025-02-14)

**初始版本 Initial Release**

- ✅ 支援 EU/JP/CN/CA/ASEAN 五大市場
- ✅ 成分合規自動比對
- ✅ 多市場矩陣視圖
- ✅ 法規自動更新
- ✅ 瀏覽器端處理（隱私保護）
- ✅ PDF/CSV 匯出功能
- ✅ 繁中/英文雙語介面

## 附錄：市場法規概覽 Appendix: Market Regulation Overview

### EU (歐盟)

**主要法規:** Regulation (EC) No 1223/2009

**附錄結構:**
- Annex II: 禁用物質
- Annex III: 限用物質
- Annex IV: 允用著色劑
- Annex V: 允用防腐劑
- Annex VI: 允用紫外線過濾劑

### JP (日本)

**主要法規:** Pharmaceutical and Medical Device Act

**特色:**
- 準藥品制度（Quasi-drugs）
- 嚴格的防腐劑限制

### CN (中國)

**主管機關:** NMPA (國家藥品監督管理局)

**主要法規:** 化妝品監督管理條例

**目錄結構:**
- 禁用成分目錄
- 限用成分目錄
- 准用防腐劑目錄
- 准用著色劑目錄

### CA (加拿大)

**主管機關:** Health Canada

**主要法規:** Cosmetic Regulations C.R.C., c. 869

**特色:**
- Cosmetic Ingredient Hotlist
- 分為禁用和限用兩類

### ASEAN (東協)

**主要法規:** ASEAN Cosmetic Directive (ACD)

**特色:**
- 參考 EU 架構
- 涵蓋 10 個成員國
- 逐步協調各國法規

---

感謝使用本系統！

Thank you for using this system!
