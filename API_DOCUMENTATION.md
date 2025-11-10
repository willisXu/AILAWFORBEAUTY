# API 文件 API Documentation

## 概述 Overview

本系統採用靜態資料 API 架構，所有資料以 JSON 格式存儲在 `data/` 目錄中。

This system uses a static data API architecture, with all data stored as JSON files in the `data/` directory.

## 資料端點 Data Endpoints

### 基礎路徑 Base Path

- **開發環境 Development:** `/data/`
- **生產環境 Production:** `/AILAWFORBEAUTY/data/`

### 規則資料 Rules Data

#### 獲取最新規則 Get Latest Rules

**端點 Endpoint:**
```
GET /data/rules/{jurisdiction}/latest.json
```

**參數 Parameters:**
- `jurisdiction`: 市場代碼 (EU, JP, CN, CA, ASEAN)

**回應範例 Response Example:**

```json
{
  "jurisdiction": "EU",
  "version": "20240214",
  "published_at": "2024-02-14T00:00:00Z",
  "effective_date": "2024-02-14T00:00:00Z",
  "fetched_at": "2024-02-14T03:00:00Z",
  "source": "European Commission - CosIng Database",
  "regulation": "Regulation (EC) No 1223/2009",
  "data_hash": "abc123...",
  "statistics": {
    "total_ingredients": 150,
    "total_clauses": 200,
    "banned": 50,
    "restricted": 100,
    "allowed": 50
  },
  "ingredients": [...],
  "clauses": [...]
}
```

#### 獲取特定版本規則 Get Specific Version Rules

**端點 Endpoint:**
```
GET /data/rules/{jurisdiction}/{version}.json
```

**參數 Parameters:**
- `jurisdiction`: 市場代碼
- `version`: 版本號 (例如: 20240214)

### 成分資料庫 Ingredients Database

**端點 Endpoint:**
```
GET /data/ingredients_db.json
```

**回應範例 Response Example:**

```json
{
  "database_version": "1.0.0",
  "last_updated": "2024-02-14",
  "ingredients": {
    "formaldehyde": {
      "id": "formaldehyde",
      "inci": "Formaldehyde",
      "cas": "50-00-0",
      "synonyms": ["Formaldehyde", "Formalin", "Methanal"],
      "family": {
        "formaldehyde_releasers": [...]
      }
    }
  }
}
```

### 版本差異 Version Diffs

**端點 Endpoint:**
```
GET /data/diff/{jurisdiction}/{from_version}_to_{to_version}.json
```

**參數 Parameters:**
- `jurisdiction`: 市場代碼
- `from_version`: 起始版本號
- `to_version`: 目標版本號

**回應範例 Response Example:**

```json
{
  "jurisdiction": "EU",
  "from_version": "20240101",
  "to_version": "20240214",
  "from_date": "2024-01-01T00:00:00Z",
  "to_date": "2024-02-14T00:00:00Z",
  "generated_at": "2024-02-14T03:30:00Z",
  "summary": {
    "total_changes": 15,
    "added": 5,
    "removed": 3,
    "modified": 7,
    "affected_ingredients": 15
  },
  "changes": {
    "added": [...],
    "removed": [...],
    "modified": [...]
  },
  "affected_ingredients": [...]
}
```

## 資料結構 Data Structures

### Clause 條款

```typescript
interface Clause {
  id: string                    // 唯一識別碼
  jurisdiction: string          // 市場代碼
  annex?: string               // 附錄編號 (EU/ASEAN)
  category: string             // banned, restricted, allowed, colorant, preservative, uv_filter
  ingredient_ref: string       // 成分參考名稱
  inci?: string               // INCI 名稱
  cas?: string                // CAS 號碼
  chemical_name?: string      // 化學名稱
  conditions: {
    max_pct?: number          // 最大濃度 (%)
    product_type?: string[]   // 允許的產品類型
    specific_conditions?: any // 特定條件
  }
  warnings?: string           // 警語
  notes: string              // 備註
  source_ref: string         // 來源參考
}
```

### Ingredient 成分

```typescript
interface Ingredient {
  id: string              // 唯一識別碼
  inci: string           // INCI 名稱
  cas?: string           // CAS 號碼
  synonyms: string[]     // 同義詞列表
  family: {
    salts_of?: string                // 鹽類基礎物質
    esters_of?: string[]             // 酯類衍生物
    compounds_of?: string[]          // 化合物
    formaldehyde_releasers?: string[] // 甲醛釋放劑
    polymer_range?: string           // 聚合度範圍
  }
}
```

### Compliance Result 合規結果

```typescript
interface ComplianceResult {
  ingredient_name: string
  jurisdiction: string
  status: 'compliant' | 'restricted_compliant' | 'non_compliant' | 'banned' | 'insufficient_info'
  matched_clauses: Clause[]
  rationale: string
  required_fields?: string[]
  warnings?: string[]
}
```

## 瀏覽器端 API Browser-Side API

### complianceChecker.ts

#### checkIngredient()

檢查單一成分合規性

**函式簽名 Function Signature:**

```typescript
async function checkIngredient(
  ingredient: Ingredient,
  jurisdiction: string,
  productInfo?: any
): Promise<ComplianceResult>
```

**參數 Parameters:**
- `ingredient`: 成分物件
  - `name`: 成分名稱
  - `concentration?`: 濃度 (%)
  - `role?`: 功能
- `jurisdiction`: 市場代碼
- `productInfo?`: 產品資訊
  - `product_type?`: 產品類型
  - 其他選用欄位

**回傳 Returns:**
- `ComplianceResult`: 合規檢查結果

**使用範例 Usage Example:**

```typescript
import { checkIngredient } from '@/lib/complianceChecker'

const result = await checkIngredient(
  {
    name: 'Salicylic Acid',
    concentration: 1.5
  },
  'EU',
  { product_type: 'leave-on' }
)

console.log(result.status)      // 'restricted_compliant'
console.log(result.rationale)   // 詳細說明
```

#### checkFormulation()

檢查整個配方合規性

**函式簽名 Function Signature:**

```typescript
async function checkFormulation(
  ingredients: Ingredient[],
  jurisdictions: string[],
  productInfo?: any
): Promise<Record<string, any>>
```

**參數 Parameters:**
- `ingredients`: 成分陣列
- `jurisdictions`: 市場代碼陣列
- `productInfo?`: 產品資訊

**回傳 Returns:**
- `Record<string, any>`: 各市場的檢查結果

**使用範例 Usage Example:**

```typescript
import { checkFormulation } from '@/lib/complianceChecker'

const ingredients = [
  { name: 'Aqua', concentration: 75.5 },
  { name: 'Glycerin', concentration: 5.0 },
  { name: 'Salicylic Acid', concentration: 1.5 }
]

const results = await checkFormulation(
  ingredients,
  ['EU', 'JP', 'CN'],
  { product_type: 'leave-on' }
)

console.log(results.EU.overall_status)
console.log(results.EU.ingredient_results)
```

## 快取策略 Caching Strategy

### 規則資料快取 Rules Data Cache

```typescript
const rulesCache: Record<string, any> = {}

async function loadRules(jurisdiction: string): Promise<any> {
  if (rulesCache[jurisdiction]) {
    return rulesCache[jurisdiction]
  }

  const rules = await fetch(`/data/rules/${jurisdiction}/latest.json`)
    .then(res => res.json())

  rulesCache[jurisdiction] = rules
  return rules
}
```

### 瀏覽器快取 Browser Cache

- 規則資料會被瀏覽器快取
- 使用 ETags 進行版本控制
- 建議設定 Cache-Control headers

## 錯誤處理 Error Handling

### 常見錯誤 Common Errors

**1. 規則資料不存在 Rules Not Found**

```json
{
  "error": "No rules found for jurisdiction",
  "jurisdiction": "XX"
}
```

**處理方式 Handling:**
- 返回空的 clauses 陣列
- 將成分標記為 'compliant'（無資料，無限制）

**2. 成分名稱無法識別 Ingredient Name Not Recognized**

**處理方式 Handling:**
- 嘗試模糊匹配
- 檢查同義詞
- 如無匹配，返回 'compliant'

**3. 資訊不足 Insufficient Information**

```json
{
  "status": "insufficient_info",
  "required_fields": ["concentration", "product_type"]
}
```

## 版本控制 Versioning

### 規則資料版本 Rules Data Versioning

- 版本號格式：`YYYYMMDD` 或 `YYYYMMDDHHMMSS`
- 每次更新產生新版本檔案
- `latest.json` 指向最新版本
- 保留歷史版本以供追溯

### API 版本 API Version

當前版本：v1.0.0

未來如有重大變更，將使用語意化版本號：
- MAJOR: 不相容的 API 變更
- MINOR: 向下相容的功能新增
- PATCH: 向下相容的問題修正

## 效能建議 Performance Recommendations

### 1. 批量載入 Batch Loading

一次載入所有需要的市場規則：

```typescript
const jurisdictions = ['EU', 'JP', 'CN', 'CA', 'ASEAN']
const rulesPromises = jurisdictions.map(j => loadRules(j))
const allRules = await Promise.all(rulesPromises)
```

### 2. Web Worker

大量成分比對時使用 Web Worker：

```typescript
const worker = new Worker('/worker.js')
worker.postMessage({ ingredients, jurisdictions })
worker.onmessage = (e) => {
  const results = e.data
  // 處理結果
}
```

### 3. 增量更新 Incremental Updates

只重新檢查變更的成分：

```typescript
// 快取之前的結果
const previousResults = {...}

// 只檢查新增或修改的成分
const changedIngredients = ingredients.filter(...)
```

## 整合範例 Integration Examples

### React Hook

```typescript
import { useState, useEffect } from 'react'
import { checkFormulation } from '@/lib/complianceChecker'

export function useComplianceCheck(ingredients, jurisdictions, productInfo) {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (ingredients.length === 0) return

    setLoading(true)
    checkFormulation(ingredients, jurisdictions, productInfo)
      .then(setResults)
      .finally(() => setLoading(false))
  }, [ingredients, jurisdictions, productInfo])

  return { results, loading }
}
```

### Vue Composable

```typescript
import { ref, watch } from 'vue'
import { checkFormulation } from '@/lib/complianceChecker'

export function useComplianceCheck(ingredients, jurisdictions, productInfo) {
  const results = ref(null)
  const loading = ref(false)

  watch(
    () => [ingredients.value, jurisdictions.value, productInfo.value],
    async () => {
      if (ingredients.value.length === 0) return

      loading.value = true
      try {
        results.value = await checkFormulation(
          ingredients.value,
          jurisdictions.value,
          productInfo.value
        )
      } finally {
        loading.value = false
      }
    },
    { deep: true }
  )

  return { results, loading }
}
```

## 授權 License

MIT License

## 變更日誌 Changelog

### v1.0.0 (2024-02-14)

- 初始 API 版本
- 支援 5 大市場
- 完整的合規檢查功能
