# 數據持久化策略 / Data Persistence Strategy

## 📋 概述 / Overview

本系統採用 **GitHub 倉庫** 作為數據的持久化存儲，確保爬取的法規數據始終可用且有完整的版本歷史。

This system uses **GitHub repository** as persistent storage for scraped data, ensuring regulation data is always available with complete version history.

---

## 🔄 自動化流程 / Automated Workflow

### 1. 定時爬取 / Scheduled Scraping

**時間安排**:
- 每週一凌晨 3:00 (台北時間)
- Every Monday at 03:00 AM (Taipei Time)
- Cron: `0 19 * * 0` (UTC)

**觸發方式**:
```yaml
on:
  schedule:
    - cron: '0 19 * * 0'
  workflow_dispatch:  # 支持手動觸發 / Manual trigger supported
```

### 2. 數據存儲位置 / Data Storage Location

```
data/
├── raw/                    # 原始爬取數據 / Raw scraped data
│   ├── EU/
│   │   ├── latest.json    # 最新版本 / Latest version
│   │   └── EU_20251110....json  # 帶時間戳的版本 / Timestamped version
│   ├── CA/
│   ├── CN/
│   ├── JP/
│   └── ASEAN/
├── parsed/                 # 解析後的數據 / Parsed data
└── diff/                   # 變更記錄 / Change history
```

### 3. 版本控制 / Version Control

**文件命名格式**:
```
{JURISDICTION}_{TIMESTAMP}.json
例如 / Example: EU_20251110100549.json
```

**版本信息** / **Version Information**:
```json
{
  "jurisdiction": "EU",
  "fetched_at": "2025-11-10T10:05:49Z",
  "version": "20251110100549",
  "metadata": {
    "source": "EC CosIng Database",
    "published_at": "2024-04-04",
    "effective_date": "2024-04-24"
  },
  "raw_data": { ... }
}
```

---

## ✅ 成功場景 / Success Scenario

### 流程 / Process

1. **爬取數據** / **Scrape Data**
   ```bash
   cd scripts
   python -m scrapers.fetch_all
   ```

2. **保存到本地** / **Save Locally**
   - `data/raw/{JURISDICTION}/latest.json`
   - `data/raw/{JURISDICTION}/{JURISDICTION}_{TIMESTAMP}.json`

3. **自動提交到 GitHub** / **Auto-commit to GitHub**
   ```bash
   git add data/raw/
   git commit -m "chore: Update regulation data"
   git push
   ```

4. **數據可用** / **Data Available**
   - ✅ 在線數據已更新 / Online data updated
   - ✅ 版本歷史保留 / Version history preserved
   - ✅ 所有市場數據同步 / All markets synchronized

### GitHub Actions 日誌 / Logs

```
✅ EU scraper - 成功 / Success
✅ JP scraper - 成功 / Success
✅ CN scraper - 成功 / Success
✅ CA scraper - 成功 / Success
✅ ASEAN scraper - 成功 / Success

📦 Committed 5 files to GitHub
🚀 Data published to repository
```

---

## ❌ 失敗場景 / Failure Scenario

### 失敗類型 / Failure Types

#### 1. 網絡錯誤 / Network Error
```
❌ EU scraper failed: Unable to fetch data from CosIng database
   RequestException: Connection timeout
```

#### 2. 解析錯誤 / Parsing Error
```
❌ CA scraper failed: Error parsing data from Health Canada Hotlist
   HTMLParseError: Expected table structure not found
```

#### 3. 數據驗證失敗 / Data Validation Error
```
❌ JP scraper failed: No valid data extracted
   DataError: Empty ingredient list
```

### GitHub Actions 行為 / Actions Behavior

1. **顯示錯誤** / **Show Error**
   ```
   ::error::Regulation fetch failed
   Exit code: 1
   ```

2. **創建 Issue** / **Create Issue**
   ```markdown
   ❌ Regulation Fetch Failed

   The regulation fetch workflow failed.

   **Run:** https://github.com/.../actions/runs/...
   **Date:** 2025-11-10T10:05:49Z

   Please check the logs and retry manually if needed.
   ```

3. **不提交數據** / **No Data Committed**
   - ❌ 失敗的數據不會被提交 / Failed data won't be committed
   - ✅ 保持上一次成功的數據 / Keep last successful data
   - ✅ 數據完整性得到保證 / Data integrity guaranteed

### 日誌示例 / Log Example

```
2025-11-10 10:05:47 - scrapers.base_scraper.EU - INFO - Starting scraper for EU
2025-11-10 10:05:47 - scrapers.base_scraper.EU - INFO - Fetching EU cosmetics regulation data
2025-11-10 10:05:49 - scrapers.base_scraper.EU - ERROR - Failed to fetch EU data: HTTPError 503
2025-11-10 10:05:49 - __main__ - ERROR - Failed to fetch EU: EU scraper failed: Unable to fetch data from CosIng database

============================================================
Fetch Summary:
  Successful: 0 / 5
  Failed: 5
  Failed jurisdictions: EU, JP, CN, CA, ASEAN
============================================================
```

---

## 🔧 手動觸發 / Manual Trigger

### 在 GitHub Actions 頁面 / On GitHub Actions Page

1. 訪問 / Visit: `https://github.com/willisXu/AILAWFORBEAUTY/actions`
2. 選擇 / Select: **"Fetch Regulations"** workflow
3. 點擊 / Click: **"Run workflow"** 按鈕
4. 選擇分支 / Select branch: `claude/cosmetics-compliance-audit-system-...`
5. 運行 / Run

### 查看結果 / View Results

- **成功** / **Success**: ✅ 綠色標記，數據已提交
- **失敗** / **Failure**: ❌ 紅色標記，查看日誌了解原因

---

## 📊 數據訪問 / Data Access

### 1. 通過 GitHub 訪問 / Via GitHub

```
https://github.com/willisXu/AILAWFORBEAUTY/tree/main/data/raw
```

### 2. 通過 Git 克隆 / Via Git Clone

```bash
git clone https://github.com/willisXu/AILAWFORBEAUTY.git
cd AILAWFORBEAUTY/data/raw
```

### 3. 通過 Raw GitHub URL / Via Raw GitHub URL

```
https://raw.githubusercontent.com/willisXu/AILAWFORBEAUTY/main/data/raw/EU/latest.json
```

### 4. 在應用中使用 / In Application

```javascript
// Frontend can fetch directly from GitHub
const response = await fetch(
  'https://raw.githubusercontent.com/willisXu/AILAWFORBEAUTY/main/data/raw/EU/latest.json'
);
const data = await response.json();
```

---

## 🔐 數據完整性保證 / Data Integrity Guarantees

### ✅ 保證項 / Guarantees

1. **只提交成功的數據** / **Only Commit Successful Data**
   - 爬取失敗時不會覆蓋舊數據
   - Failed scrapes won't overwrite old data

2. **完整的版本歷史** / **Complete Version History**
   - 所有數據變更都有 Git 記錄
   - All data changes tracked in Git

3. **時間戳標記** / **Timestamp Marking**
   - 每個版本都有明確的獲取時間
   - Each version has clear fetch timestamp

4. **原始數據保留** / **Raw Data Preserved**
   - 保留未經處理的原始數據
   - Unprocessed raw data preserved

### ❌ 不允許的行為 / Prohibited Behaviors

1. ❌ 提交樣本數據（已移除）
2. ❌ 覆蓋失敗的爬取結果
3. ❌ 隱藏錯誤信息
4. ❌ 使用過時數據

---

## 📈 監控與維護 / Monitoring & Maintenance

### 定期檢查 / Regular Checks

1. **每週檢查 GitHub Actions 狀態**
   - Check GitHub Actions status weekly

2. **查看最新數據時間戳**
   - Review latest data timestamps

3. **監控 Issue 通知**
   - Monitor issue notifications

### 故障恢復 / Failure Recovery

1. **查看錯誤日誌** / **Review Error Logs**
   ```
   GitHub Actions → Fetch Regulations → Failed Run → Logs
   ```

2. **手動重試** / **Manual Retry**
   ```
   GitHub Actions → Run workflow
   ```

3. **修復爬蟲代碼**（如果網站結構變化）
   ```bash
   # 更新解析邏輯
   git checkout -b fix/scraper-update
   # 修改 scripts/scrapers/*.py
   git commit -m "fix: Update scraper for new website structure"
   git push
   ```

---

## 🎯 最佳實踐 / Best Practices

### 對於開發者 / For Developers

1. ✅ 定期檢查 GitHub Actions 運行結果
2. ✅ 保持爬蟲代碼與官方網站同步
3. ✅ 及時修復失敗的爬取任務
4. ✅ 記錄每次數據結構變更

### 對於用戶 / For Users

1. ✅ 使用 `latest.json` 獲取最新數據
2. ✅ 檢查 `fetched_at` 時間戳確認數據新鮮度
3. ✅ 關注 GitHub Issues 了解爬取狀態
4. ✅ 在應用中實現數據緩存機制

---

## 📝 總結 / Summary

### ✅ 優勢 / Advantages

- **可靠性**: GitHub 提供高可用性存儲
- **可追溯性**: 完整的 Git 版本歷史
- **透明度**: 所有數據變更公開可見
- **自動化**: 無需人工干預的更新流程
- **免費**: GitHub 免費提供存儲和 Actions

### 🎯 目標達成 / Goals Achieved

1. ✅ 爬取數據後自動保存在線
2. ✅ 不斷更新的數據源
3. ✅ 後端始終有可用數據
4. ✅ 失敗時明確顯示錯誤

---

**最後更新** / **Last Updated**: 2025-11-10
**維護者** / **Maintainer**: Claude Code Assistant
