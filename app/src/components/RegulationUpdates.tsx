'use client'

import { useState, useEffect } from 'react'
import CrossMarketComparison from './CrossMarketComparison'

interface DiffSummary {
  jurisdiction: string
  from_version: string
  to_version: string
  total_changes: number
  added: number
  removed: number
  modified: number
}

export default function RegulationUpdates() {
  const [diffs, setDiffs] = useState<DiffSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<string | null>(null)
  const [activeView, setActiveView] = useState<'updates' | 'comparison'>('updates')

  useEffect(() => {
    loadDiffs()
  }, [])

  const loadDiffs = async () => {
    try {
      const basePath = process.env.NODE_ENV === 'production' ? '/AILAWFORBEAUTY' : ''
      const jurisdictions = ['EU', 'JP', 'CN', 'CA', 'ASEAN']
      const allDiffs: DiffSummary[] = []

      for (const jurisdiction of jurisdictions) {
        try {
          // Try to load latest diff
          const response = await fetch(`${basePath}/data/diff/${jurisdiction}/`, {
            method: 'GET',
          })

          if (response.ok) {
            // Parse directory listing or load specific file
            // For simplicity, we'll just indicate updates are available
            allDiffs.push({
              jurisdiction,
              from_version: 'N/A',
              to_version: 'Latest',
              total_changes: 0,
              added: 0,
              removed: 0,
              modified: 0,
            })
          }
        } catch (error) {
          console.debug(`No diffs for ${jurisdiction}`)
        }
      }

      setDiffs(allDiffs)
    } catch (error) {
      console.error('Error loading diffs:', error)
    } finally {
      setLoading(false)
    }
  }

  const triggerManualUpdate = () => {
    // Directly open the specific workflow dispatch page
    const repoUrl = 'https://github.com/willisXu/AILAWFORBEAUTY'
    const workflowFile = 'fetch-regulations.yml'

    // Open the workflow_dispatch page directly
    window.open(`${repoUrl}/actions/workflows/${workflowFile}`, '_blank')
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
    <div className="space-y-6">
      {/* Header with Tabs */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              法規更新中心 Regulation Update Center
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              自動每週更新 | 也可手動觸發 Automatic weekly updates | Manual trigger available
            </p>
          </div>

          <button
            onClick={triggerManualUpdate}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-all font-medium shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 flex items-center space-x-2"
            title="點擊後將跳轉到 GitHub，點擊 'Run workflow' 按鈕即可觸發更新"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>🚀 立即更新 Update Now</span>
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-4 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setActiveView('updates')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeView === 'updates'
                ? 'border-b-2 border-primary-600 text-primary-600'
                : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'
            }`}
          >
            法規變更 Updates
          </button>
          <button
            onClick={() => setActiveView('comparison')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeView === 'comparison'
                ? 'border-b-2 border-primary-600 text-primary-600'
                : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'
            }`}
          >
            跨市場比較 Cross-Market Comparison
          </button>
        </div>
      </div>

      {/* Content based on active view */}
      {activeView === 'comparison' ? (
        <CrossMarketComparison />
      ) : (
        <>

      {/* Quick Action Guide */}
      <div className="bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-lg p-6 border-2 border-primary-200 dark:border-primary-800">
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-primary-600 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
              ⚡ 快速更新指南 Quick Update Guide
            </h3>
            <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
              <div className="flex items-center space-x-2">
                <span className="flex-shrink-0 w-6 h-6 bg-white dark:bg-gray-800 rounded-full flex items-center justify-center text-primary-600 font-bold">1</span>
                <span>點擊上方 <strong>「🚀 立即更新」</strong> 按鈕 | Click the <strong>"🚀 Update Now"</strong> button above</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="flex-shrink-0 w-6 h-6 bg-white dark:bg-gray-800 rounded-full flex items-center justify-center text-primary-600 font-bold">2</span>
                <span>在 GitHub 頁面點擊 <strong className="text-green-600">"Run workflow"</strong> 綠色按鈕 | Click the green <strong className="text-green-600">"Run workflow"</strong> button on GitHub</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="flex-shrink-0 w-6 h-6 bg-white dark:bg-gray-800 rounded-full flex items-center justify-center text-primary-600 font-bold">3</span>
                <span>等待 2-3 分鐘，數據自動更新完成！| Wait 2-3 minutes for automatic data update!</span>
              </div>
            </div>
            <div className="mt-3 text-xs text-gray-600 dark:text-gray-400">
              💡 提示：首次更新可能需要登入 GitHub 帳號 | Tip: First-time update may require GitHub login
            </div>
          </div>
        </div>
      </div>

      {/* Update Schedule */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
          更新排程 Update Schedule
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div className="flex items-center space-x-3">
              <svg
                className="w-6 h-6 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div>
                <div className="font-semibold text-gray-900 dark:text-white">自動更新 Automatic</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  每週一 03:00 (台北時間) Every Monday 03:00 (Taipei Time)
                </div>
              </div>
            </div>
          </div>

          <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <div className="flex items-center space-x-3">
              <svg
                className="w-6 h-6 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div>
                <div className="font-semibold text-gray-900 dark:text-white">涵蓋市場 Markets Covered</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  EU, JP, CN, CA, ASEAN
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Changes */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
          近期變更 Recent Changes
        </h3>

        {diffs.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <p>暫無法規變更記錄 No regulation changes recorded yet</p>
            <p className="text-sm mt-2">
              首次抓取後將在此顯示變更歷史 Change history will appear here after first fetch
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {diffs.map((diff) => (
              <div
                key={diff.jurisdiction}
                className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-lg text-gray-900 dark:text-white">
                      {diff.jurisdiction}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      版本 Version: {diff.from_version} → {diff.to_version}
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-2xl font-bold text-primary-600">
                      {diff.total_changes}
                    </div>
                    <div className="text-xs text-gray-500">變更 changes</div>
                  </div>
                </div>

                {diff.total_changes > 0 && (
                  <div className="mt-3 flex space-x-4 text-sm">
                    <span className="text-green-600">
                      ➕ {diff.added} 新增 added
                    </span>
                    <span className="text-red-600">
                      ➖ {diff.removed} 移除 removed
                    </span>
                    <span className="text-yellow-600">
                      ✏️ {diff.modified} 修改 modified
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Info Box */}
      <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <svg
            className="w-5 h-5 text-yellow-600 mt-0.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div className="text-sm text-yellow-800 dark:text-yellow-200">
            <p className="font-medium">注意 Note</p>
            <p className="mt-1">
              法規資料來源於各國官方公開資訊，僅供參考。實際應用請諮詢專業法規顧問。
              Regulation data is sourced from official public information for reference only.
              Please consult professional regulatory advisors for actual applications.
            </p>
          </div>
        </div>
      </div>
      </>
      )}
    </div>
  )
}
