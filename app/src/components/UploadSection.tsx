'use client'

import { useState, useCallback } from 'react'
import * as XLSX from 'xlsx'
import Papa from 'papaparse'
import { checkFormulation } from '@/lib/complianceChecker'

interface UploadSectionProps {
  onResultsChange: (results: any) => void
}

export default function UploadSection({ onResultsChange }: UploadSectionProps) {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [productInfo, setProductInfo] = useState({
    product_type: 'leave-on',
    markets: ['EU', 'JP', 'CN', 'CA', 'ASEAN']
  })

  const handleFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = e.target.files?.[0]
    if (!uploadedFile) return

    setFile(uploadedFile)
    setLoading(true)

    try {
      const ingredients = await parseFile(uploadedFile)
      const results = await checkFormulation(ingredients, productInfo.markets, productInfo)

      onResultsChange(results)
    } catch (error) {
      console.error('Error processing file:', error)
      alert('檔案處理錯誤 Error processing file: ' + (error as Error).message)
    } finally {
      setLoading(false)
    }
  }, [productInfo, onResultsChange])

  const parseFile = async (file: File): Promise<any[]> => {
    const extension = file.name.split('.').pop()?.toLowerCase()

    if (extension === 'csv') {
      return new Promise((resolve, reject) => {
        Papa.parse(file, {
          header: true,
          skipEmptyLines: true,
          complete: (results) => {
            const ingredients = results.data.map((row: any) => {
              // 支持多種欄位名稱格式
              const name = row['INCI NAME'] || row['INCI name'] || row['INCI'] ||
                          row.ingredient_name || row.name || row.Ingredient

              // 支持 % 符號的欄位名稱
              const concentration = parseFloat(
                row['%'] || row.percentage || row.concentration || row.Concentration || 0
              )

              // 支持 Function 欄位
              const role = row['Function'] || row.function || row.role || row.Role || ''

              // CAS No. 欄位（可選，用於更精確的成分識別）
              const casNo = row['CAS.No.'] || row['CAS No'] || row['CAS'] || row.cas_no || ''

              return {
                name: name?.trim(),
                concentration,
                role: role?.trim(),
                cas_no: casNo?.trim()
              }
            }).filter(ing => ing.name && ing.name.length > 0)

            if (ingredients.length === 0) {
              reject(new Error('未找到有效成分資料。請確保檔案包含 INCI NAME 欄位。\nNo valid ingredients found. Please ensure file contains INCI NAME column.'))
            } else {
              resolve(ingredients)
            }
          },
          error: (error) => reject(new Error('CSV 解析錯誤: ' + error.message))
        })
      })
    } else if (extension === 'xlsx' || extension === 'xls') {
      const buffer = await file.arrayBuffer()
      const workbook = XLSX.read(buffer)
      const sheetName = workbook.SheetNames[0]
      const sheet = workbook.Sheets[sheetName]
      const data = XLSX.utils.sheet_to_json(sheet)

      const ingredients = data.map((row: any) => {
        // 支持多種欄位名稱格式
        const name = row['INCI NAME'] || row['INCI name'] || row['INCI'] ||
                    row.ingredient_name || row.name || row.Ingredient

        const concentration = parseFloat(
          row['%'] || row.percentage || row.concentration || row.Concentration || 0
        )

        const role = row['Function'] || row.function || row.role || row.Role || ''
        const casNo = row['CAS.No.'] || row['CAS No'] || row['CAS'] || row.cas_no || ''

        return {
          name: name?.toString().trim(),
          concentration,
          role: role?.toString().trim(),
          cas_no: casNo?.toString().trim()
        }
      }).filter(ing => ing.name && ing.name.length > 0)

      if (ingredients.length === 0) {
        throw new Error('未找到有效成分資料。請確保檔案包含 INCI NAME 欄位。\nNo valid ingredients found. Please ensure file contains INCI NAME column.')
      }

      return ingredients
    } else {
      throw new Error('不支援的檔案格式。請上傳 CSV 或 Excel 文件。\nUnsupported file format. Please upload CSV or Excel file.')
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
        上傳成分表 Upload Ingredient List
      </h2>

      {/* Product Info */}
      <div className="mb-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            產品類型 Product Type
          </label>
          <select
            value={productInfo.product_type}
            onChange={(e) => setProductInfo({ ...productInfo, product_type: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          >
            <option value="rinse-off">沖洗型 Rinse-off</option>
            <option value="leave-on">停留型 Leave-on</option>
            <option value="hair">髮類 Hair Care</option>
            <option value="oral">口腔 Oral Care</option>
            <option value="eye-area">眼部 Eye Area</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            目標市場 Target Markets
          </label>
          <div className="flex flex-wrap gap-3">
            {['EU', 'JP', 'CN', 'CA', 'ASEAN'].map((market) => (
              <label key={market} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={productInfo.markets.includes(market)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setProductInfo({
                        ...productInfo,
                        markets: [...productInfo.markets, market]
                      })
                    } else {
                      setProductInfo({
                        ...productInfo,
                        markets: productInfo.markets.filter(m => m !== market)
                      })
                    }
                  }}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">{market}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* File Upload */}
      <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center">
        <input
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileUpload}
          className="hidden"
          id="file-upload"
          disabled={loading}
        />
        <label
          htmlFor="file-upload"
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
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>

          <div>
            <p className="text-lg font-medium text-gray-900 dark:text-white">
              {loading ? '處理中... Processing...' : '點擊上傳或拖曳檔案 Click to upload or drag and drop'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              支援 CSV, Excel (.xlsx, .xls)
            </p>
          </div>

          {file && !loading && (
            <div className="text-sm text-primary-600 dark:text-primary-400">
              已選擇: {file.name}
            </div>
          )}
        </label>
      </div>

      {/* File Format Info */}
      <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          檔案格式要求 File Format Requirements:
        </p>
        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1 list-disc list-inside">
          <li>必要欄位 Required: <code className="bg-white dark:bg-gray-800 px-1 rounded">INCI NAME</code></li>
          <li>選用欄位 Optional: <code className="bg-white dark:bg-gray-800 px-1 rounded">CAS.No.</code>, <code className="bg-white dark:bg-gray-800 px-1 rounded">%</code>, <code className="bg-white dark:bg-gray-800 px-1 rounded">Function</code></li>
        </ul>
        <div className="mt-3 p-3 bg-white dark:bg-gray-800 rounded border border-gray-300 dark:border-gray-600">
          <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">範例格式 Example Format:</p>
          <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto">
排序,INCI NAME,CAS.No.,%,Function
1,AQUA,7732-18-5,,SOLVENT
2,NIACINAMIDE,98-92-0,,SMOOTHING
3,GLYCERIN,56-81-5,,HUMECTANT</pre>
        </div>
      </div>
    </div>
  )
}
