# PDF法規數據提取指南

本指南說明如何從PDF法規文件中提取化妝品成分數據。

## 📊 數據概覽

### 當前狀態

| 轄區 | 當前記錄數 | PDF包含數據 | 狀態 | PDF文件 |
|------|-----------|------------|------|---------|
| **CN** | 0 | 1388禁用+47限用+310準用=**1745條** | ⚠️ 需提取 | 11MB, 563頁 |
| **EU** | 8 | 5個Annex（禁/限/色/防/UV） | ⚠️ 需提取 | ~1.4MB |
| **JP** | 12 | 完整標準文件 | ⚠️ 需確認 | 126KB |
| **CA** | 7 | Hotlist清單 | ⚠️ 需確認 | 495KB |
| **ASEAN** | 2830 | Annex II | ✓ 已完整 | 1.7MB |

**預期總數**: >3000條法規記錄

---

## 🚀 快速開始

### 方案一：使用GitHub Actions（推薦）

1. **觸發workflow**
   ```bash
   # 在GitHub網頁上：
   Actions > Extract PDF Regulations > Run workflow

   # 或使用gh CLI：
   gh workflow run extract-pdf-regulations.yml
   ```

2. **指定轄區**（可選）
   ```bash
   # 只提取中國法規
   gh workflow run extract-pdf-regulations.yml -f jurisdictions="CN"

   # 提取多個轄區
   gh workflow run extract-pdf-regulations.yml -f jurisdictions="CN EU JP"
   ```

3. **查看結果**
   - Actions標籤頁查看執行日誌
   - 提取的數據自動提交到 `data/extracted/`
   - 下載artifacts查看提取結果

### 方案二：本地執行

#### 1. 安裝依賴

```bash
# 基本依賴
pip install PyPDF2

# 完整功能（表格提取）
pip install pdfplumber pandas openpyxl
```

#### 2. 執行提取

```bash
# 列出所有PDF文件
python scripts/extract_regulations_from_pdfs.py --list-only

# 提取所有轄區
python scripts/extract_regulations_from_pdfs.py

# 提取特定轄區
python scripts/extract_regulations_from_pdfs.py --jurisdictions CN EU JP CA
```

#### 3. 查看結果

```bash
# 檢查提取的數據
ls -lh data/extracted/*/extracted_latest.json

# 查看中國數據摘要
python -c "import json; data=json.load(open('data/extracted/CN/extracted_latest.json')); print(f\"Total: {data['metadata']['total_ingredients']} ingredients\")"
```

---

## 📁 文件結構

```
data/
├── raw/                          # 原始PDF文件
│   ├── CN/
│   │   └── cosmetics_safety_technical_standards_2015.pdf
│   ├── EU/
│   │   ├── 附件1-1_歐盟LIST OF SUBSTANCES PROHIBITED.pdf
│   │   ├── 附件1-2_歐盟LIST OF SUBSTANCES RESTRICTED.pdf
│   │   ├── 附件1-3_歐盟LIST OF COLORANTS ALLOWED.pdf
│   │   ├── 附件1-4_歐盟LIST OF PRESERVATIVES ALLOWED.pdf
│   │   └── 附件1-5_歐盟LIST OF UV FILTERS ALLOWED.pdf
│   ├── JP/
│   │   └── 附件2-1_日本Standards for Cosmetic Products.pdf
│   └── CA/
│       └── 附件4_加拿大Cosmetic Ingredient Hotlist.pdf
│
└── extracted/                    # 提取的JSON數據
    ├── CN/
    │   └── extracted_latest.json
    ├── EU/
    │   └── extracted_latest.json
    ├── JP/
    │   └── extracted_latest.json
    └── CA/
        └── extracted_latest.json
```

---

## 🔧 提取器說明

### CN提取器 (`CNExtractor`)

**數據來源**: 化妝品安全技術規範（2015年版）

**提取內容**:
- 表2-1: 化妝品禁用組分（1388項）
- 表2-2: 化妝品限用組分（47項）
- 表3-1: 準用防腐劑（51項）
- 表3-2: 準用防曬劑（27項）
- 表3-3: 準用著色劑（157項）
- 表3-4: 準用染髮劑（75項）

**字段映射**:
```python
{
    "序號": "serial_number",
    "化妝品原料名稱": "ingredient_name",
    "使用目的/理由": "purpose_rationale",
    "使用範圍/限用條件": "usage_restrictions",
    "最大允許濃度": "max_concentration"
}
```

### EU提取器 (`EUExtractor`)

**數據來源**: Regulation (EC) No 1223/2009

**提取內容**:
- Annex II: 禁用物質
- Annex III: 限用物質
- Annex IV: 允用色料
- Annex V: 允用防腐劑
- Annex VI: 允用UV過濾劑

### JP提取器 (`JPExtractor`)

**數據來源**: 化粧品基準（Standards for Cosmetics）

**提取內容**:
- ネガティブリスト（Negative List）：禁用成分
- ポジティブリスト（Positive List）：準用成分

### CA提取器 (`CAExtractor`)

**數據來源**: Cosmetic Ingredient Hotlist

**提取內容**:
- Prohibited Ingredients
- Restricted Ingredients

---

## 📝 輸出格式

提取的數據保存為JSON格式：

```json
{
  "jurisdiction": "CN",
  "source": "化妝品安全技術規範（2015年版）",
  "source_url": "https://...",
  "pdf_path": "/path/to/pdf",
  "metadata": {
    "jurisdiction": "CN",
    "extracted_at": "2025-11-12T12:00:00Z",
    "total_ingredients": 1745,
    "extractor": "pdf_table_extractor",
    "extractor_version": "1.0.0"
  },
  "tables": {
    "prohibited": {
      "table_name": "化妝品禁用組分",
      "table_number": "表2-1",
      "expected_count": 1388,
      "ingredients_count": 1388,
      "ingredients": [
        {
          "serial_number": "1",
          "ingredient_name": "2-乙酰氧基乙基三甲基氯化铵",
          "cas_no": "123-45-6",
          "purpose_rationale": "..."
        }
      ]
    }
  }
}
```

---

## 🛠️ 技術實現

### 提取策略

1. **文本提取** (使用PyPDF2)
   - 提取所有頁面文本
   - 識別表格開始位置
   - 提取基本結構信息

2. **表格提取** (使用pdfplumber - 在本地/CI環境)
   - 自動識別表格邊界
   - 提取表格單元格數據
   - 處理跨頁表格

3. **數據清洗**
   - 移除空白和特殊字符
   - 提取CAS號
   - 統一字段格式

### 關鍵類和方法

```python
# 基類
class BasePDFExtractor:
    def extract_text_pypdf2(pdf_path, start_page, end_page)
    def extract_tables_pdfplumber(pdf_path, start_page, end_page)
    def find_table_start(texts, keywords)
    def clean_text(text)
    def extract_cas_number(text)

# CN提取器
class CNExtractor(BasePDFExtractor):
    def extract_prohibited_table(texts)
    def extract_restricted_table(texts)
    def extract_preservatives_table(texts)
```

---

## ⚠️ 常見問題

### Q1: pdfplumber安裝失敗

**問題**: `ModuleNotFoundError: No module named '_cffi_backend'`

**解決**:
```bash
# 安裝依賴
pip install cffi cryptography --upgrade
pip install pdfplumber
```

### Q2: GitHub Actions中如何查看提取結果？

**解決**:
1. Actions > 選擇workflow run
2. 點擊 "Artifacts" 下載 `extracted-regulations`
3. 或查看提交歷史中的自動提交

### Q3: 提取的數據為0條

**原因**: 當前環境不支持完整表格提取（缺少pdfplumber）

**解決**: 在本地或CI環境中執行（已配置GitHub Actions workflow）

### Q4: 如何驗證提取數據的正確性？

```bash
# 檢查記錄數
python -c "
import json
from pathlib import Path

for jur in ['CN', 'EU', 'JP', 'CA']:
    path = Path(f'data/extracted/{jur}/extracted_latest.json')
    if path.exists():
        data = json.load(open(path))
        count = data['metadata']['total_ingredients']
        print(f'{jur}: {count} 條記錄')
"

# 查看詳細數據
python -c "
import json
data = json.load(open('data/extracted/CN/extracted_latest.json'))
prohibited = data['tables']['prohibited']
print(f\"禁用組分: {prohibited['ingredients_count']} / {prohibited['expected_count']}\")
"
```

---

## 🔄 定期更新

### 自動執行

GitHub Actions配置了定期執行（每月1號）：

```yaml
schedule:
  - cron: '0 0 1 * *'  # 每月1號 00:00 UTC
```

### 手動觸發

當PDF文件更新時：

1. 替換 `data/raw/<jurisdiction>/` 下的PDF文件
2. 提交推送到main分支
3. GitHub Actions自動執行提取
4. 或手動觸發workflow

---

## 📞 支持

如遇問題請：

1. 查看 [GitHub Actions日誌](../../actions/workflows/extract-pdf-regulations.yml)
2. 檢查 [Issues](../../issues)
3. 提交新的Issue並附上錯誤信息

---

## 📈 下一步

1. ✅ 運行PDF提取
2. ✅ 驗證提取數據
3. 🔄 更新解析器以支持新格式
4. 🔄 將提取的數據整合到現有系統
5. 🔄 更新前端以顯示完整數據

---

**最後更新**: 2025-11-12
**維護者**: AI Law for Beauty Team
