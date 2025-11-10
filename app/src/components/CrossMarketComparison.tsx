'use client'

import { useState, useEffect } from 'react'

interface IngredientMarketStatus {
  ingredient_name: string
  markets: {
    [market: string]: {
      status: string
      category: string
    }
  }
}

const statusTranslations: { [key: string]: string } = {
  'banned': '禁止',
  'prohibited': '禁止',
  'restricted': '限用',
  'monitored': '監測',
  'allowed': '允許',
  'compliant': '合規',
  'non_compliant': '不合規'
}

const statusColors: { [key: string]: string } = {
  'banned': 'bg-red-100 text-red-900 border-red-300',
  'prohibited': 'bg-red-100 text-red-900 border-red-300',
  'restricted': 'bg-yellow-100 text-yellow-900 border-yellow-300',
  'monitored': 'bg-blue-100 text-blue-900 border-blue-300',
  'allowed': 'bg-green-100 text-green-900 border-green-300',
  'compliant': 'bg-green-100 text-green-900 border-green-300',
  'non_compliant': 'bg-red-100 text-red-900 border-red-300'
}

export default function CrossMarketComparison() {
  const [comparisonData, setComparisonData] = useState<IngredientMarketStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  const markets = ['CN', 'JP', 'EU', 'CA', 'ASEAN']

  useEffect(() => {
    loadComparisonData()
  }, [])

  const loadComparisonData = async () => {
    try {
      const basePath = process.env.NODE_ENV === 'production' ? '/AILAWFORBEAUTY' : ''
      const allIngredients: { [key: string]: IngredientMarketStatus } = {}

      // 載入所有市場的法規資料
      for (const market of markets) {
        try {
          const response = await fetch(`${basePath}/data/rules/${market}/latest.json`)
          if (response.ok) {
            const data = await response.json()

            // 處理不同類別的成分
            const categories = ['banned', 'prohibited', 'restricted', 'monitored']

            categories.forEach(category => {
              const ingredients = data[category] || data.clauses?.filter((c: any) =>
                c.restriction_type === category || c.type === category
              ) || []

              ingredients.forEach((ingredient: any) => {
                const name = ingredient.ingredient_name || ingredient.name || ingredient.inci_name
                if (!name) return

                if (!allIngredients[name]) {
                  allIngredients[name] = {
                    ingredient_name: name,
                    markets: {}
                  }
                }

                allIngredients[name].markets[market] = {
                  status: category,
                  category: ingredient.category || ingredient.product_type || 'all'
                }
              })
            })
          }
        } catch (error) {
          console.debug(`Failed to load ${market} regulations:`, error)
        }
      }

      // 補充未列入的市場狀態為 "允許"
      Object.values(allIngredients).forEach(ingredient => {
        markets.forEach(market => {
          if (!ingredient.markets[market]) {
            ingredient.markets[market] = {
              status: 'allowed',
              category: 'all'
            }
          }
        })
      })

      setComparisonData(Object.values(allIngredients))
    } catch (error) {
      console.error('Error loading comparison data:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredData = comparisonData.filter(item => {
    const matchesSearch = item.ingredient_name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === 'all' ||
      Object.values(item.markets).some(m => m.status === selectedCategory)
    return matchesSearch && matchesCategory
  })

  const exportToCSV = () => {
    let csv = '成分名稱,Ingredient Name,' + markets.join(',') + '\n'

    filteredData.forEach(item => {
      const row = [
        item.ingredient_name,
        item.ingredient_name,
        ...markets.map(market => statusTranslations[item.markets[market].status] || item.markets[market].status)
      ]
      csv += row.join(',') + '\n'
    })

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'cross-market-comparison.csv'
    a.click()
  }

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">載入中... Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          跨市場成分比較 Cross-Market Ingredient Comparison
        </h2>
        <button
          onClick={exportToCSV}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          匯出 CSV Export CSV
        </button>
      </div>

      {/* 搜尋和篩選 */}
      <div className="mb-6 flex flex-col md:flex-row gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="搜尋成分名稱 Search ingredient..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
        </div>
        <div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          >
            <option value="all">所有類別 All Categories</option>
            <option value="banned">禁止 Banned</option>
            <option value="restricted">限用 Restricted</option>
            <option value="monitored">監測 Monitored</option>
            <option value="allowed">允許 Allowed</option>
          </select>
        </div>
      </div>

      {/* 統計資訊 */}
      <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          顯示 <span className="font-semibold text-gray-900 dark:text-white">{filteredData.length}</span> 個成分
          （共 <span className="font-semibold">{comparisonData.length}</span> 個）
        </p>
      </div>

      {/* 比較表格 */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gray-100 dark:bg-gray-700">
              <th className="border border-gray-300 dark:border-gray-600 px-4 py-3 text-left font-semibold sticky left-0 bg-gray-100 dark:bg-gray-700 z-10">
                成分名稱<br/>Ingredient Name
              </th>
              {markets.map((market) => (
                <th
                  key={market}
                  className="border border-gray-300 dark:border-gray-600 px-4 py-3 text-center font-semibold min-w-[120px]"
                >
                  {market === 'CN' && '中國'}
                  {market === 'JP' && '日本'}
                  {market === 'EU' && '歐盟'}
                  {market === 'CA' && '加拿大'}
                  {market === 'ASEAN' && '東協'}
                  <br/>
                  <span className="text-xs font-normal">{market}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredData.length === 0 ? (
              <tr>
                <td colSpan={markets.length + 1} className="border border-gray-300 dark:border-gray-600 px-4 py-8 text-center text-gray-500">
                  未找到符合條件的成分 No ingredients found
                </td>
              </tr>
            ) : (
              filteredData.map((item, idx) => (
                <tr
                  key={item.ingredient_name}
                  className={idx % 2 === 0 ? 'bg-white dark:bg-gray-800' : 'bg-gray-50 dark:bg-gray-750'}
                >
                  <td className="border border-gray-300 dark:border-gray-600 px-4 py-3 font-medium sticky left-0 bg-inherit z-10">
                    {item.ingredient_name}
                  </td>
                  {markets.map((market) => {
                    const marketStatus = item.markets[market]
                    const statusClass = statusColors[marketStatus.status] || 'bg-gray-100 text-gray-800'
                    const statusText = statusTranslations[marketStatus.status] || marketStatus.status

                    return (
                      <td
                        key={market}
                        className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-center"
                      >
                        <div className={`px-3 py-2 rounded text-sm font-medium border ${statusClass}`}>
                          {statusText}
                        </div>
                      </td>
                    )
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 圖例 */}
      <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">圖例 Legend:</p>
        <div className="flex flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-red-100 border border-red-300"></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">禁止 Banned</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-yellow-100 border border-yellow-300"></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">限用 Restricted</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-blue-100 border border-blue-300"></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">監測 Monitored</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-green-100 border border-green-300"></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">允許 Allowed</span>
          </div>
        </div>
      </div>
    </div>
  )
}
