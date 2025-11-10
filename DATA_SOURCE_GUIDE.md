# 📊 法規資料來源說明

## 🎯 總覽

目前系統中的法規資料有**兩種狀態**：

### 1. 當前使用的資料（✅ 已就緒）
- **位置**：`data/rules/{市場}/latest.json`
- **狀態**：**示範資料（Sample Data）**
- **內容**：手動創建的樣本法規數據
- **用途**：前端展示、功能測試、系統演示

### 2. 自動抓取系統（⚙️ 已實現但未啟用）
- **位置**：`scripts/scrapers/`
- **狀態**：**代碼已完成，等待啟用**
- **功能**：自動從各國官方網站抓取最新法規
- **觸發**：GitHub Actions 自動/手動執行

---

## 📂 當前資料狀態

### 現有資料文件

```
data/
├── rules/
│   ├── EU/latest.json       ✅ 示範資料
│   ├── JP/latest.json       ✅ 示範資料
│   ├── CN/latest.json       ✅ 示範資料
│   ├── CA/latest.json       ✅ 示範資料
│   └── ASEAN/latest.json    ✅ 示範資料
├── raw/                      ⚠️ 空目錄（等待自動抓取）
├── parsed/                   ⚠️ 空目錄（等待自動解析）
└── diff/                     ⚠️ 空目錄（等待生成變更）
```

### 示範資料內容

每個 `latest.json` 包含：
```json
{
  "jurisdiction": "EU",
  "version": "20250210",
  "source": "European Commission - CosIng Database",
  "regulation": "Regulation (EC) No 1223/2009",
  "statistics": {
    "total_ingredients": 14,
    "banned": 3,
    "restricted": 4
  },
  "clauses": [
    {
      "id": "EU-AII-1",
      "ingredient_name": "Formaldehyde",
      "cas_no": "50-00-0",
      "restriction_type": "banned",
      "rationale": "Prohibited in all cosmetic products"
    }
    // ... 更多條款
  ]
}
```

這些是我在初始實現時創建的**樣本數據**，用於：
- ✅ 演示系統功能
- ✅ 測試前端界面
- ✅ 驗證合規檢查邏輯

---

## 🤖 自動抓取系統架構

### 系統組件

#### 1. **Scrapers（抓取器）**
**位置**：`scripts/scrapers/`

**功能**：從官方網站抓取法規數據

**支持的市場**：

| 市場 | 官方來源 | 抓取器 |
|------|---------|--------|
| 🇪🇺 **EU** | EC CosIng Database<br/>https://ec.europa.eu/growth/tools-databases/cosing/ | `eu_scraper.py` |
| 🇯🇵 **JP** | MHLW Cosmetics Standards<br/>https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iyakuhin/keshouhin/ | `jp_scraper.py` |
| 🇨🇳 **CN** | NMPA Cosmetics Database<br/>https://www.nmpa.gov.cn/ | `cn_scraper.py` |
| 🇨🇦 **CA** | Health Canada Hotlist<br/>https://www.canada.ca/en/health-canada/services/consumer-product-safety/cosmetics/ | `ca_scraper.py` |
| 🌏 **ASEAN** | ASEAN Cosmetic Directive<br/>https://asean.org/our-communities/economic-community/cosmetics/ | `asean_scraper.py` |

#### 2. **Parsers（解析器）**
**位置**：`scripts/parsers/`

**功能**：將原始數據轉換為標準化格式

#### 3. **Rule Engine（規則引擎）**
**位置**：`scripts/rule_engine.py`

**功能**：
- 標準化法規條款
- 提取禁用/限用成分
- 生成合規檢查規則

#### 4. **Diff Generator（變更追蹤）**
**位置**：`scripts/diff_generator.py`

**功能**：
- 比較新舊版本
- 生成變更摘要
- 識別新增/移除/修改的成分

---

## ⚙️ GitHub Actions 工作流程

### 已實現的自動化

#### 1️⃣ **抓取法規** `.github/workflows/fetch-regulations.yml`

**觸發時機**：
- 📅 每週一 03:00 (台北時間) 自動執行
- 🔘 也可手動觸發

**執行步驟**：
```
1. 下載代碼
2. 安裝 Python 依賴
3. 執行所有市場的爬蟲
4. 保存原始數據到 data/raw/
5. 提交更改到 Git
6. 如果失敗，創建 GitHub Issue
```

**預期輸出**：
```
data/raw/
├── EU/EU_20250210_030000.json
├── JP/JP_20250210_030000.json
├── CN/CN_20250210_030000.json
├── CA/CA_20250210_030000.json
└── ASEAN/ASEAN_20250210_030000.json
```

#### 2️⃣ **解析法規** `.github/workflows/parse-regulations.yml`

**觸發時機**：
- 當 `data/raw/` 有新數據時觸發
- 也可手動觸發

**執行步驟**：
```
1. 讀取 data/raw/ 中的原始數據
2. 使用各市場的解析器處理
3. 標準化為統一格式
4. 應用規則引擎
5. 生成 data/rules/{market}/latest.json
6. 提交更改
```

#### 3️⃣ **生成變更** `.github/workflows/generate-diff.yml`

**觸發時機**：
- 當 `data/rules/` 有更新時觸發

**執行步驟**：
```
1. 比較新舊版本的 latest.json
2. 識別變更：新增/移除/修改
3. 生成變更摘要
4. 保存到 data/diff/
5. 提交更改
```

---

## 🔄 完整數據流程

### 理想的自動化流程

```
每週一 03:00
     ↓
┌────────────────────────────────┐
│  1. Fetch Regulations (抓取)   │
│  - 訪問官方網站                 │
│  - 下載最新法規                 │
│  - 保存原始 HTML/JSON           │
└────────────────────────────────┘
     ↓
     data/raw/{market}/{date}.json
     ↓
┌────────────────────────────────┐
│  2. Parse Regulations (解析)   │
│  - 提取成分資訊                 │
│  - 標準化欄位名稱               │
│  - 分類：禁用/限用/允許         │
└────────────────────────────────┘
     ↓
     data/parsed/{market}/{date}.json
     ↓
┌────────────────────────────────┐
│  3. Apply Rule Engine (規則)   │
│  - 生成合規檢查規則             │
│  - 建立成分索引                 │
│  - 優化查詢性能                 │
└────────────────────────────────┘
     ↓
     data/rules/{market}/latest.json
     ↓
┌────────────────────────────────┐
│  4. Generate Diff (變更追蹤)   │
│  - 與上次版本比較               │
│  - 記錄所有變更                 │
│  - 生成變更報告                 │
└────────────────────────────────┘
     ↓
     data/diff/{market}/{from}_{to}.json
     ↓
┌────────────────────────────────┐
│  5. Deploy (部署到網站)        │
│  - 觸發 GitHub Pages 部署       │
│  - 前端載入最新資料             │
│  - 用戶看到更新                 │
└────────────────────────────────┘
```

---

## ⚠️ 當前實現狀態

### ✅ 已完成
- [x] 完整的爬蟲架構
- [x] 5 個市場的爬蟲實現
- [x] 解析器框架
- [x] 規則引擎
- [x] 變更追蹤器
- [x] GitHub Actions workflows
- [x] 示範資料（供測試使用）

### ⚠️ 需要注意
當前爬蟲中的數據抓取部分使用的是**示範邏輯**：

```python
# scripts/scrapers/eu_scraper.py (第 29-39 行)
def fetch(self) -> Dict[str, Any]:
    # Note: In a real implementation, this would scrape the actual CosIng database
    # For this demo, we'll create a structure that represents the data

    data = {
        "source": "European Commission - CosIng Database",
        "regulation": "Regulation (EC) No 1223/2009",
        "url": "https://ec.europa.eu/growth/tools-databases/cosing/",
        "last_update": "2024-02-14",
        "annexes": self._fetch_annexes(),  # 返回示範數據
    }

    return data
```

### 🔧 需要實現的部分

要讓爬蟲真正從官網抓取數據，需要：

1. **實現真實的 HTTP 請求**
   ```python
   def fetch(self) -> Dict[str, Any]:
       # 真實實現
       response = requests.get(self.jurisdiction_config['sources'][0]['url'])
       soup = BeautifulSoup(response.content, 'html.parser')
       # 解析 HTML 提取數據
       ...
   ```

2. **處理各網站的特殊格式**
   - EU：可能需要下載 PDF 或 Excel 文件
   - CN：可能需要處理中文編碼
   - JP：可能需要處理日文網頁結構

3. **處理反爬蟲機制**
   - 添加適當的 headers
   - 實現請求延遲
   - 處理驗證碼（如果有）

4. **錯誤處理和重試**
   - 網路超時
   - 網站結構變更
   - 數據格式異常

---

## 🚀 如何啟用自動抓取

### 方案 1：手動觸發測試（推薦先試）

1. **訪問 GitHub Actions**：
   ```
   https://github.com/willisXu/AILAWFORBEAUTY/actions/workflows/fetch-regulations.yml
   ```

2. **點擊 "Run workflow"**

3. **查看執行結果**：
   - 如果成功：檢查 `data/raw/` 目錄
   - 如果失敗：查看錯誤日誌，確認需要改進的地方

### 方案 2：等待自動執行

- 每週一 03:00 (台北時間) 會自動執行
- 首次執行可能會失敗（因為使用示範邏輯）
- 需要根據錯誤修改爬蟲代碼

### 方案 3：完善爬蟲實現（建議）

**優先級排序**：

1. **最容易的**：Canada (CA)
   - Health Canada 提供結構化的 Hotlist
   - 可能有 CSV/Excel 下載

2. **中等難度**：EU
   - CosIng 有 API 或可下載的數據庫

3. **較困難**：China (CN)
   - NMPA 網站結構複雜
   - 可能需要處理中文編碼

4. **最困難**：Japan (JP)
   - 日文網頁
   - 數據分散在多個頁面

---

## 💡 建議的改進路徑

### 階段 1：驗證當前系統 ✅
- [x] 使用示範資料測試所有功能
- [x] 確認前端正常工作
- [x] 驗證合規檢查邏輯

### 階段 2：實現第一個真實爬蟲
- [ ] 選擇 Canada 作為起點（最簡單）
- [ ] 實現真實的 HTTP 請求
- [ ] 測試數據抓取
- [ ] 驗證解析邏輯

### 階段 3：擴展到其他市場
- [ ] 依次實現 EU、CN、JP、ASEAN
- [ ] 每個市場獨立測試
- [ ] 處理特殊情況

### 階段 4：啟用自動化
- [ ] 配置 GitHub Actions 權限
- [ ] 測試自動執行
- [ ] 設置錯誤通知

### 階段 5：優化和監控
- [ ] 添加數據驗證
- [ ] 實現變更通知
- [ ] 建立監控儀表板

---

## 📊 當前可用的功能

### 即使使用示範資料，以下功能完全可用：

✅ **成分上傳和比對**
- 上傳 CSV/Excel 成分表
- 檢查 5 個市場的合規性
- 生成合規矩陣

✅ **跨市場比較**
- 查看成分在不同市場的狀態
- 搜尋和篩選
- 匯出 CSV

✅ **報告生成**
- PDF 合規報告
- CSV 數據匯出

### 需要真實數據的功能：

⏳ **法規變更追蹤**
- 需要真實的歷史數據
- 需要定期更新

⏳ **最新法規同步**
- 需要實時抓取
- 需要自動化流程

---

## 🎯 結論

### 當前狀態總結

| 組件 | 狀態 | 說明 |
|------|------|------|
| 前端界面 | ✅ 完成 | 完全可用 |
| 合規檢查引擎 | ✅ 完成 | 邏輯正確 |
| 示範資料 | ✅ 可用 | 足夠測試和演示 |
| 爬蟲架構 | ✅ 完成 | 代碼結構完整 |
| 真實數據抓取 | ⚠️ 示範實現 | 需要完善 |
| 自動化流程 | ⚠️ 配置完成 | 需要測試 |

### 建議

**短期（當前可做）**：
1. ✅ 繼續使用示範資料進行測試
2. ✅ 完善前端功能
3. ✅ 改進用戶體驗
4. ✅ 收集用戶反饋

**中期（1-2 週）**：
1. 🔧 實現第一個真實爬蟲（Canada）
2. 🔧 測試自動化流程
3. 🔧 驗證數據質量

**長期（1 個月+）**：
1. 🎯 完成所有市場的爬蟲
2. 🎯 建立完整的自動化
3. 🎯 實現實時更新

---

## 📞 需要幫助？

如果您想要：
- ✅ 實現真實的數據抓取
- ✅ 優化現有的爬蟲代碼
- ✅ 處理特定網站的抓取邏輯
- ✅ 改進自動化流程

請告訴我具體需求，我可以協助實現！

---

**總結**：系統架構完整，當前使用示範數據，所有前端功能都正常工作。要實現真實的自動抓取，需要完善爬蟲的實際 HTTP 請求和解析邏輯。
