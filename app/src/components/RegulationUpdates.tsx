'use client'

import { useState, useEffect } from 'react'
import CrossMarketComparison from './CrossMarketComparison'
import { API_CONFIG, hasDirectTrigger } from '../config/api'

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
  const [triggering, setTriggering] = useState(false)
  const [triggerStatus, setTriggerStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [lastUpdate, setLastUpdate] = useState<string | null>(null)
  const [waitingForUpdate, setWaitingForUpdate] = useState(false)

  useEffect(() => {
    loadDiffs()
  }, [])

  const loadDiffs = async () => {
    try {
      const basePath = process.env.NODE_ENV === 'production' ? '/AILAWFORBEAUTY' : ''
      const jurisdictions = ['EU', 'JP', 'CN', 'CA', 'ASEAN']
      const allDiffs: DiffSummary[] = []
      let latestFetchTime: Date | null = null

      for (const jurisdiction of jurisdictions) {
        try {
          // Load latest.json to get fetch timestamp
          const rawResponse = await fetch(`${basePath}/data/raw/${jurisdiction}/latest.json`, {
            cache: 'no-cache',
          })

          if (rawResponse.ok) {
            const rawData = await rawResponse.json()
            if (rawData.fetched_at) {
              const fetchTime = new Date(rawData.fetched_at)
              if (!latestFetchTime || fetchTime > latestFetchTime) {
                latestFetchTime = fetchTime
              }
            }
          }

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

      // Update last fetch time
      if (latestFetchTime) {
        setLastUpdate(latestFetchTime.toISOString())
      }
    } catch (error) {
      console.error('Error loading diffs:', error)
    } finally {
      setLoading(false)
      setWaitingForUpdate(false)
    }
  }

  const triggerManualUpdate = async () => {
    setTriggering(true)
    setTriggerStatus('idle')

    try {
      // 優先使用配置的直接觸發端點
      let apiEndpoint = API_CONFIG.TRIGGER_ENDPOINT

      // 如果沒有配置，嘗試使用本地 serverless function
      if (!apiEndpoint) {
        const basePath = process.env.NODE_ENV === 'production' ? '/AILAWFORBEAUTY' : ''
        apiEndpoint = `${basePath}/api/trigger-update`
      }

      console.log('Attempting to trigger via:', apiEndpoint)

      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          timestamp: new Date().toISOString(),
          source: 'web_ui',
        }),
      })

      const data = await response.json()

      if (response.ok && data.success) {
        // 成功觸發！
        setTriggerStatus('success')
        setWaitingForUpdate(true)
        console.log('✅ Workflow triggered successfully!')

        // 提示用户等待
        alert(
          '✅ 更新已觸發！\n' +
          'Update triggered successfully!\n\n' +
          '爬蟲正在抓取最新法規數據...\n' +
          'Scraper is fetching latest regulation data...\n\n' +
          '預計需要 2-3 分鐘\n' +
          'Estimated time: 2-3 minutes\n\n' +
          '完成後頁面將自動刷新\n' +
          'Page will auto-refresh when complete'
        )

        // 2.5 分钟后自动刷新数据
        setTimeout(() => {
          console.log('🔄 Auto-refreshing data...')
          loadDiffs()
          setTriggerStatus('idle')
        }, 150000) // 150秒 = 2.5分钟

        // 5秒後重置按鈕狀態（但保持 waitingForUpdate）
        setTimeout(() => {
          setTriggerStatus('idle')
        }, 5000)
      } else {
        throw new Error(data.error || 'Trigger failed')
      }
    } catch (error) {
      // 如果沒有配置直接觸發端點，顯示設置提示
      if (!hasDirectTrigger()) {
        console.log('⚠️ Direct trigger not configured')
        setTriggerStatus('error')

        // 顯示配置提示
        alert(
          '⚠️ 直接觸發功能尚未配置\n' +
          'Direct trigger not configured yet\n\n' +
          '請按照 QUICK_SETUP.md 的說明配置 Cloudflare Worker\n' +
          'Please follow QUICK_SETUP.md to configure Cloudflare Worker\n\n' +
          '配置後即可實現一鍵觸發，無需跳轉！\n' +
          'After setup, you can trigger with one click, no redirect!'
        )
      } else {
        console.error('Trigger failed:', error)
        setTriggerStatus('error')

        // 仍然提供 GitHub 跳轉作為備選
        if (confirm('直接觸發失敗。是否跳轉到 GitHub 手動觸發？\nDirect trigger failed. Open GitHub for manual trigger?')) {
          window.open(API_CONFIG.GITHUB_WORKFLOW_URL, '_blank')
        }
      }

      setTimeout(() => {
        setTriggerStatus('idle')
      }, 3000)
    } finally {
      setTriggering(false)
    }
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
            {lastUpdate && (
              <div className="mt-2 flex items-center space-x-2 text-xs text-gray-600 dark:text-gray-400">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>最後更新 Last updated: {new Date(lastUpdate).toLocaleString('zh-TW', {
                  year: 'numeric',
                  month: '2-digit',
                  day: '2-digit',
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: false
                })}</span>
              </div>
            )}
            {waitingForUpdate && (
              <div className="mt-2 flex items-center space-x-2 text-xs text-blue-600 dark:text-blue-400 animate-pulse">
                <svg className="animate-spin w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>正在抓取最新數據，預計 2-3 分鐘... Fetching latest data, ~2-3 minutes...</span>
              </div>
            )}
            {!hasDirectTrigger() && (
              <div className="mt-2 flex items-center space-x-2 text-xs text-amber-600 dark:text-amber-400">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>需配置才能直接觸發 | Needs setup for direct trigger</span>
                <a href="/AILAWFORBEAUTY/QUICK_SETUP.md" target="_blank" className="underline hover:text-amber-700">查看設置</a>
              </div>
            )}
          </div>

          <button
            onClick={triggerManualUpdate}
            disabled={triggering}
            className={`px-6 py-3 rounded-lg transition-all font-medium shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 flex items-center space-x-2 ${
              triggering
                ? 'bg-gray-400 cursor-not-allowed'
                : triggerStatus === 'success'
                ? 'bg-green-600 hover:bg-green-700'
                : 'bg-primary-600 hover:bg-primary-700 text-white'
            }`}
            title={triggering ? '觸發中...' : '點擊直接觸發更新（如失敗會跳轉到 GitHub）'}
          >
            {triggering ? (
              <>
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>觸發中... Triggering...</span>
              </>
            ) : triggerStatus === 'success' ? (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>✅ 已觸發 Triggered!</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>🚀 立即更新 Update Now</span>
              </>
            )}
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
                <span>點擊 <strong>「🚀 立即更新」</strong> 按鈕，系統將嘗試自動觸發 | Click <strong>"🚀 Update Now"</strong> button for automatic trigger</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="flex-shrink-0 w-6 h-6 bg-white dark:bg-gray-800 rounded-full flex items-center justify-center text-primary-600 font-bold">2</span>
                <span>看到 <strong className="text-green-600">「✅ 已觸發」</strong> 表示成功！| <strong className="text-green-600">"✅ Triggered!"</strong> means success!</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="flex-shrink-0 w-6 h-6 bg-white dark:bg-gray-800 rounded-full flex items-center justify-center text-primary-600 font-bold">3</span>
                <span>等待 2-3 分鐘後刷新頁面查看新數據 | Refresh page after 2-3 minutes for new data</span>
              </div>
            </div>
            <div className="mt-3 p-3 bg-white dark:bg-gray-800 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                <p>💡 <strong>智能模式</strong> Smart Mode:</p>
                <p className="ml-4">• 首先嘗試直接觸發（無需跳轉）</p>
                <p className="ml-4">• 如果直接觸發不可用，會自動跳轉到 GitHub</p>
                <p className="ml-4">• First try direct trigger (no redirect)</p>
                <p className="ml-4">• Auto fallback to GitHub if needed</p>
              </div>
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
