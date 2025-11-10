'use client'

import { useMemo } from 'react'
import jsPDF from 'jspdf'

interface ComplianceMatrixProps {
  results: Record<string, any>
}

const statusColors = {
  compliant: 'bg-green-100 text-green-800 border-green-200',
  restricted_compliant: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  non_compliant: 'bg-red-100 text-red-800 border-red-200',
  banned: 'bg-red-200 text-red-900 border-red-300',
  insufficient_info: 'bg-gray-100 text-gray-800 border-gray-200',
}

const statusLabels = {
  compliant: '✓ 合規 Compliant',
  restricted_compliant: '⚠ 限用-合規 Restricted-Compliant',
  non_compliant: '✗ 不合規 Non-Compliant',
  banned: '⊗ 禁用 Banned',
  insufficient_info: '? 資訊不足 Insufficient Info',
}

export default function ComplianceMatrix({ results }: ComplianceMatrixProps) {
  const jurisdictions = Object.keys(results)

  // Get all unique ingredients
  const allIngredients = useMemo(() => {
    const ingredientsSet = new Set<string>()
    Object.values(results).forEach((jurisdictionResult: any) => {
      jurisdictionResult.ingredient_results.forEach((ir: any) => {
        ingredientsSet.add(ir.ingredient_name)
      })
    })
    return Array.from(ingredientsSet)
  }, [results])

  const exportToPDF = () => {
    const doc = new jsPDF()

    doc.setFontSize(16)
    doc.text('Cosmetics Compliance Report', 14, 15)

    doc.setFontSize(10)
    doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 25)

    let yPos = 35

    jurisdictions.forEach((jurisdiction) => {
      const jurisdictionResult = results[jurisdiction]

      doc.setFontSize(14)
      doc.text(`Market: ${jurisdiction}`, 14, yPos)
      yPos += 7

      doc.setFontSize(10)
      doc.text(`Overall Status: ${jurisdictionResult.overall_status}`, 14, yPos)
      yPos += 10

      jurisdictionResult.ingredient_results.forEach((ir: any) => {
        if (yPos > 270) {
          doc.addPage()
          yPos = 15
        }

        doc.text(`- ${ir.ingredient_name}: ${ir.status}`, 16, yPos)
        yPos += 5

        if (ir.rationale) {
          doc.setFontSize(8)
          const lines = doc.splitTextToSize(ir.rationale, 170)
          doc.text(lines, 20, yPos)
          yPos += lines.length * 4
          doc.setFontSize(10)
        }

        yPos += 3
      })

      yPos += 5
    })

    doc.save('compliance-report.pdf')
  }

  const exportToCSV = () => {
    let csv = 'Ingredient,'+jurisdictions.join(',')+'\n'

    allIngredients.forEach(ingredient => {
      const row = [ingredient]

      jurisdictions.forEach(jurisdiction => {
        const jurisdictionResult = results[jurisdiction]
        const ingredientResult = jurisdictionResult.ingredient_results.find(
          (ir: any) => ir.ingredient_name === ingredient
        )
        row.push(ingredientResult?.status || 'N/A')
      })

      csv += row.join(',') + '\n'
    })

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'compliance-matrix.csv'
    a.click()
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          多市場合規矩陣 Multi-Market Compliance Matrix
        </h2>

        <div className="flex space-x-2">
          <button
            onClick={exportToCSV}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            匯出 CSV Export CSV
          </button>
          <button
            onClick={exportToPDF}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            匯出 PDF Export PDF
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
        {jurisdictions.map((jurisdiction) => {
          const jurisdictionResult = results[jurisdiction]
          const statusClass = statusColors[jurisdictionResult.overall_status as keyof typeof statusColors]

          return (
            <div
              key={jurisdiction}
              className={`p-4 rounded-lg border-2 ${statusClass}`}
            >
              <div className="text-lg font-bold mb-1">{jurisdiction}</div>
              <div className="text-sm">
                {statusLabels[jurisdictionResult.overall_status as keyof typeof statusLabels]}
              </div>
              <div className="text-xs mt-2">
                {jurisdictionResult.total_ingredients} 成分 ingredients
              </div>
            </div>
          )
        })}
      </div>

      {/* Detailed Matrix */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gray-100 dark:bg-gray-700">
              <th className="border border-gray-300 dark:border-gray-600 px-4 py-3 text-left font-semibold">
                成分 Ingredient
              </th>
              {jurisdictions.map((jurisdiction) => (
                <th
                  key={jurisdiction}
                  className="border border-gray-300 dark:border-gray-600 px-4 py-3 text-center font-semibold"
                >
                  {jurisdiction}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {allIngredients.map((ingredient, idx) => (
              <tr
                key={ingredient}
                className={idx % 2 === 0 ? 'bg-white dark:bg-gray-800' : 'bg-gray-50 dark:bg-gray-750'}
              >
                <td className="border border-gray-300 dark:border-gray-600 px-4 py-3 font-medium">
                  {ingredient}
                </td>
                {jurisdictions.map((jurisdiction) => {
                  const jurisdictionResult = results[jurisdiction]
                  const ingredientResult = jurisdictionResult.ingredient_results.find(
                    (ir: any) => ir.ingredient_name === ingredient
                  )

                  if (!ingredientResult) {
                    return (
                      <td
                        key={jurisdiction}
                        className="border border-gray-300 dark:border-gray-600 px-4 py-3 text-center"
                      >
                        N/A
                      </td>
                    )
                  }

                  const statusClass = statusColors[ingredientResult.status as keyof typeof statusColors]

                  return (
                    <td
                      key={jurisdiction}
                      className="border border-gray-300 dark:border-gray-600 px-2 py-2"
                    >
                      <div className={`p-2 rounded text-xs ${statusClass}`}>
                        <div className="font-semibold mb-1">
                          {statusLabels[ingredientResult.status as keyof typeof statusLabels]}
                        </div>
                        <div className="text-[10px] leading-tight">
                          {ingredientResult.rationale}
                        </div>
                        {ingredientResult.warnings && ingredientResult.warnings.length > 0 && (
                          <div className="mt-1 text-[10px] text-red-600">
                            ⚠ {ingredientResult.warnings.join('; ')}
                          </div>
                        )}
                      </div>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
