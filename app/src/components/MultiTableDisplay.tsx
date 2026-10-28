'use client'

import { useState, useEffect } from 'react'
import { fetchParsedTables, type ParsedTablesResponse } from '@/lib/dataFetcher'

interface TableData {
  jurisdiction: string
  table_type: string
  version: string
  generated_at: string
  total_records: number
  records: any[]
  displayName: {
    en: string
    zh: string
  }
}

interface MultiTableDisplayProps {
  jurisdiction: string
  version?: string
  onVersionChange?: (version: string) => void
}

const TABLE_ORDER = [
  'prohibited',
  'restricted',
  'preservatives',
  'uv_filters',
  'colorants',
  'whitelist'
]

// 表格颜色主题
const TABLE_COLORS: Record<string, string> = {
  prohibited: 'red',
  restricted: 'yellow',
  preservatives: 'green',
  uv_filters: 'blue',
  colorants: 'purple',
  whitelist: 'gray'
}

export default function MultiTableDisplay({
  jurisdiction,
  version = 'latest',
  onVersionChange
}: MultiTableDisplayProps) {
  const [data, setData] = useState<ParsedTablesResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [activeTable, setActiveTable] = useState<string>('prohibited')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [selectedVersion, setSelectedVersion] = useState(version)

  useEffect(() => {
    loadData()
  }, [jurisdiction, selectedVersion])

  const loadData = async () => {
    setLoading(true)
    setError('')

    try {
      const result = await fetchParsedTables(jurisdiction, selectedVersion)
      setData(result)

      // Set active table to first available table
      if (result.tables && Object.keys(result.tables).length > 0) {
        const availableTables = Object.keys(result.tables)
        if (!availableTables.includes(activeTable)) {
          setActiveTable(availableTables[0])
        }
      }
    } catch (err) {
      console.error('Error loading parsed tables:', err)
      const errorMsg = err instanceof Error ? err.message : 'Failed to load data'
      setError(`${jurisdiction} - ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const handleVersionChange = (newVersion: string) => {
    setSelectedVersion(newVersion)
    onVersionChange?.(newVersion)
  }

  const getColorClasses = (color: string, variant: 'bg' | 'border' | 'text' = 'bg') => {
    const colors = {
      red: { bg: 'bg-red-100 dark:bg-red-900/20', border: 'border-red-300 dark:border-red-700', text: 'text-red-700 dark:text-red-400' },
      yellow: { bg: 'bg-yellow-100 dark:bg-yellow-900/20', border: 'border-yellow-300 dark:border-yellow-700', text: 'text-yellow-700 dark:text-yellow-400' },
      green: { bg: 'bg-green-100 dark:bg-green-900/20', border: 'border-green-300 dark:border-green-700', text: 'text-green-700 dark:text-green-400' },
      blue: { bg: 'bg-blue-100 dark:bg-blue-900/20', border: 'border-blue-300 dark:border-blue-700', text: 'text-blue-700 dark:text-blue-400' },
      purple: { bg: 'bg-purple-100 dark:bg-purple-900/20', border: 'border-purple-300 dark:border-purple-700', text: 'text-purple-700 dark:text-purple-400' },
      gray: { bg: 'bg-gray-100 dark:bg-gray-900/20', border: 'border-gray-300 dark:border-gray-700', text: 'text-gray-700 dark:text-gray-400' }
    }
    return colors[color as keyof typeof colors]?.[variant] || colors.gray[variant]
  }

  const filterRecords = (records: any[]) => {
    if (!searchQuery.trim()) return records

    const query = searchQuery.toLowerCase()
    return records.filter(record => {
      return (
        record.INCI_Name?.toLowerCase().includes(query) ||
        record.CAS_No?.toLowerCase().includes(query) ||
        record.CN_Name?.toLowerCase().includes(query) ||
        record.EU_Name?.toLowerCase().includes(query)
      )
    })
  }

  const renderRecordValue = (value: any): string => {
    if (value === null || value === undefined) return '-'
    if (typeof value === 'boolean') return value ? '✓' : '✗'
    if (typeof value === 'object') return JSON.stringify(value)
    return String(value)
  }

  const getKeyFields = (tableType: string) => {
    const commonFields = ['INCI_Name', 'CAS_No', 'CN_Name', 'EU_Name', 'Status']

    switch (tableType) {
      case 'prohibited':
        return [...commonFields, 'Rationale', 'Legal_Basis']
      case 'restricted':
        return [...commonFields, 'Max_Conc_Percent', 'Product_Type', 'Conditions', 'Warnings']
      case 'preservatives':
      case 'uv_filters':
      case 'colorants':
        return [...commonFields, 'Max_Conc_Percent', 'Product_Type', 'Conditions', 'Colour_Index_Number']
      case 'whitelist':
        return [...commonFields, 'Function', 'Origin', 'Category']
      default:
        return commonFields
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">載入中... Loading...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
        <div className="flex items-start space-x-3">
          <span className="text-2xl">❌</span>
          <div className="flex-1">
            <p className="text-red-800 dark:text-red-300 font-medium mb-2">載入失敗 Failed to Load Data</p>
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            <button
              onClick={loadData}
              className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition-colors"
            >
              🔄 重試 Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!data || !data.tables || Object.keys(data.tables).length === 0) {
    return (
      <div className="p-8 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-center">
        <div className="text-6xl mb-4">📭</div>
        <p className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">
          暫無解析數據
        </p>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          No parsed data available for {jurisdiction} (version: {selectedVersion})
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-500 mt-4">
          請先上傳並解析 {jurisdiction} 辖区的法規文件
        </p>
      </div>
    )
  }

  const currentTableData = data.tables[activeTable]
  const filteredRecords = currentTableData ? filterRecords(currentTableData.records) : []
  const keyFields = getKeyFields(activeTable)

  return (
    <div className="space-y-4">
      {/* Header with Statistics */}
      <div className="bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20 rounded-lg p-6 border border-primary-200 dark:border-primary-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
              {jurisdiction} 法規解析結果 Parsed Regulations
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              版本 Version: {data.version}
            </p>
          </div>

          {/* Version Selector */}
          {data.available_versions.length > 1 && (
            <div>
              <select
                value={selectedVersion}
                onChange={(e) => handleVersionChange(e.target.value)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-primary-500"
              >
                {data.available_versions.map(v => (
                  <option key={v} value={v}>
                    {v === 'latest' ? 'Latest' : v}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Statistics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {TABLE_ORDER.filter(t => data.statistics.by_table[t]).map(tableType => {
            const stat = data.statistics.by_table[tableType]
            const color = TABLE_COLORS[tableType]
            return (
              <div
                key={tableType}
                className={`${getColorClasses(color, 'bg')} ${getColorClasses(color, 'border')} border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
                  activeTable === tableType ? 'ring-2 ring-primary-500' : ''
                }`}
                onClick={() => setActiveTable(tableType)}
              >
                <p className={`text-xs font-medium ${getColorClasses(color, 'text')} mb-1`}>
                  {stat.name.zh}
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stat.count}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  {stat.name.en}
                </p>
              </div>
            )
          })}
        </div>

        {/* Total */}
        <div className="mt-4 pt-4 border-t border-primary-200 dark:border-primary-700">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              總記錄數 Total Records:
            </span>
            <span className="text-xl font-bold text-primary-700 dark:text-primary-400">
              {data.statistics.total_records}
            </span>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="flex items-center space-x-2">
        <input
          type="text"
          placeholder="搜索 INCI Name, CAS No, CN Name... Search"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
          >
            清除 Clear
          </button>
        )}
      </div>

      {/* Table Display */}
      {currentTableData && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden border border-gray-200 dark:border-gray-700">
          {/* Table Header */}
          <div className={`${getColorClasses(TABLE_COLORS[activeTable], 'bg')} ${getColorClasses(TABLE_COLORS[activeTable], 'border')} border-b px-6 py-4`}>
            <h4 className="text-lg font-bold text-gray-900 dark:text-white">
              {currentTableData.displayName.zh} / {currentTableData.displayName.en}
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {filteredRecords.length} / {currentTableData.total_records} 條記錄
            </p>
          </div>

          {/* Table Content */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    #
                  </th>
                  {keyFields.map(field => (
                    <th
                      key={field}
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                    >
                      {field.replace(/_/g, ' ')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {filteredRecords.length > 0 ? (
                  filteredRecords.map((record, index) => (
                    <tr
                      key={index}
                      className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                        {index + 1}
                      </td>
                      {keyFields.map(field => (
                        <td
                          key={field}
                          className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100"
                        >
                          {renderRecordValue(record[field])}
                        </td>
                      ))}
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan={keyFields.length + 1}
                      className="px-4 py-8 text-center text-gray-500 dark:text-gray-400"
                    >
                      {searchQuery ? '無搜索結果 No search results' : '暫無數據 No data'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
