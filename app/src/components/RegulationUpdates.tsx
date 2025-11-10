'use client'

import { useState, useEffect } from 'react'

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
    alert(
      '手動更新功能:\n\n' +
      '請前往 GitHub Actions 頁面手動觸發 "Fetch Regulations" 工作流程\n\n' +
      'Manual Update:\n' +
      'Please go to GitHub Actions page and manually trigger the "Fetch Regulations" workflow'
    )

    // Open GitHub Actions page
    const repoUrl = 'https://github.com/willisXu/AILAWFORBEAUTY'
    window.open(`${repoUrl}/actions`, '_blank')
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
      {/* Manual Update Button */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between">
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
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
          >
            🔄 手動更新 Manual Update
          </button>
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
    </div>
  )
}
