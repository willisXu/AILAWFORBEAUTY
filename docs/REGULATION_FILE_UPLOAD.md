# 法規文件上傳功能 Regulation File Upload Feature

## 概述 Overview

本系統已升級為支援直接上傳法規文件進行解析，無需依賴自動爬蟲。此功能允許用戶手動上傳 PDF、JSON 或 HTML 格式的法規文件，系統將自動解析並更新法規數據庫。

This system has been upgraded to support direct regulation file upload and parsing, without relying on automatic scrapers. This feature allows users to manually upload PDF, JSON, or HTML regulation files, which the system will automatically parse and update the regulation database.

## 功能特點 Features

- ✅ 支援多種文件格式：PDF, JSON, HTML
- ✅ 支援所有法規辖區：EU, ASEAN, CN, JP, CA
- ✅ 對於 EU 和 ASEAN 支援選擇附錄 (Annex II-VI)
- ✅ 自動版本控制
- ✅ 完整的錯誤處理和狀態反饋
- ✅ 處理完成後自動提交到 GitHub
- ✅ 支援並發處理多個文件

## 使用方法 How to Use

### 1. 前端上傳 Frontend Upload

1. 訪問應用的 "法規更新中心" (Regulation Update Center)
2. 點擊 "上傳文件" (Upload File) 標籤
3. 選擇法規辖區 (Jurisdiction)
4. 選擇文件類型 (File Type)
5. 對於 EU/ASEAN，選擇附錄編號 (可選)
6. 輸入版本標識 (可選，留空則使用時間戳)
7. 選擇要上傳的文件
8. 點擊 "上傳並處理" (Upload & Process)

### 2. 處理流程 Processing Flow

```
用戶上傳文件
    ↓
API 接收文件 (/api/upload-regulation)
    ↓
文件上傳到 GitHub (data/raw/[jurisdiction]/uploads/)
    ↓
觸發 GitHub Actions 工作流 (process-uploaded-regulation.yml)
    ↓
Python 腳本處理文件 (process_uploaded_file.py)
    ↓
解析並生成規則 (使用對應的 parser)
    ↓
保存結果到 GitHub (data/rules/[jurisdiction]/)
    ↓
自動提交更改
```

### 3. 命令行使用 Command Line Usage

您也可以直接使用命令行處理已上傳的文件：

```bash
cd scripts

# 處理 PDF 文件
python process_uploaded_file.py path/to/file.pdf EU --type pdf --annex II

# 處理 JSON 文件
python process_uploaded_file.py path/to/file.json CN --type json

# 指定版本並輸出結果
python process_uploaded_file.py path/to/file.pdf ASEAN \
  --type pdf \
  --annex III \
  --version 2024-12 \
  --output result.json
```

## 文件格式要求 File Format Requirements

### PDF 文件 PDF Files

- 應包含表格數據
- 系統使用 pdfplumber 提取表格內容
- 建議使用標準化的法規文件格式

### JSON 文件 JSON Files

JSON 文件應遵循以下結構：

```json
{
  "jurisdiction": "EU",
  "version": "2024-12",
  "metadata": {
    "source": "Official Source",
    "published_at": "2024-12-06",
    "effective_date": "2024-12-06",
    "regulation": "Regulation Name"
  },
  "raw_data": {
    "annexes": {
      "annex_ii": {
        "ingredients": [
          {
            "ingredient_name": "Ingredient Name",
            "inci_name": "INCI Name",
            "cas_no": "CAS Number",
            "conditions": "Conditions",
            "rationale": "Rationale"
          }
        ]
      }
    }
  }
}
```

### HTML 文件 HTML Files

- 應包含結構化的表格數據
- 系統將提取表格並解析內容

## API 端點 API Endpoints

### POST /api/upload-regulation

上傳法規文件

**請求參數 Request Parameters:**

- `file` (File, required): 要上傳的文件
- `jurisdiction` (String, required): 法規辖區 (EU, JP, CN, CA, ASEAN)
- `fileType` (String, optional): 文件類型 (pdf, json, html), 默認: pdf
- `annex` (String, optional): 附錄編號 (for EU/ASEAN)
- `version` (String, optional): 版本標識

**響應 Response:**

```json
{
  "success": true,
  "message": "File uploaded and processing triggered",
  "data": {
    "jurisdiction": "EU",
    "filename": "20241206120000_II.pdf",
    "file_path": "data/raw/EU/uploads/20241206120000_II.pdf",
    "timestamp": "20241206120000"
  }
}
```

## 目錄結構 Directory Structure

```
data/
├── raw/
│   └── [jurisdiction]/
│       └── uploads/          # 上傳的原始文件
│           ├── [timestamp]_[annex].pdf
│           └── [timestamp]_[annex].json
└── rules/
    └── [jurisdiction]/
        ├── [version].json    # 版本化的規則
        └── latest.json       # 最新規則
```

## GitHub Actions 工作流 GitHub Actions Workflow

### process-uploaded-regulation.yml

此工作流處理上傳的法規文件：

**觸發方式 Triggered by:**
- workflow_dispatch (手動觸發或 API 調用)

**輸入參數 Inputs:**
- `jurisdiction`: 法規辖區
- `file_type`: 文件類型
- `annex`: 附錄編號 (可選)
- `version`: 版本標識 (可選)
- `file_path`: 文件在倉庫中的路徑

**執行步驟 Steps:**
1. 檢出倉庫
2. 設置 Python 環境
3. 安裝依賴
4. 運行處理腳本
5. 讀取處理結果
6. 提交更改
7. 生成摘要
8. 失敗時創建 Issue

## 解析器 Parsers

系統使用以下 V2 解析器處理不同辖區的法規（基於多表架構）：

- **EU**: `EUParserV2` - 處理 EU Regulation (EC) No 1223/2009
- **ASEAN**: `ASEANParserV2` - 處理 ASEAN Cosmetic Directive
- **CN**: `CNParserV2` - 處理中國化妝品安全技術規範
- **JP**: `JPParserV2` - 處理日本化妝品基準
- **CA**: `CAParserV2` - 處理加拿大 Cosmetic Ingredient Hotlist

每個解析器都繼承自 `BaseParserV2`，並實現特定於辖區的解析邏輯。V2 解析器支持多表架構（Prohibited, Restricted, Preservatives, UV_Filters, Colorants, Whitelist）。

## 錯誤處理 Error Handling

系統提供完整的錯誤處理：

- 文件驗證失敗
- 解析錯誤
- GitHub API 錯誤
- 處理超時 (20 分鐘)

錯誤信息將顯示在前端，並在 GitHub Actions 中創建 Issue。

## 環境變量 Environment Variables

需要配置以下環境變量：

```bash
# GitHub Personal Access Token (需要 repo 和 workflow 權限)
GITHUB_TOKEN=your_github_token

# GitHub 分支 (可選，默認為 main)
GITHUB_BRANCH=main
```

## 注意事項 Notes

1. **文件大小限制**: 最大 50MB
2. **處理時間**: 通常需要 1-3 分鐘
3. **並發限制**: GitHub Actions 有並發限制
4. **版本控制**: 系統自動為每次上傳創建版本
5. **數據驗證**: 上傳前請確保文件格式正確

## 疑難排解 Troubleshooting

### 上傳失敗

- 檢查文件大小是否超過限制
- 確認文件格式是否正確
- 檢查網絡連接

### 處理失敗

- 查看 GitHub Actions 日誌
- 檢查文件內容是否符合格式要求
- 確認解析器是否支援該文件格式

### 結果未顯示

- 等待 2-3 分鐘後刷新頁面
- 檢查 GitHub Actions 是否完成
- 查看是否有錯誤 Issue 創建

## 相關文件 Related Files

- `scripts/process_uploaded_file.py` - 文件處理腳本
- `api/upload-regulation.js` - API 端點
- `app/src/components/RegulationFileUpload.tsx` - 前端上傳組件
- `.github/workflows/process-uploaded-regulation.yml` - GitHub Actions 工作流
- `scripts/parsers/` - 解析器目錄

## 未來改進 Future Improvements

- [ ] 支援批量上傳
- [ ] 添加文件預覽功能
- [ ] 實時處理進度顯示
- [ ] 支援更多文件格式
- [ ] 添加文件校驗功能
- [ ] 支援增量更新
- [ ] 添加回滾功能

## 支援 Support

如有問題或建議，請在 GitHub Issues 中提出。

For questions or suggestions, please create a GitHub Issue.
