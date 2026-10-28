/**
 * Browser-side compliance checking library
 *
 * Rules come from two sources that are merged per jurisdiction and indexed by
 * normalised INCI name and CAS number:
 *   - data/rules/<J>/latest.json          legacy clause list (carries max_pct / product_type)
 *   - data/parsed/<J>/<table>_latest.json V2 multi-table lists extracted from the official texts
 */

export interface Ingredient {
  name: string
  concentration?: number
  role?: string
  cas_no?: string
}

export interface ComplianceResult {
  ingredient_name: string
  jurisdiction: string
  status: 'compliant' | 'restricted_compliant' | 'non_compliant' | 'banned' | 'insufficient_info'
  matched_clauses: Clause[]
  rationale: string
  required_fields?: string[]
  warnings?: string[]
}

export type ClauseCategory = 'banned' | 'restricted' | 'allowed' | 'colorant' | 'preservative' | 'uv_filter'

export interface Clause {
  id: string
  ingredient_ref: string
  inci: string
  cas: string
  category: ClauseCategory
  conditions: { max_pct?: number | null; product_type?: string[] }
  notes: string
  warnings: string
  source_ref: string
  source: 'rules' | 'parsed'
}

interface JurisdictionIndex {
  clauses: Clause[]
  byName: Map<string, Clause[]>
  byCas: Map<string, Clause[]>
}

const BASE_PATH = '/AILAWFORBEAUTY'

const PARSED_TABLES: Record<string, ClauseCategory> = {
  prohibited: 'banned',
  restricted: 'restricted',
  preservatives: 'preservative',
  uv_filters: 'uv_filter',
  colorants: 'colorant',
}

const PARSED_TABLE_LABELS: Record<string, string> = {
  prohibited: 'prohibited substances list',
  restricted: 'restricted substances list',
  preservatives: 'allowed preservatives list',
  uv_filters: 'allowed UV filters list',
  colorants: 'allowed colorants list',
}

// Table header rows that leaked into the extracted data as records
const HEADER_LIKE_NAMES = new Set([
  'ingredient', 'ingredients', 'substance', 'substances', 'inci', 'inci name', 'name',
  'chemical name', 'chemical name/inn', 'substance name', 'cas', 'cas no', 'cas number',
])

// Index per jurisdiction; the promise is cached so concurrent callers share one load
const indexCache: Record<string, Promise<JurisdictionIndex>> = {}

export function normalizeInciName(name: string): string {
  return (name || '').toLowerCase().trim().replace(/\s+/g, ' ')
}

export function normalizeCas(cas: string | null | undefined): string {
  const value = (cas || '').trim().replace(/\s+/g, '')
  return /^\d{2,7}-\d{2}-\d$/.test(value) ? value : ''
}

function toNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string') {
    const parsed = parseFloat(value.replace(',', '.'))
    if (Number.isFinite(parsed)) return parsed
  }
  return null
}

async function fetchJson(path: string): Promise<any | null> {
  try {
    const response = await fetch(`${BASE_PATH}${path}`)
    if (!response.ok) return null
    return await response.json()
  } catch (error) {
    console.warn(`Failed to load ${path}:`, error)
    return null
  }
}

function clauseFromRule(raw: any, jurisdiction: string, position: number): Clause | null {
  const ingredientRef = String(raw?.ingredient_ref || raw?.inci || '').trim()
  if (!ingredientRef || HEADER_LIKE_NAMES.has(ingredientRef.toLowerCase())) return null

  const rawConditions = raw.conditions
  const conditions = rawConditions && typeof rawConditions === 'object' ? rawConditions : {}
  const stringConditions = typeof rawConditions === 'string' ? rawConditions : ''

  return {
    id: String(raw.id || `${jurisdiction}-rule-${position}`),
    ingredient_ref: ingredientRef,
    inci: String(raw.inci || ingredientRef),
    cas: normalizeCas(raw.cas),
    category: raw.category,
    conditions: {
      max_pct: toNumber(conditions.max_pct),
      product_type: Array.isArray(conditions.product_type) ? conditions.product_type : [],
    },
    notes: String(raw.notes || stringConditions || ''),
    warnings: String(raw.warnings || ''),
    source_ref: String(raw.source_ref || ''),
    source: 'rules',
  }
}

function clauseFromParsed(record: any, jurisdiction: string, table: string, position: number): Clause | null {
  const name = String(record?.INCI_Name || '').trim()
  if (!name || HEADER_LIKE_NAMES.has(name.toLowerCase())) return null
  if (String(record.Status || '').toUpperCase() === 'NOT_SPECIFIED') return null

  const maxPct = toNumber(record.Max_Conc_Percent)
  const conditionsText = typeof record.Conditions === 'string' ? record.Conditions.trim() : ''

  return {
    id: `${jurisdiction}-${table}-${position}`,
    ingredient_ref: name,
    inci: name,
    cas: normalizeCas(record.CAS_No),
    category: PARSED_TABLES[table],
    conditions: { max_pct: maxPct, product_type: [] },
    notes: String(record.Notes || conditionsText || ''),
    warnings: '',
    source_ref: String(record.Legal_Basis || `${jurisdiction} ${PARSED_TABLE_LABELS[table]}`),
    source: 'parsed',
  }
}

function addToIndex(map: Map<string, Clause[]>, key: string, clause: Clause): void {
  if (!key) return
  const bucket = map.get(key)
  if (bucket) bucket.push(clause)
  else map.set(key, [clause])
}

function buildIndex(clauses: Clause[]): JurisdictionIndex {
  const byName = new Map<string, Clause[]>()
  const byCas = new Map<string, Clause[]>()
  const seen = new Set<string>()
  const unique: Clause[] = []

  for (const clause of clauses) {
    const nameKey = normalizeInciName(clause.ingredient_ref)
    const inciKey = normalizeInciName(clause.inci)
    const dedupeKey = `${clause.category}|${nameKey}|${clause.cas}`
    if (seen.has(dedupeKey)) continue
    seen.add(dedupeKey)

    unique.push(clause)
    addToIndex(byName, nameKey, clause)
    if (inciKey !== nameKey) addToIndex(byName, inciKey, clause)
    addToIndex(byCas, clause.cas, clause)
  }

  return { clauses: unique, byName, byCas }
}

async function loadIndex(jurisdiction: string): Promise<JurisdictionIndex> {
  const tables = Object.keys(PARSED_TABLES)
  const [rules, ...parsed] = await Promise.all([
    fetchJson(`/data/rules/${jurisdiction}/latest.json`),
    ...tables.map(table => fetchJson(`/data/parsed/${jurisdiction}/${table}_latest.json`)),
  ])

  const clauses: Clause[] = []

  const ruleClauses: any[] = Array.isArray(rules?.clauses) ? rules.clauses : []
  ruleClauses.forEach((raw, i) => {
    const clause = clauseFromRule(raw, jurisdiction, i)
    if (clause) clauses.push(clause)
  })

  parsed.forEach((tableData, t) => {
    const records: any[] = Array.isArray(tableData?.records) ? tableData.records : []
    records.forEach((record, i) => {
      const clause = clauseFromParsed(record, jurisdiction, tables[t], i)
      if (clause) clauses.push(clause)
    })
  })

  if (clauses.length === 0) {
    console.warn(`No rules found for ${jurisdiction}`)
  }

  return buildIndex(clauses)
}

function getIndex(jurisdiction: string): Promise<JurisdictionIndex> {
  if (!indexCache[jurisdiction]) {
    indexCache[jurisdiction] = loadIndex(jurisdiction).catch(error => {
      delete indexCache[jurisdiction]
      throw error
    })
  }
  return indexCache[jurisdiction]
}

/**
 * Preload rules for multiple jurisdictions in parallel
 */
export async function preloadRules(jurisdictions: string[]): Promise<void> {
  await Promise.all(jurisdictions.map(j => getIndex(j)))
}

function findMatches(index: JurisdictionIndex, ingredient: Ingredient): Clause[] {
  const matches = new Set<Clause>()

  const cas = normalizeCas(ingredient.cas_no)
  if (cas) {
    for (const clause of index.byCas.get(cas) || []) matches.add(clause)
  }

  const name = normalizeInciName(ingredient.name)
  if (name) {
    for (const clause of index.byName.get(name) || []) matches.add(clause)
  }

  return Array.from(matches)
}

/**
 * Check single ingredient compliance
 */
export async function checkIngredient(
  ingredient: Ingredient,
  jurisdiction: string,
  productInfo: any = {}
): Promise<ComplianceResult> {
  const index = await getIndex(jurisdiction)
  const matchedClauses = findMatches(index, ingredient)

  if (matchedClauses.length === 0) {
    return {
      ingredient_name: ingredient.name,
      jurisdiction,
      status: 'compliant',
      matched_clauses: [],
      rationale: '未在資料庫中發現限制 No restrictions found in database'
    }
  }

  const bannedClause = matchedClauses.find(c => c.category === 'banned')
  if (bannedClause) {
    return {
      ingredient_name: ingredient.name,
      jurisdiction,
      status: 'banned',
      matched_clauses: [bannedClause],
      rationale: `成分被禁用 Ingredient is banned. ${bannedClause.source_ref}`.trim(),
      warnings: bannedClause.notes ? [bannedClause.notes] : []
    }
  }

  const restrictedClauses = matchedClauses.filter(c => c.category === 'restricted')
  if (restrictedClauses.length > 0) {
    return evaluateRestrictions(ingredient, jurisdiction, restrictedClauses, productInfo)
  }

  const allowedClauses = matchedClauses.filter(c =>
    ['colorant', 'preservative', 'uv_filter', 'allowed'].includes(c.category)
  )
  if (allowedClauses.length > 0) {
    return evaluateAllowed(ingredient, jurisdiction, allowedClauses)
  }

  return {
    ingredient_name: ingredient.name,
    jurisdiction,
    status: 'compliant',
    matched_clauses: matchedClauses,
    rationale: '成分已匹配但無特定限制 Ingredient matched but has no specific restrictions'
  }
}

function hasConcentration(ingredient: Ingredient): boolean {
  return typeof ingredient.concentration === 'number' && Number.isFinite(ingredient.concentration)
}

/**
 * Evaluate restriction compliance
 */
function evaluateRestrictions(
  ingredient: Ingredient,
  jurisdiction: string,
  clauses: Clause[],
  productInfo: any
): ComplianceResult {
  const requiredFields: string[] = []
  const warnings: string[] = []
  let limitKnown = false

  for (const clause of clauses) {
    const maxPct = clause.conditions.max_pct

    if (maxPct !== null && maxPct !== undefined) {
      limitKnown = true
      if (!hasConcentration(ingredient)) {
        requiredFields.push('concentration')
      } else if ((ingredient.concentration as number) > maxPct) {
        return {
          ingredient_name: ingredient.name,
          jurisdiction,
          status: 'non_compliant',
          matched_clauses: [clause],
          rationale: `濃度 ${ingredient.concentration}% 超過最大限制 ${maxPct}% Concentration exceeds maximum. ${clause.source_ref}`.trim(),
          warnings: clause.warnings ? [clause.warnings] : []
        }
      }
    }

    const allowedTypes = clause.conditions.product_type || []
    if (allowedTypes.length > 0) {
      if (!productInfo.product_type) {
        requiredFields.push('product_type')
      } else if (!allowedTypes.includes(productInfo.product_type)) {
        return {
          ingredient_name: ingredient.name,
          jurisdiction,
          status: 'non_compliant',
          matched_clauses: [clause],
          rationale: `產品類型 '${productInfo.product_type}' 不被允許 Product type not allowed. Allowed: ${allowedTypes.join(', ')}`,
          warnings: clause.warnings ? [clause.warnings] : []
        }
      }
    }

    if (clause.warnings) warnings.push(clause.warnings)
    if (clause.notes) warnings.push(clause.notes)
  }

  if (requiredFields.length > 0) {
    return {
      ingredient_name: ingredient.name,
      jurisdiction,
      status: 'insufficient_info',
      matched_clauses: clauses,
      rationale: `需要額外資訊 Additional information required: ${Array.from(new Set(requiredFields)).join(', ')}`,
      required_fields: Array.from(new Set(requiredFields)),
      warnings
    }
  }

  // Listed as restricted but the database carries no numeric limit: flag for
  // manual verification instead of reporting compliance.
  if (!limitKnown) {
    return {
      ingredient_name: ingredient.name,
      jurisdiction,
      status: 'insufficient_info',
      matched_clauses: clauses,
      rationale: `成分列於限用清單，資料庫無濃度上限，請依原始法規核對 Listed as restricted; no concentration limit in database, verify against the source. ${clauses[0].source_ref}`.trim(),
      required_fields: ['verify_restriction_conditions'],
      warnings
    }
  }

  return {
    ingredient_name: ingredient.name,
    jurisdiction,
    status: 'restricted_compliant',
    matched_clauses: clauses,
    rationale: `成分受限但符合條件 Ingredient is restricted but complies with conditions. ${clauses[0].source_ref}`.trim(),
    warnings
  }
}

/**
 * Evaluate allowed category compliance
 */
function evaluateAllowed(
  ingredient: Ingredient,
  jurisdiction: string,
  clauses: Clause[]
): ComplianceResult {
  const requiredFields: string[] = []
  const warnings: string[] = []

  for (const clause of clauses) {
    const maxPct = clause.conditions.max_pct

    if (maxPct !== null && maxPct !== undefined) {
      if (!hasConcentration(ingredient)) {
        requiredFields.push('concentration')
      } else if ((ingredient.concentration as number) > maxPct) {
        return {
          ingredient_name: ingredient.name,
          jurisdiction,
          status: 'non_compliant',
          matched_clauses: [clause],
          rationale: `濃度超過最大限制 Concentration exceeds maximum ${maxPct}%. ${clause.source_ref}`.trim(),
          warnings: clause.warnings ? [clause.warnings] : []
        }
      }
    }

    if (clause.warnings) warnings.push(clause.warnings)
  }

  if (requiredFields.length > 0) {
    return {
      ingredient_name: ingredient.name,
      jurisdiction,
      status: 'insufficient_info',
      matched_clauses: clauses,
      rationale: `需要額外資訊 Additional information required: ${Array.from(new Set(requiredFields)).join(', ')}`,
      required_fields: Array.from(new Set(requiredFields)),
      warnings
    }
  }

  const category = clauses[0].category
  return {
    ingredient_name: ingredient.name,
    jurisdiction,
    status: 'compliant',
    matched_clauses: clauses,
    rationale: `成分被允許作為 ${category} 並符合條件 Permitted as ${category} and complies with conditions. ${clauses[0].source_ref}`.trim(),
    warnings
  }
}

/**
 * Check entire formulation: all jurisdictions and ingredients concurrently
 */
export async function checkFormulation(
  ingredients: Ingredient[],
  jurisdictions: string[],
  productInfo: any = {}
): Promise<Record<string, any>> {
  await preloadRules(jurisdictions)

  const jurisdictionResults = await Promise.all(jurisdictions.map(async (jurisdiction) => {
    const ingredientResults = await Promise.all(
      ingredients.map(ingredient => checkIngredient(ingredient, jurisdiction, productInfo))
    )

    const statuses = ingredientResults.map(r => r.status)
    let overallStatus = 'compliant'

    if (statuses.includes('banned') || statuses.includes('non_compliant')) {
      overallStatus = 'non_compliant'
    } else if (statuses.includes('restricted_compliant')) {
      overallStatus = 'restricted_compliant'
    } else if (statuses.includes('insufficient_info')) {
      overallStatus = 'insufficient_info'
    }

    return {
      jurisdiction,
      data: {
        overall_status: overallStatus,
        total_ingredients: ingredients.length,
        ingredient_results: ingredientResults
      }
    }
  }))

  const results: Record<string, any> = {}
  jurisdictionResults.forEach(({ jurisdiction, data }) => {
    results[jurisdiction] = data
  })

  return results
}
