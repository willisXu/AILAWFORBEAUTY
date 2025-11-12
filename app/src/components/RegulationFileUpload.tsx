'use client'

import { useState, useCallback } from 'react'

interface RegulationFileUploadProps {
  onUploadComplete?: (result: any) => void
}

const JURISDICTIONS = [
  { code: 'EU', name: 'European Union', annexes: ['II', 'III', 'IV', 'V', 'VI'] },
  { code: 'ASEAN', name: 'ASEAN', annexes: ['II', 'III', 'IV', 'V', 'VI'] },
  { code: 'CN', name: 'China', annexes: [] },
  { code: 'JP', name: 'Japan', annexes: [] },
  { code: 'CA', name: 'Canada', annexes: [] },
]

const FILE_TYPES = [
  { value: 'pdf', label: 'PDF Document' },
  { value: 'json', label: 'JSON Data' },
  { value: 'html', label: 'HTML Page' },
]

export default function RegulationFileUpload({ onUploadComplete }: RegulationFileUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [jurisdiction, setJurisdiction] = useState<string>('EU')
  const [fileType, setFileType] = useState<string>('pdf')
  const [annex, setAnnex] = useState<string>('')
  const [version, setVersion] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [uploadResult, setUploadResult] = useState<any>(null)
  const [error, setError] = useState<string>('')

  const selectedJurisdiction = JURISDICTIONS.find(j => j.code === jurisdiction)

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      setError('')
      setUploadResult(null)
    }
  }, [])

  const handleUpload = useCallback(async () => {
    if (!file) {
      setError('请选择要上传的文件 Please select a file to upload')
      return
    }

    if (!jurisdiction) {
      setError('请选择法规辖区 Please select a jurisdiction')
      return
    }

    setLoading(true)
    setError('')
    setUploadResult(null)

    try {
      // Create form data
      const formData = new FormData()
      formData.append('file', file)
      formData.append('jurisdiction', jurisdiction)
      formData.append('fileType', fileType)
      if (annex) formData.append('annex', annex)
      if (version) formData.append('version', version)

      // Upload to API
      const response = await fetch('/api/upload-regulation', {
        method: 'POST',
        body: formData,
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.error || result.message || 'Upload failed')
      }

      setUploadResult(result)
      onUploadComplete?.(result)

      // Reset form
      setFile(null)
      setAnnex('')
      setVersion('')

      // Reset file input
      const fileInput = document.getElementById('regulation-file-upload') as HTMLInputElement
      if (fileInput) fileInput.value = ''

    } catch (err) {
      console.error('Upload error:', err)
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setLoading(false)
    }
  }, [file, jurisdiction, fileType, annex, version, onUploadComplete])

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
        上傳法規文件 Upload Regulation File
      </h2>

      <div className="space-y-4 mb-6">
        {/* Jurisdiction Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            法規辖區 Jurisdiction *
          </label>
          <select
            value={jurisdiction}
            onChange={(e) => {
              setJurisdiction(e.target.value)
              setAnnex('') // Reset annex when jurisdiction changes
            }}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            disabled={loading}
          >
            {JURISDICTIONS.map(j => (
              <option key={j.code} value={j.code}>
                {j.code} - {j.name}
              </option>
            ))}
          </select>
        </div>

        {/* File Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            文件類型 File Type
          </label>
          <select
            value={fileType}
            onChange={(e) => setFileType(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            disabled={loading}
          >
            {FILE_TYPES.map(ft => (
              <option key={ft.value} value={ft.value}>
                {ft.label}
              </option>
            ))}
          </select>
        </div>

        {/* Annex Selection (for EU/ASEAN) */}
        {selectedJurisdiction && selectedJurisdiction.annexes.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              附錄編號 Annex (Optional)
            </label>
            <select
              value={annex}
              onChange={(e) => setAnnex(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              disabled={loading}
            >
              <option value="">選擇附錄 Select Annex...</option>
              {selectedJurisdiction.annexes.map(a => (
                <option key={a} value={a}>
                  Annex {a}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Version (Optional) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            版本標識 Version (Optional)
          </label>
          <input
            type="text"
            value={version}
            onChange={(e) => setVersion(e.target.value)}
            placeholder="例如: 2024-12 或留空使用時間戳"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            disabled={loading}
          />
        </div>
      </div>

      {/* File Upload Area */}
      <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center mb-6">
        <input
          type="file"
          accept=".pdf,.json,.html"
          onChange={handleFileSelect}
          className="hidden"
          id="regulation-file-upload"
          disabled={loading}
        />
        <label
          htmlFor="regulation-file-upload"
          className="cursor-pointer flex flex-col items-center space-y-4"
        >
          <svg
            className="w-16 h-16 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>

          <div>
            <p className="text-lg font-medium text-gray-900 dark:text-white">
              {file ? file.name : '點擊選擇文件 Click to select file'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              支援 PDF, JSON, HTML (最大 50MB)
            </p>
          </div>
        </label>
      </div>

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        disabled={loading || !file}
        className="w-full px-6 py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors disabled:cursor-not-allowed"
      >
        {loading ? '上傳處理中... Uploading...' : '上傳並處理 Upload & Process'}
      </button>

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">
            ❌ {error}
          </p>
        </div>
      )}

      {/* Success Display */}
      {uploadResult && uploadResult.success && (
        <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <p className="text-sm font-medium text-green-800 dark:text-green-400 mb-2">
            ✅ {uploadResult.message}
          </p>
          <div className="text-xs text-green-700 dark:text-green-500 space-y-1">
            <p><strong>Jurisdiction:</strong> {uploadResult.data?.jurisdiction}</p>
            <p><strong>File:</strong> {uploadResult.data?.filename}</p>
            <p><strong>Path:</strong> {uploadResult.data?.file_path}</p>
          </div>
          <p className="text-xs text-green-600 dark:text-green-500 mt-2">
            處理工作流已觸發，請檢查 GitHub Actions 查看處理進度。
            <br />
            Processing workflow triggered. Check GitHub Actions for progress.
          </p>
        </div>
      )}

      {/* Help Text */}
      <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          使用說明 Instructions:
        </p>
        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1 list-disc list-inside">
          <li>選擇對應的法規辖區 (EU, ASEAN, CN, JP, CA)</li>
          <li>對於 EU 和 ASEAN，可選擇附錄編號 (Annex II-VI)</li>
          <li>上傳 PDF、JSON 或 HTML 格式的法規文件</li>
          <li>系統將自動解析並更新法規數據庫</li>
          <li>處理完成後，結果將自動提交到 GitHub</li>
          <li className="font-medium text-primary-600 dark:text-primary-400">
            📊 上傳完成後，可前往「法規瀏覽」頁面查看解析結果
          </li>
        </ul>
      </div>
    </div>
  )
}
