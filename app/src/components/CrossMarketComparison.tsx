'use client'

import { useState, useEffect } from 'react'
import { fetchAllJurisdictions } from '@/lib/dataFetcher'

interface MarketRegulation {
  Status: string
  Table_Type: string
  Max_Conc_Percent?: number
  Product_Type?: string
  Conditions?: string
}

interface IngredientComparison {
  INCI_Name: string
  CAS_No?: string
  CN_Name?: string
  markets: {
    [jurisdiction: string]: MarketRegulation | null
  }
}

const JURISDICTIONS = [
  { code: 'EU', name: '欧盟', enName: 'EU' },
  { code: 'ASEAN', name: '东盟', enName: 'ASEAN' },
  { code: 'CN', name: '中国', enName: 'China' },
  { code: 'JP', name: '日本', enName: 'Japan' },
  { code: 'CA', name: '加拿大', enName: 'Canada' },
]

const TABLE_TYPES = [
  { key: 'all', name: '全部表格', enName: 'All Tables' },
  { key: 'prohibited', name: '禁用物质', enName: 'Prohibited' },
  { key: 'restricted', name: '限用物质', enName: 'Restricted' },
  { key: 'preservatives', name: '防腐剂', enName: 'Preservatives' },
  { key: 'uv_filters', name: '紫外线吸收剂', enName: 'UV Filters' },
  { key: 'colorants', name: '色料', enName: 'Colorants' },
  { key: 'whitelist', name: '一般白名单', enName: 'Whitelist' },
]

const STATUS_COLORS: Record<string, string> = {
  'PROHIBITED': 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-red-300 dark:border-red-700',
  'RESTRICTED': 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700',
  'ALLOWED': 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border-green-300 dark:border-green-700',
  'LISTED': 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 border-blue-300 dark:border-blue-700',
  'NOT_SPECIFIED': 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600',
}

const STATUS_LABELS: Record<string, string> = {
  'PROHIBITED': '禁用',
  'RESTRICTED': '限用',
  'ALLOWED': '允许',
  'LISTED': '收录',
  'NOT_SPECIFIED': '未规定',
}

export default function CrossMarketComparison() {
  const [allData, setAllData] = useState<Record<string, any>>({})
  const [comparisonData, setComparisonData] = useState<IngredientComparison[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedTableType, setSelectedTableType] = useState('all')

  useEffect(() => {
    loadAllJurisdictionsData()
  }, [])

  useEffect(() => {
    if (Object.keys(allData).length > 0) {
      generateComparisonData()
    }
  }, [allData, selectedTableType])

  const loadAllJurisdictionsData = async () => {
    setLoading(true)

    try {
      const jurisdictionCodes = JURISDICTIONS.map(j => j.code)
      const loadedData = await fetchAllJurisdictions(jurisdictionCodes)

      const successCount = Object.keys(loadedData).length
      const failCount = JURISDICTIONS.length - successCount

      console.log(`Data loading complete: ${successCount} success, ${failCount} failed`)
      console.log('Loaded jurisdictions:', Object.keys(loadedData).join(', '))

      setAllData(loadedData)
    } catch (error) {
      console.error('Error loading jurisdictions data:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateComparisonData = () => {
    const ingredientsMap = new Map<string, IngredientComparison>()

    // 遍历所有辖区和表格
    JURISDICTIONS.forEach(jurisdiction => {
      const jurisdictionTables = allData[jurisdiction.code]
      if (!jurisdictionTables) return

      Object.entries(jurisdictionTables).forEach(([tableType, tableData]: [string, any]) => {
        // 如果选择了特定表格类型，只处理该类型
        if (selectedTableType !== 'all' && tableType !== selectedTableType) return

        const records = tableData.records || []

        records.forEach((record: any) => {
          const key = record.INCI_Name || record.CAS_No || ''
          if (!key) return

          if (!ingredientsMap.has(key)) {
            ingredientsMap.set(key, {
              INCI_Name: record.INCI_Name || '',
              CAS_No: record.CAS_No || '',
              CN_Name: record.CN_Name || '',
              markets: {}
            })
          }

          const ingredient = ingredientsMap.get(key)!

          // 如果该辖区还没有记录，或者当前状态优先级更高，则更新
          if (!ingredient.markets[jurisdiction.code] || shouldUpdateStatus(
            ingredient.markets[jurisdiction.code]!.Status,
            record.Status
          )) {
            ingredient.markets[jurisdiction.code] = {
              Status: record.Status,
              Table_Type: tableType,
              Max_Conc_Percent: record.Max_Conc_Percent,
              Product_Type: record.Product_Type,
              Conditions: record.Conditions
            }
          }
        })
      })
    })

    // 填充未规定的辖区
    ingredientsMap.forEach(ingredient => {
      JURISDICTIONS.forEach(jurisdiction => {
        if (!ingredient.markets[jurisdiction.code]) {
          ingredient.markets[jurisdiction.code] = {
            Status: 'NOT_SPECIFIED',
            Table_Type: 'none'
          }
        }
      })
    })

    setComparisonData(Array.from(ingredientsMap.values()))
  }

  const shouldUpdateStatus = (currentStatus: string, newStatus: string): boolean => {
    const priority: Record<string, number> = {
      'PROHIBITED': 1,
      'RESTRICTED': 2,
      'ALLOWED': 3,
      'LISTED': 4,
      'NOT_SPECIFIED': 5
    }
    return (priority[newStatus] || 5) < (priority[currentStatus] || 5)
  }

  const filteredData = comparisonData.filter(item => {
    const searchLower = searchTerm.toLowerCase()
    return (
      item.INCI_Name?.toLowerCase().includes(searchLower) ||
      item.CAS_No?.toLowerCase().includes(searchLower) ||
      item.CN_Name?.toLowerCase().includes(searchLower)
    )
  })

  const exportToCSV = () => {
    let csv = 'INCI Name,CAS No,CN Name,' + JURISDICTIONS.map(j => j.name).join(',') + '\n'

    filteredData.forEach(item => {
      const row = [
        item.INCI_Name || '',
        item.CAS_No || '',
        item.CN_Name || '',
        ...JURISDICTIONS.map(j => {
          const market = item.markets[j.code]
          if (!market) return '未规定'
          const status = STATUS_LABELS[market.Status] || market.Status
          const conc = market.Max_Conc_Percent ? ` (${market.Max_Conc_Percent}%)` : ''
          return `${status}${conc}`
        })
      ]
      csv += row.map(cell => `"${cell}"`).join(',') + '\n'
    })

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `cross-market-comparison-${selectedTableType}-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
  }

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">載入中... Loading cross-market data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              跨市場成分比較 Cross-Market Ingredient Comparison
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              基於V2多表架構的跨辖区法规比较
            </p>
          </div>
          <button
            onClick={exportToCSV}
            disabled={filteredData.length === 0}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg transition-colors flex items-center space-x-2"
          >
            <span>📥</span>
            <span>匯出 CSV</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              搜尋成分 Search Ingredient
            </label>
            <input
              type="text"
              placeholder="INCI Name, CAS No, CN Name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
            />
          </div>

          {/* Table Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              表格類型 Table Type
            </label>
            <select
              value={selectedTableType}
              onChange={(e) => setSelectedTableType(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
            >
              {TABLE_TYPES.map(type => (
                <option key={type.key} value={type.key}>
                  {type.name} / {type.enName}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Statistics */}
        <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            顯示 <span className="font-bold text-primary-600 dark:text-primary-400">{filteredData.length}</span> 個成分
            （共 <span className="font-semibold">{comparisonData.length}</span> 個）
          </p>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead className="bg-gray-100 dark:bg-gray-900">
              <tr>
                <th className="border border-gray-300 dark:border-gray-700 px-4 py-3 text-left font-semibold text-gray-900 dark:text-white sticky left-0 bg-gray-100 dark:bg-gray-900 z-20 min-w-[200px]">
                  <div>成分名称</div>
                  <div className="text-xs font-normal text-gray-600 dark:text-gray-400">INCI Name</div>
                </th>
                <th className="border border-gray-300 dark:border-gray-700 px-4 py-3 text-left font-semibold text-gray-900 dark:text-white sticky left-[200px] bg-gray-100 dark:bg-gray-900 z-20 min-w-[120px]">
                  <div>CAS No</div>
                </th>
                {JURISDICTIONS.map(jurisdiction => (
                  <th
                    key={jurisdiction.code}
                    className="border border-gray-300 dark:border-gray-700 px-4 py-3 text-center font-semibold text-gray-900 dark:text-white min-w-[140px]"
                  >
                    <div>{jurisdiction.name}</div>
                    <div className="text-xs font-normal text-gray-600 dark:text-gray-400">{jurisdiction.code}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredData.length === 0 ? (
                <tr>
                  <td
                    colSpan={JURISDICTIONS.length + 2}
                    className="border border-gray-300 dark:border-gray-700 px-4 py-12 text-center text-gray-500 dark:text-gray-400"
                  >
                    未找到符合條件的成分 No ingredients found
                  </td>
                </tr>
              ) : (
                filteredData.map((item, idx) => (
                  <tr
                    key={`${item.INCI_Name}-${item.CAS_No}`}
                    className={idx % 2 === 0 ? 'bg-white dark:bg-gray-800' : 'bg-gray-50 dark:bg-gray-750'}
                  >
                    <td className="border border-gray-300 dark:border-gray-700 px-4 py-3 font-medium text-gray-900 dark:text-white sticky left-0 bg-inherit z-10">
                      <div>{item.INCI_Name}</div>
                      {item.CN_Name && (
                        <div className="text-xs text-gray-600 dark:text-gray-400">{item.CN_Name}</div>
                      )}
                    </td>
                    <td className="border border-gray-300 dark:border-gray-700 px-4 py-3 text-sm text-gray-700 dark:text-gray-300 sticky left-[200px] bg-inherit z-10">
                      {item.CAS_No || '-'}
                    </td>
                    {JURISDICTIONS.map(jurisdiction => {
                      const market = item.markets[jurisdiction.code]
                      if (!market) {
                        return (
                          <td
                            key={jurisdiction.code}
                            className="border border-gray-300 dark:border-gray-700 px-2 py-2 text-center"
                          >
                            <div className={`px-2 py-1 rounded text-xs border ${STATUS_COLORS['NOT_SPECIFIED']}`}>
                              未规定
                            </div>
                          </td>
                        )
                      }

                      const statusClass = STATUS_COLORS[market.Status] || STATUS_COLORS['NOT_SPECIFIED']
                      const statusText = STATUS_LABELS[market.Status] || market.Status

                      return (
                        <td
                          key={jurisdiction.code}
                          className="border border-gray-300 dark:border-gray-700 px-2 py-2"
                        >
                          <div className={`px-2 py-1 rounded text-xs border ${statusClass}`}>
                            <div className="font-medium">{statusText}</div>
                            {market.Max_Conc_Percent !== undefined && market.Max_Conc_Percent !== null && (
                              <div className="text-xs mt-1">≤ {market.Max_Conc_Percent}%</div>
                            )}
                            {market.Product_Type && market.Product_Type !== 'ALL' && (
                              <div className="text-xs mt-1">{market.Product_Type}</div>
                            )}
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
      </div>

      {/* Legend */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">圖例 Legend:</p>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {Object.entries(STATUS_LABELS).map(([status, label]) => (
            <div key={status} className="flex items-center gap-2">
              <div className={`w-6 h-6 rounded border ${STATUS_COLORS[status]}`}></div>
              <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
