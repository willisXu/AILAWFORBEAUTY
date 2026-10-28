# PDF Extractors

PDF表格提取器，用於從各轄區的法規PDF文件中提取化妝品成分數據。

## 模塊結構

```
extractors/
├── __init__.py              # 包初始化
├── base_extractor.py        # 基礎提取器類
├── cn_extractor.py          # 中國（CN）提取器
├── eu_extractor.py          # 歐盟（EU）提取器
├── jp_extractor.py          # 日本（JP）提取器
└── ca_extractor.py          # 加拿大（CA）提取器
```

## 使用方法

### 快速開始

```python
from extractors import CNExtractor, EUExtractor

# 提取中國法規
cn_extractor = CNExtractor()
cn_data = cn_extractor.run()

# 提取歐盟法規
eu_extractor = EUExtractor()
eu_data = eu_extractor.run()
```

### 使用命令行腳本

```bash
# 提取所有轄區
python scripts/extract_regulations_from_pdfs.py

# 提取特定轄區
python scripts/extract_regulations_from_pdfs.py --jurisdictions CN EU

# 僅列出PDF文件
python scripts/extract_regulations_from_pdfs.py --list-only
```

## 提取器說明

### BasePDFExtractor

基礎提取器類，提供通用功能：

- `extract_text_pypdf2()`: 使用PyPDF2提取文本
- `extract_tables_pdfplumber()`: 使用pdfplumber提取表格
- `find_table_start()`: 查找表格開始位置
- `clean_text()`: 清理文本
- `extract_cas_number()`: 提取CAS號
- `save_json()`: 保存JSON文件

### CNExtractor（中國）

從《化妝品安全技術規範》(2015年版)提取：
- 表2-1: 禁用組分（1388項）
- 表2-2: 限用組分（47項）
- 表3-1: 準用防腐劑（51項）
- 表3-2: 準用防曬劑（27項）
- 表3-3: 準用著色劑（157項）
- 表3-4: 準用染髮劑（75項）

### EUExtractor（歐盟）

從Regulation (EC) No 1223/2009提取：
- Annex II: 禁用物質
- Annex III: 限用物質
- Annex IV: 允用色料
- Annex V: 允用防腐劑
- Annex VI: 允用UV過濾劑

### JPExtractor（日本）

從化粧品基準提取：
- ネガティブリスト（禁用清單）
- ポジティブリスト（準用清單）

### CAExtractor（加拿大）

從Cosmetic Ingredient Hotlist提取：
- Prohibited Ingredients（禁用成分）
- Restricted Ingredients（限用成分）

## 依賴要求

```bash
pip install PyPDF2 pdfplumber pandas openpyxl
```

## 輸出格式

提取的數據保存為JSON格式：

```json
{
  "jurisdiction": "CN",
  "source": "...",
  "metadata": {
    "total_ingredients": 1745,
    "extracted_at": "2025-11-12T12:00:00Z",
    ...
  },
  "tables": {
    "prohibited": {
      "ingredients_count": 1388,
      "ingredients": [...]
    }
  }
}
```

## 擴展指南

### 添加新的提取器

1. 繼承 `BasePDFExtractor`
2. 實現 `extract()` 方法
3. 在 `__init__.py` 中導出
4. 在主腳本中註冊

範例：

```python
from .base_extractor import BasePDFExtractor

class NewExtractor(BasePDFExtractor):
    def __init__(self):
        super().__init__("NEW")

    def extract(self) -> Dict[str, Any]:
        # 實現提取邏輯
        pass
```

## 故障排除

### 問題：pdfplumber導入失敗

**解決**：
```bash
pip install cffi cryptography --upgrade
pip install pdfplumber
```

### 問題：提取數據為空

**原因**：PDF結構複雜，需要調試表格識別邏輯

**解決**：
1. 使用 `--list-only` 確認PDF文件存在
2. 檢查PDF文本內容（開發模式）
3. 調整關鍵詞和表格識別邏輯

## 性能優化

- 使用頁面範圍限制：`extract_text_pypdf2(pdf_path, start_page=10, end_page=50)`
- 並行處理多個PDF文件
- 緩存中間結果

## 授權

MIT License - 參見主專案LICENSE文件
