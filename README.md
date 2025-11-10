# 跨國化妝品法規自動稽核與成分風險比對系統

Cross-Border Cosmetics Regulation Compliance Audit System

## 概述 Overview

自動化法規追蹤與成分合規性檢查系統，支援 EU/JP/CN/CA/ASEAN 市場。

Automated regulation tracking and ingredient compliance checking system for EU/JP/CN/CA/ASEAN markets.

## 功能特點 Features

- ✅ 每週自動抓取化妝品法規更新 (Weekly automated regulation updates)
- ✅ 成分表上傳與即時合規比對 (Ingredient upload and real-time compliance check)
- ✅ 多市場風險矩陣 (Multi-market risk matrix)
- ✅ 法規變更影響告警 (Regulation change impact alerts)
- ✅ 瀏覽器端處理，無資料上傳 (Browser-side processing, no data upload)
- ✅ 完整版本控制與追溯 (Full version control and traceability)

## 系統架構 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Repository                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Frontend   │  │   Scripts    │  │  Workflows   │  │
│  │  (Next.js)   │  │  (Python)    │  │  (Actions)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Data (Versioned JSON)                  │  │
│  │  /raw  /parsed  /rules  /diff                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                ┌──────────────────┐
                │  GitHub Pages    │
                │  Static Website  │
                └──────────────────┘
```

## 快速開始 Quick Start

### 前端開發 Frontend Development

```bash
cd app
npm install
npm run dev
```

### 執行爬蟲 Run Scrapers

```bash
cd scripts
pip install -r requirements.txt
python -m scrapers.fetch_all
```

### 手動觸發更新 Manual Update Trigger

前往 [Actions](../../actions) 頁面，執行 `Fetch Regulations` 工作流程。

Go to [Actions](../../actions) page and run the `Fetch Regulations` workflow.

## 專案結構 Project Structure

```
.
├── app/                    # Next.js 前端應用
│   ├── components/         # React 組件
│   ├── pages/             # 頁面路由
│   ├── lib/               # 工具函數
│   └── public/            # 靜態資源
├── scripts/               # Python 腳本
│   ├── scrapers/          # 爬蟲模組
│   ├── parsers/           # 解析器
│   └── utils/             # 工具函數
├── data/                  # 資料目錄 (版本化)
│   ├── raw/               # 原始資料
│   ├── parsed/            # 解析後資料
│   ├── rules/             # 規則資料集
│   └── diff/              # 版本差異
└── .github/workflows/     # GitHub Actions

```

## 支援市場 Supported Markets

| 市場 Market | 資料來源 Data Source | 更新週期 Update Frequency |
|------------|---------------------|-------------------------|
| 🇪🇺 EU | EC Cosmetics Regulation | Weekly |
| 🇯🇵 JP | MHLW Notifications | Weekly |
| 🇨🇳 CN | NMPA Cosmetics Database | Weekly |
| 🇨🇦 CA | Health Canada Cosmetics | Weekly |
| 🌏 ASEAN | ASEAN Cosmetic Directive | Weekly |

## 資料模型 Data Model

### Ingredient 成分

```json
{
  "id": "string",
  "inci": "string",
  "cas": "string",
  "synonyms": ["string"],
  "family": {
    "salts_of": "string",
    "esters_of": "string",
    "polymer_range": "string"
  }
}
```

### Clause 條款

```json
{
  "id": "string",
  "jurisdiction": "EU|JP|CN|CA|ASEAN",
  "ingredient_ref": "string",
  "category": "banned|restricted|allowed|colorant|preservative|uv",
  "conditions": {
    "max_pct": "number",
    "product_type": ["string"],
    "site": ["string"],
    "age": "string"
  },
  "notes": "string",
  "version": "string",
  "source_ref": "string"
}
```

## 效能指標 Performance Metrics

- ⚡ 100 條成分比對：≤ 10 秒 (P95)
- ⚡ 1000 條成分比對：≤ 45 秒 (P95)
- 🎯 匹配精確率：≥ 98%
- 🎯 匹配召回率：≥ 97%
- 🎯 命名正規化準確率：≥ 98%

## 隱私與安全 Privacy & Security

- ✅ 所有比對在瀏覽器端完成
- ✅ 不上傳使用者檔案至伺服器
- ✅ 不蒐集使用者行為紀錄
- ✅ 本地 SKU 清單僅存於 localStorage
- ✅ 可一鍵清除所有本地資料

## 授權 License

MIT License

## 聯絡方式 Contact

如有問題或建議，請開啟 [Issue](../../issues)。

For questions or suggestions, please open an [Issue](../../issues).
