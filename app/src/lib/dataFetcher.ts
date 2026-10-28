/**
 * Data fetcher utility that works in both static export and dynamic modes
 *
 * In static mode (GitHub Pages): directly reads JSON files
 * In dynamic mode (Vercel): uses API routes
 */

export interface ParsedTablesResponse {
  success: boolean
  jurisdiction: string
  version: string
  available_versions: string[]
  statistics: {
    total_tables: number
    total_records: number
    by_table: Record<string, { count: number; name: { en: string; zh: string } }>
  }
  tables: Record<string, any>
}

const TABLE_TYPES = [
  'prohibited',
  'restricted',
  'preservatives',
  'uv_filters',
  'colorants',
  'whitelist'
]

const TABLE_NAMES = {
  'prohibited': { en: 'Prohibited Substances', zh: '禁用物质清单' },
  'restricted': { en: 'Restricted Substances', zh: '限用物质清单' },
  'preservatives': { en: 'Allowed Preservatives', zh: '防腐剂允用表' },
  'uv_filters': { en: 'Allowed UV Filters', zh: '紫外线吸收剂允用表' },
  'colorants': { en: 'Allowed Colorants', zh: '色料允用表' },
  'whitelist': { en: 'General Whitelist', zh: '一般白名单（原料名录）' }
}

/**
 * Detect if running in static export mode
 */
function isStaticMode(): boolean {
  return typeof window !== 'undefined' && window.location.pathname.includes('/AILAWFORBEAUTY')
}

/**
 * Get base path for data files
 */
function getBasePath(): string {
  if (typeof window === 'undefined') return ''
  return process.env.NODE_ENV === 'production' ? '/AILAWFORBEAUTY' : ''
}

/**
 * Fetch parsed tables data - works in both static and dynamic modes
 */
export async function fetchParsedTables(
  jurisdiction: string,
  version: string = 'latest',
  table?: string
): Promise<ParsedTablesResponse> {
  const basePath = getBasePath()

  // Try API first (for Vercel deployment)
  try {
    const apiUrl = `/api/parsed-tables?jurisdiction=${jurisdiction}&version=${version}${table ? `&table=${table}` : ''}`
    const response = await fetch(apiUrl)

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        console.log(`✓ Loaded ${jurisdiction} via API`)
        return data
      }
    }
  } catch (error) {
    console.log(`API not available, falling back to static files`)
  }

  // Fallback: Load from static JSON files (for GitHub Pages)
  try {
    console.log(`Loading ${jurisdiction} from static files...`)
    const tables: Record<string, any> = {}

    for (const tableType of TABLE_TYPES) {
      try {
        const fileUrl = `${basePath}/data/parsed/${jurisdiction}/${tableType}_${version}.json`
        const response = await fetch(fileUrl)

        if (response.ok) {
          const data = await response.json()
          tables[tableType] = {
            ...data,
            displayName: TABLE_NAMES[tableType as keyof typeof TABLE_NAMES]
          }
        }
      } catch (error) {
        // Table doesn't exist, skip it
        console.debug(`Table ${tableType} not found for ${jurisdiction}`)
      }
    }

    if (Object.keys(tables).length === 0) {
      throw new Error(`No data found for ${jurisdiction}`)
    }

    // Calculate statistics
    const statistics = {
      total_tables: Object.keys(tables).length,
      total_records: Object.values(tables).reduce((sum: number, t: any) => sum + (t.total_records || 0), 0),
      by_table: {} as Record<string, { count: number; name: { en: string; zh: string } }>
    }

    for (const [tableType, tableData] of Object.entries(tables)) {
      statistics.by_table[tableType] = {
        count: (tableData as any).total_records || 0,
        name: TABLE_NAMES[tableType as keyof typeof TABLE_NAMES]
      }
    }

    console.log(`✓ Loaded ${jurisdiction} from static files: ${Object.keys(tables).length} tables`)

    return {
      success: true,
      jurisdiction,
      version,
      available_versions: [version],
      statistics,
      tables
    }
  } catch (error) {
    console.error(`Failed to load ${jurisdiction} data:`, error)
    throw error
  }
}

/**
 * Fetch all jurisdictions data
 */
export async function fetchAllJurisdictions(
  jurisdictions: string[]
): Promise<Record<string, any>> {
  const results: Record<string, any> = {}

  for (const jurisdiction of jurisdictions) {
    try {
      const data = await fetchParsedTables(jurisdiction, 'latest')
      if (data.success && data.tables) {
        results[jurisdiction] = data.tables
      }
    } catch (error) {
      console.warn(`Failed to load ${jurisdiction}:`, error)
    }
  }

  return results
}
