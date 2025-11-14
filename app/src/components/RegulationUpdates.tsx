'use client'

import { useState, useEffect } from 'react'
import CrossMarketComparison from './CrossMarketComparison'
import RegulationFileUpload from './RegulationFileUpload'
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

interface RegulationData {
  jurisdiction: string
  version: string
  published_at: string
  fetched_at: string
  source: string
  regulation: string
  statistics: {
    total_ingredients: number
    total_clauses: number
    banned: number
    restricted: number
    allowed: number
  }
  clauses?: any[]
}

export default function RegulationUpdates() {
  const [diffs, setDiffs] = useState<DiffSummary[]>([])
  const [regulations, setRegulations] = useState<RegulationData[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<string | null>(null)
  const [expandedJurisdiction, setExpandedJurisdiction] = useState<string | null>(null)
  const [activeView, setActiveView] = useState<'regulations-list' | 'comparison' | 'upload'>('regulations-list')
  const [triggering, setTriggering] = useState(false)
  const [triggerStatus, setTriggerStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [lastUpdate, setLastUpdate] = useState<string | null>(null)
  const [waitingForUpdate, setWaitingForUpdate] = useState(false)

  useEffect(() => {
    loadDiffs()
    loadRegulations()
  }, [])

  // Helper function to get category label
  const getCategoryLabel = (category: string) => {
    const labels: { [key: string]: string } = {
      'banned': '禁用 Banned',
      'prohibited': '禁用 Prohibited',
      'restricted': '限用 Restricted',
      'colorant': '著色劑 Colorant',
      'preservative': '防腐劑 Preservative',
      'uv_filter': '防曬劑 UV Filter',
      'allowed': '允許 Allowed'
    }
    return labels[category] || category
  }

  // Helper function to get category color
  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      'banned': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
      'prohibited': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
      'restricted': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      'colorant': 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
      'preservative': 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400',
      'uv_filter': 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
      'allowed': 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
    }
    return colors[category] || 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
  }

  // Helper function to format max percentage
  const formatMaxPct = (conditions: any) => {
    if (!conditions) return '未規定 Not specified'
    if (typeof conditions === 'string') return conditions || '未規定 Not specified'
    if (typeof conditions === 'object' && conditions.max_pct !== null && conditions.max_pct !== undefined) {
      return `≤ ${conditions.max_pct}%`
    }
    return '未規定 Not specified'
  }

  // Helper function to get additional conditions
  const getAdditionalConditions = (clause: any) => {
    const conditions = clause.conditions
    if (!conditions) return '未規定 Not specified'

    if (typeof conditions === 'string') {
      return conditions || '未規定 Not specified'
    }

    if (typeof conditions === 'object') {
      const parts = []
      if (conditions.specific_conditions) {
        parts.push(conditions.specific_conditions)
      }
      if (conditions.product_type && Array.isArray(conditions.product_type) && conditions.product_type.length > 0) {
        parts.push(`產品類型 Product type: ${conditions.product_type.join(', ')}`)
      }
      if (clause.warnings) {
        parts.push(`⚠️ ${clause.warnings}`)
      }
      if (clause.notes) {
        parts.push(clause.notes)
      }
      return parts.length > 0 ? parts.join(' | ') : '未規定 Not specified'
    }

    return '未規定 Not specified'
  }

  const loadRegulations = async () => {
    try {
      const basePath = process.env.NODE_ENV === 'production' ? '/AILAWFORBEAUTY' : ''
      const jurisdictions = ['EU', 'JP', 'CN', 'CA', 'ASEAN']
      const allRegulations: RegulationData[] = []

      for (const jurisdiction of jurisdictions) {
        try {
          const response = await fetch(`${basePath}/data/rules/${jurisdiction}/latest.json`, {
            cache: 'no-cache',
          })

          if (response.ok) {
            const data = await response.json()
            allRegulations.push({
              jurisdiction: data.jurisdiction || jurisdiction,
              version: data.version || 'N/A',
              published_at: data.published_at || 'N/A',
              fetched_at: data.fetched_at || 'N/A',
              source: data.source || 'N/A',
              regulation: data.regulation || 'N/A',
              statistics: data.statistics || {
                total_ingredients: 0,
                total_clauses: 0,
                banned: 0,
                restricted: 0,
                allowed: 0
              },
              clauses: data.clauses || []
            })
          }
        } catch (error) {
          console.debug(`Failed to load regulations for ${jurisdiction}:`, error)
        }
      }

      setRegulations(allRegulations)
    } catch (error) {
      console.error('Error loading regulations:', error)
    }
  }

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
            onClick={() => setActiveView('regulations-list')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeView === 'regulations-list'
                ? 'border-b-2 border-primary-600 text-primary-600'
                : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'
            }`}
          >
            各國法規清單 Regulations List
          </button>
          <button
            onClick={() => setActiveView('upload')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeView === 'upload'
                ? 'border-b-2 border-primary-600 text-primary-600'
                : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'
            }`}
          >
            上傳文件 Upload File
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
      ) : activeView === 'upload' ? (
        <RegulationFileUpload
          onUploadComplete={(result) => {
            console.log('Upload complete:', result)
            // Optionally reload regulations after upload
            setTimeout(() => {
              loadDiffs()
              loadRegulations()
            }, 3000)
          }}
        />
      ) : (
        <>
      {/* Regulations List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          各國法規清單 Regulations by Jurisdiction
        </h3>

        {regulations.length === 0 ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="mt-4 text-lg">暫無法規數據 No regulation data available</p>
            <p className="text-sm mt-2">
              請點擊上方「🚀 立即更新」按鈕來抓取最新法規數據
              <br />
              Please click "🚀 Update Now" button above to fetch latest regulation data
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {regulations.map((reg) => (
              <div key={reg.jurisdiction} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden bg-white dark:bg-gray-800">
                {/* Regulation Card Header */}
                <div className="p-6 bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Jurisdiction Header */}
                      <div className="flex items-center space-x-3 mb-3">
                        <h4 className="text-2xl font-bold text-primary-600 dark:text-primary-400">
                          {reg.jurisdiction}
                        </h4>
                        <div className="text-xs px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded">
                          v{reg.version}
                        </div>
                      </div>

                      {/* Regulation Name */}
                      <div className="mb-4">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {reg.regulation}
                        </p>
                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                          {reg.source}
                        </p>
                      </div>

                      {/* Statistics */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                          <div className="text-2xl font-bold text-gray-900 dark:text-white">{reg.statistics.total_clauses}</div>
                          <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">總條款 Total</div>
                        </div>
                        <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                          <div className="text-2xl font-bold text-red-600 dark:text-red-400">{reg.statistics.banned}</div>
                          <div className="text-xs text-red-600 dark:text-red-400 mt-1">禁用 Banned</div>
                        </div>
                        <div className="text-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                          <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{reg.statistics.restricted}</div>
                          <div className="text-xs text-yellow-600 dark:text-yellow-400 mt-1">限用 Restricted</div>
                        </div>
                        <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                          <div className="text-2xl font-bold text-green-600 dark:text-green-400">{reg.statistics.allowed}</div>
                          <div className="text-xs text-green-600 dark:text-green-400 mt-1">允許 Allowed</div>
                        </div>
                      </div>

                      {/* Dates */}
                      <div className="mt-4 flex flex-wrap gap-4 text-xs text-gray-500 dark:text-gray-400">
                        <div className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          <span>發布 Published: {reg.published_at}</span>
                        </div>
                        <div className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          <span>更新 Fetched: {new Date(reg.fetched_at).toLocaleDateString('zh-TW')}</span>
                        </div>
                      </div>
                    </div>

                    {/* Expand Button */}
                    <button
                      onClick={() => setExpandedJurisdiction(expandedJurisdiction === reg.jurisdiction ? null : reg.jurisdiction)}
                      className="ml-4 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors flex items-center space-x-2"
                    >
                      <span>{expandedJurisdiction === reg.jurisdiction ? '收起' : '查看詳情'}</span>
                      <svg
                        className={`w-5 h-5 transition-transform ${expandedJurisdiction === reg.jurisdiction ? 'rotate-180' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* Detailed Table - Expandable */}
                {expandedJurisdiction === reg.jurisdiction && reg.clauses && reg.clauses.length > 0 && (
                  <div className="p-6 bg-gray-50 dark:bg-gray-900/50">
                    <h5 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                      法規條款詳情 Regulation Details
                    </h5>
                    <div className="overflow-x-auto">
                      <table className="w-full border-collapse">
                        <thead>
                          <tr className="bg-gray-100 dark:bg-gray-800">
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 border-b border-gray-300 dark:border-gray-600">
                              成分名稱<br/>Ingredient Name
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 border-b border-gray-300 dark:border-gray-600">
                              CAS號<br/>CAS No.
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 border-b border-gray-300 dark:border-gray-600">
                              類別<br/>Category
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 border-b border-gray-300 dark:border-gray-600">
                              限用百分比<br/>Max %
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 border-b border-gray-300 dark:border-gray-600">
                              額外說明<br/>Additional Info
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 border-b border-gray-300 dark:border-gray-600">
                              來源<br/>Source
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {reg.clauses.map((clause, index) => (
                            <tr
                              key={clause.id || index}
                              className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800/50"
                            >
                              <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                                <div className="font-medium">{clause.ingredient_ref || clause.inci || clause.chemical_name || '未知'}</div>
                                {clause.inci && clause.ingredient_ref !== clause.inci && (
                                  <div className="text-xs text-gray-500 dark:text-gray-400">INCI: {clause.inci}</div>
                                )}
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                                {clause.cas || '未規定'}
                              </td>
                              <td className="px-4 py-3">
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(clause.category)}`}>
                                  {getCategoryLabel(clause.category)}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100 font-medium">
                                {formatMaxPct(clause.conditions)}
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 max-w-md">
                                <div className="line-clamp-2" title={getAdditionalConditions(clause)}>
                                  {getAdditionalConditions(clause)}
                                </div>
                              </td>
                              <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">
                                {clause.source_ref || '未規定'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
                      共 {reg.clauses.length} 條法規條款 | Total {reg.clauses.length} regulation clauses
                    </div>
                  </div>
                )}

                {/* Empty State for Clauses */}
                {expandedJurisdiction === reg.jurisdiction && (!reg.clauses || reg.clauses.length === 0) && (
                  <div className="p-6 bg-gray-50 dark:bg-gray-900/50 text-center">
                    <p className="text-gray-500 dark:text-gray-400">
                      暫無詳細法規條款數據 No detailed regulation clauses available
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <svg
            className="w-5 h-5 text-blue-600 mt-0.5"
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
          <div className="text-sm text-blue-800 dark:text-blue-200">
            <p className="font-medium">提示 Tips</p>
            <p className="mt-1">
              點擊上方「🚀 立即更新」可手動觸發法規數據更新。系統每週一 03:00 (台北時間) 自動更新。
              <br />
              Click "🚀 Update Now" button above to manually trigger regulation data update. System auto-updates every Monday at 03:00 (Taipei Time).
            </p>
          </div>
        </div>
      </div>
      </>
      )}
    </div>
  )
}
