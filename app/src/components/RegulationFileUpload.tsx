'use client'

import { useState, useCallback } from 'react'
import { getUploadEndpoint } from '../config/api'

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
  const [uploadProgress, setUploadProgress] = useState<number>(0)
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
    setUploadProgress(0)

    try {
      // Validate file size (50MB limit)
      const maxSize = 50 * 1024 * 1024 // 50MB
      if (file.size > maxSize) {
        throw new Error(`文件過大 File too large: ${(file.size / 1024 / 1024).toFixed(2)}MB (max: 50MB)`)
      }

      // Create form data
      const formData = new FormData()
      formData.append('file', file)
      formData.append('jurisdiction', jurisdiction)
      formData.append('fileType', fileType)
      if (annex) formData.append('annex', annex)
      if (version) formData.append('version', version)

      const result = await new Promise<any>((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        xhr.open('POST', getUploadEndpoint())

        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            setUploadProgress(Math.round((e.loaded / e.total) * 100))
          }
        }

        xhr.onload = () => {
          const isJson = (xhr.getResponseHeader('content-type') || '').includes('application/json')

          if (xhr.status === 404 && !isJson) {
            reject(new Error(
              '此站點未提供上傳 API（GitHub Pages 為靜態站點）。請在 config/api.ts 設定 UPLOAD_ENDPOINT，或使用 Vercel 部署。 ' +
              'Upload API is not available on this host (static site). Set UPLOAD_ENDPOINT in config/api.ts or deploy on Vercel.'
            ))
            return
          }

          if (xhr.status === 413) {
            reject(new Error('文件超過伺服器上傳限制 File exceeds the server upload limit'))
            return
          }

          const body = isJson ? JSON.parse(xhr.responseText) : null

          if (xhr.status >= 200 && xhr.status < 300 && body) {
            resolve(body)
          } else {
            reject(new Error(body?.error || body?.message || `Upload failed (HTTP ${xhr.status})`))
          }
        }

        xhr.onerror = () => reject(new Error('網路錯誤，無法連接上傳服務 Network error: could not reach upload service'))
        xhr.send(formData)
      })

      setUploadProgress(100)
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
      setUploadProgress(0)
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

      {/* Upload Progress */}
      {loading && uploadProgress > 0 && (
        <div className="mb-4">
          <div className="flex justify-between mb-1">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              上傳進度 Upload Progress
            </span>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {uploadProgress}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
            <div
              className="bg-primary-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        disabled={loading || !file}
        className="w-full px-6 py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors disabled:cursor-not-allowed"
      >
        {loading
          ? uploadProgress >= 100
            ? '伺服器處理中... Processing on server...'
            : `上傳中 ${uploadProgress}%... Uploading ${uploadProgress}%...`
          : '上傳並處理 Upload & Process'}
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
        </ul>
      </div>
    </div>
  )
}
