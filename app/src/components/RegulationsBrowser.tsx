'use client'

import { useState } from 'react'
import MultiTableDisplay from './MultiTableDisplay'

const JURISDICTIONS = [
  { code: 'EU', name: 'European Union (欧盟)' },
  { code: 'ASEAN', name: 'ASEAN (东盟)' },
  { code: 'CN', name: 'China (中国)' },
  { code: 'JP', name: 'Japan (日本)' },
  { code: 'CA', name: 'Canada (加拿大)' },
]

export default function RegulationsBrowser() {
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<string>('EU')

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-200 dark:border-gray-700">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          法規解析數據瀏覽器 Regulations Data Browser
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          查看已解析的法規數據，支持多表架構（Prohibited, Restricted, Preservatives, UV Filters, Colorants, Whitelist）
        </p>
      </div>

      {/* Jurisdiction Selector */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-200 dark:border-gray-700">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          選擇法規辖區 Select Jurisdiction
        </label>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {JURISDICTIONS.map(j => (
            <button
              key={j.code}
              onClick={() => setSelectedJurisdiction(j.code)}
              className={`px-4 py-3 rounded-lg font-medium transition-all ${
                selectedJurisdiction === j.code
                  ? 'bg-primary-600 text-white shadow-lg ring-2 ring-primary-500'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              <div className="text-lg font-bold">{j.code}</div>
              <div className="text-xs mt-1">{j.name.split(' ')[0]}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Multi-Table Display */}
      <MultiTableDisplay jurisdiction={selectedJurisdiction} />
    </div>
  )
}
