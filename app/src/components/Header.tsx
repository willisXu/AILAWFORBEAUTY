'use client'

export default function Header() {
  return (
    <header className="bg-white dark:bg-gray-900 shadow-sm">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              跨國化妝品法規自動稽核系統
            </h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Cosmetics Regulation Compliance Audit System
            </p>
          </div>

          <div className="flex items-center space-x-4">
            {/* Market badges */}
            <div className="hidden md:flex space-x-2">
              {['EU', 'JP', 'CN', 'CA', 'ASEAN'].map((market) => (
                <span
                  key={market}
                  className="px-3 py-1 text-xs font-medium rounded-full bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200"
                >
                  {market}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Info banner */}
        <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <div className="flex items-start space-x-3">
            <svg
              className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5"
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
              <p className="font-medium">隱私保護 Privacy Protection</p>
              <p className="mt-1">
                所有成分比對均在您的瀏覽器本地端完成，不會上傳任何資料到伺服器。
                All ingredient checks are performed locally in your browser, no data is uploaded to servers.
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
