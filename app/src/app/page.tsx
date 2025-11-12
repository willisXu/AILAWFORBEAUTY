'use client'

import { useState } from 'react'
import Header from '@/components/Header'
import UploadSection from '@/components/UploadSection'
import ComplianceMatrix from '@/components/ComplianceMatrix'
import RegulationFileUpload from '@/components/RegulationFileUpload'
import CrossMarketComparison from '@/components/CrossMarketComparison'
import RegulationsBrowser from '@/components/RegulationsBrowser'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'ingredient' | 'regulation' | 'browser' | 'comparison'>('ingredient')
  const [complianceResults, setComplianceResults] = useState<any>(null)

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-900 dark:to-gray-800">
      <Header />

      <div className="container mx-auto px-4 py-8">
        {/* Tab Navigation */}
        <div className="flex flex-wrap space-x-2 md:space-x-4 mb-8 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setActiveTab('ingredient')}
            className={`px-4 md:px-6 py-3 font-medium transition-colors ${
              activeTab === 'ingredient'
                ? 'border-b-2 border-primary-600 text-primary-600'
                : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'
            }`}
          >
            成分比對 Ingredient Check
          </button>
          <button
            onClick={() => setActiveTab('regulation')}
            className={`px-4 md:px-6 py-3 font-medium transition-colors ${
              activeTab === 'regulation'
                ? 'border-b-2 border-primary-600 text-primary-600'
                : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'
            }`}
          >
            上傳法規 Upload Regulation
          </button>
          <button
            onClick={() => setActiveTab('browser')}
            className={`px-4 md:px-6 py-3 font-medium transition-colors ${
              activeTab === 'browser'
                ? 'border-b-2 border-primary-600 text-primary-600'
                : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'
            }`}
          >
            法規瀏覽 Regulations Browser
          </button>
          <button
            onClick={() => setActiveTab('comparison')}
            className={`px-4 md:px-6 py-3 font-medium transition-colors ${
              activeTab === 'comparison'
                ? 'border-b-2 border-primary-600 text-primary-600'
                : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'
            }`}
          >
            跨市場比較 Cross-Market
          </button>
        </div>

        {/* Content */}
        {activeTab === 'ingredient' ? (
          <div className="space-y-8">
            <UploadSection onResultsChange={setComplianceResults} />
            {complianceResults && <ComplianceMatrix results={complianceResults} />}
          </div>
        ) : activeTab === 'regulation' ? (
          <RegulationFileUpload />
        ) : activeTab === 'browser' ? (
          <RegulationsBrowser />
        ) : (
          <CrossMarketComparison />
        )}
      </div>

      {/* Footer */}
      <footer className="mt-16 py-8 border-t border-gray-200 dark:border-gray-700">
        <div className="container mx-auto px-4 text-center text-sm text-gray-600 dark:text-gray-400">
          <p>跨國化妝品法規自動稽核系統 v2.0</p>
          <p className="mt-2">
            所有比對在瀏覽器端完成，不上傳使用者檔案 | All processing is done in-browser, no data uploaded
          </p>
        </div>
      </footer>
    </main>
  )
}
