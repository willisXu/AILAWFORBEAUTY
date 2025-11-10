# 系統設置指南 Setup Guide

## 快速開始 Quick Start

### 1. 環境需求 Environment Requirements

**Python 環境 Python Environment:**
- Python 3.11+
- pip

**Node.js 環境 Node.js Environment:**
- Node.js 20+
- npm

### 2. 安裝步驟 Installation Steps

#### 後端設置 Backend Setup

```bash
# 安裝 Python 依賴 Install Python dependencies
cd scripts
pip install -r requirements.txt
```

#### 前端設置 Frontend Setup

```bash
# 安裝 Node.js 依賴 Install Node.js dependencies
cd app
npm install
```

### 3. 開發模式 Development Mode

#### 執行爬蟲 Run Scrapers

```bash
cd scripts
python -m scrapers.fetch_all
```

#### 解析資料 Parse Data

```bash
cd scripts
python -m parsers.parse_all
```

#### 啟動前端 Start Frontend

```bash
cd app
npm run dev
```

訪問 http://localhost:3000 查看應用程式

### 4. 生產部署 Production Deployment

#### 建置靜態網站 Build Static Site

```bash
cd app
npm run build
```

輸出目錄：`app/out/`

#### GitHub Pages 部署 Deploy to GitHub Pages

系統會自動通過 GitHub Actions 部署到 GitHub Pages。

觸發條件 Triggers:
- Push to `main` branch
- 修改 `app/` 或 `data/` 目錄
- 手動觸發 Manual trigger via GitHub Actions

## GitHub Actions 設定 GitHub Actions Configuration

### 啟用 GitHub Pages Enable GitHub Pages

1. 前往 Repository Settings → Pages
2. Source: GitHub Actions
3. 儲存 Save

### Workflow 說明 Workflow Description

**1. Fetch Regulations** (`fetch-regulations.yml`)
- 排程：每週一 03:00 Asia/Taipei
- 手動觸發：支援
- 功能：抓取 EU/JP/CN/CA/ASEAN 法規資料

**2. Parse Regulations** (`parse-regulations.yml`)
- 觸發：`data/raw/` 有變更時
- 功能：解析原始資料為結構化 JSON

**3. Generate Diff** (`generate-diff.yml`)
- 觸發：`data/rules/` 有變更時
- 功能：產生版本差異報告

**4. Deploy Pages** (`deploy-pages.yml`)
- 觸發：`main` 分支有變更時
- 功能：建置並部署前端到 GitHub Pages

## 資料結構 Data Structure

```
data/
├── raw/                    # 原始資料
│   ├── EU/
│   ├── JP/
│   ├── CN/
│   ├── CA/
│   └── ASEAN/
├── parsed/                 # 解析後資料 (中間件)
├── rules/                  # 規則資料集
│   ├── EU/
│   │   ├── latest.json    # 最新版本
│   │   └── 20240214*.json # 版本化資料
│   └── ...
└── diff/                   # 版本差異
    ├── EU/
    │   ├── v1_to_v2.json
    │   └── v1_to_v2.md    # 人類可讀的變更日誌
    └── ...
```

## 測試 Testing

### 執行爬蟲測試 Test Scrapers

```bash
cd scripts
python -m pytest tests/test_scrapers.py -v
```

### 執行規則引擎測試 Test Rule Engine

```bash
cd scripts
python rule_engine.py  # 執行內建測試
```

### 前端測試 Frontend Testing

```bash
cd app
npm run lint
npm run build  # 確保可以建置成功
```

## 故障排除 Troubleshooting

### 問題：爬蟲失敗 Issue: Scraper Failed

**解決方案 Solution:**
1. 檢查網路連線 Check network connection
2. 查看 GitHub Actions 日誌 Check GitHub Actions logs
3. 驗證來源網站是否可訪問 Verify source websites are accessible

### 問題：前端無法載入資料 Issue: Frontend Cannot Load Data

**解決方案 Solution:**
1. 確認 `data/rules/` 目錄有資料檔案
2. 檢查 GitHub Pages 是否已啟用
3. 驗證 `next.config.js` 的 basePath 設定

### 問題：GitHub Pages 404 錯誤 Issue: GitHub Pages 404 Error

**解決方案 Solution:**
1. 確認 `.nojekyll` 檔案存在
2. 檢查 Repository Settings → Pages 設定
3. 重新觸發 Deploy Pages workflow

## 效能優化 Performance Optimization

### 快取策略 Caching Strategy

- 規則資料在瀏覽器端快取 Rules data cached in browser
- GitHub Actions 使用 pip/npm cache
- 靜態資產由 CDN 提供 Static assets served via CDN

### 資料更新頻率 Data Update Frequency

- 自動更新：每週一次 Automatic: Weekly
- 手動更新：隨時可觸發 Manual: On-demand

## 安全性 Security

### 資料隱私 Data Privacy

- ✅ 所有成分比對在瀏覽器端完成
- ✅ 不上傳使用者檔案
- ✅ 不蒐集使用者行為
- ✅ 無後端伺服器

### GitHub Secrets

不需要設定 Secrets（系統不使用任何私密憑證）

No secrets required (system uses no private credentials)

## 貢獻指南 Contributing

1. Fork repository
2. 建立 feature branch
3. 提交 Pull Request
4. 等待審核 Wait for review

## 授權 License

MIT License

## 支援 Support

如有問題，請開啟 GitHub Issue
For questions, please open a GitHub Issue
