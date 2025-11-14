/**
 * Browser-side compliance checking library
 */

interface Ingredient {
  name: string
  concentration?: number
  role?: string
}

interface ComplianceResult {
  ingredient_name: string
  jurisdiction: string
  status: 'compliant' | 'restricted_compliant' | 'non_compliant' | 'banned' | 'insufficient_info'
  matched_clauses: any[]
  rationale: string
  required_fields?: string[]
  warnings?: string[]
}

// Cache for loaded rules
const rulesCache: Record<string, any> = {}

/**
 * Load rules for a jurisdiction
 */
async function loadRules(jurisdiction: string): Promise<any> {
  if (rulesCache[jurisdiction]) {
    return rulesCache[jurisdiction]
  }

  try {
    // Load from GitHub Pages data directory
    // 使用完整路徑以支持項目頁面部署
    const basePath = '/AILAWFORBEAUTY'
    const response = await fetch(`${basePath}/data/rules/${jurisdiction}/latest.json`)

    if (!response.ok) {
      console.warn(`No rules found for ${jurisdiction}`)
      return { clauses: [] }
    }

    const rules = await response.json()
    rulesCache[jurisdiction] = rules
    return rules
  } catch (error) {
    console.error(`Error loading rules for ${jurisdiction}:`, error)
    return { clauses: [] }
  }
}

/**
 * Normalize INCI name for matching
 */
function normalizeInciName(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/\s+/g, ' ')
}

/**
 * Check if clause matches ingredient
 */
function matchesIngredient(normalizedName: string, clause: any): boolean {
  const clauseIng = normalizeInciName(clause.ingredient_ref || '')
  const clauseInci = normalizeInciName(clause.inci || '')

  return normalizedName === clauseIng || normalizedName === clauseInci
}

/**
 * Check single ingredient compliance
 */
export async function checkIngredient(
  ingredient: Ingredient,
  jurisdiction: string,
  productInfo: any = {}
): Promise<ComplianceResult> {
  const rules = await loadRules(jurisdiction)
  const clauses = rules.clauses || []

  const normalizedName = normalizeInciName(ingredient.name)

  // Find matching clauses
  const matchedClauses = clauses.filter((clause: any) =>
    matchesIngredient(normalizedName, clause)
  )

  // If no match, consider compliant
  if (matchedClauses.length === 0) {
    return {
      ingredient_name: ingredient.name,
      jurisdiction,
      status: 'compliant',
      matched_clauses: [],
      rationale: '未在資料庫中發現限制 No restrictions found in database'
    }
  }

  // Check for banned
  const bannedClause = matchedClauses.find((c: any) => c.category === 'banned')
  if (bannedClause) {
    return {
      ingredient_name: ingredient.name,
      jurisdiction,
      status: 'banned',
      matched_clauses: [bannedClause],
      rationale: `成分被禁用 Ingredient is banned. ${bannedClause.source_ref || ''}`,
      warnings: [bannedClause.notes || '']
    }
  }

  // Check for restricted
  const restrictedClauses = matchedClauses.filter((c: any) => c.category === 'restricted')
  if (restrictedClauses.length > 0) {
    return evaluateRestrictions(ingredient, jurisdiction, restrictedClauses, productInfo)
  }

  // Check for allowed categories
  const allowedClauses = matchedClauses.filter((c: any) =>
    ['colorant', 'preservative', 'uv_filter', 'allowed'].includes(c.category)
  )

  if (allowedClauses.length > 0) {
    return evaluateAllowed(ingredient, jurisdiction, allowedClauses, productInfo)
  }

  return {
    ingredient_name: ingredient.name,
    jurisdiction,
    status: 'compliant',
    matched_clauses: matchedClauses,
    rationale: '成分已匹配但無特定限制 Ingredient matched but has no specific restrictions'
  }
}

/**
 * Evaluate restriction compliance
 */
function evaluateRestrictions(
  ingredient: Ingredient,
  jurisdiction: string,
  clauses: any[],
  productInfo: any
): ComplianceResult {
  const requiredFields: string[] = []
  const warnings: string[] = []

  for (const clause of clauses) {
    // Handle both object and string conditions for backwards compatibility
    const conditions = typeof clause.conditions === 'object' ? clause.conditions : {}
    const maxPct = conditions.max_pct

    // Check concentration
    if (maxPct !== null && maxPct !== undefined) {
      if (ingredient.concentration === undefined || ingredient.concentration === null) {
        requiredFields.push('concentration')
      } else if (ingredient.concentration > maxPct) {
        return {
          ingredient_name: ingredient.name,
          jurisdiction,
          status: 'non_compliant',
          matched_clauses: [clause],
          rationale: `濃度 ${ingredient.concentration}% 超過最大限制 ${maxPct}% Concentration exceeds maximum. ${clause.source_ref || ''}`,
          warnings: [clause.warnings || '']
        }
      }
    }

    // Check product type
    const allowedTypes = conditions.product_type || []
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
          warnings: [clause.warnings || '']
        }
      }
    }

    if (clause.warnings) {
      warnings.push(clause.warnings)
    }
  }

  if (requiredFields.length > 0) {
    return {
      ingredient_name: ingredient.name,
      jurisdiction,
      status: 'insufficient_info',
      matched_clauses: clauses,
      rationale: `需要額外資訊 Additional information required: ${requiredFields.join(', ')}`,
      required_fields: requiredFields,
      warnings
    }
  }

  return {
    ingredient_name: ingredient.name,
    jurisdiction,
    status: 'restricted_compliant',
    matched_clauses: clauses,
    rationale: `成分受限但符合條件 Ingredient is restricted but complies with conditions. ${clauses[0].source_ref || ''}`,
    warnings
  }
}

/**
 * Evaluate allowed category compliance
 */
function evaluateAllowed(
  ingredient: Ingredient,
  jurisdiction: string,
  clauses: any[],
  productInfo: any
): ComplianceResult {
  const requiredFields: string[] = []
  const warnings: string[] = []

  for (const clause of clauses) {
    // Handle both object and string conditions for backwards compatibility
    const conditions = typeof clause.conditions === 'object' ? clause.conditions : {}
    const maxPct = conditions.max_pct

    if (maxPct !== null && maxPct !== undefined) {
      if (ingredient.concentration === undefined || ingredient.concentration === null) {
        requiredFields.push('concentration')
      } else if (ingredient.concentration > maxPct) {
        return {
          ingredient_name: ingredient.name,
          jurisdiction,
          status: 'non_compliant',
          matched_clauses: [clause],
          rationale: `濃度超過最大限制 Concentration exceeds maximum ${maxPct}%`,
          warnings: [clause.warnings || '']
        }
      }
    }

    if (clause.warnings) {
      warnings.push(clause.warnings)
    }
  }

  if (requiredFields.length > 0) {
    return {
      ingredient_name: ingredient.name,
      jurisdiction,
      status: 'insufficient_info',
      matched_clauses: clauses,
      rationale: `需要額外資訊 Additional information required: ${requiredFields.join(', ')}`,
      required_fields: requiredFields,
      warnings
    }
  }

  const category = clauses[0].category
  return {
    ingredient_name: ingredient.name,
    jurisdiction,
    status: 'compliant',
    matched_clauses: clauses,
    rationale: `成分被允許作為 ${category} 並符合條件 Permitted as ${category} and complies with conditions`,
    warnings
  }
}

/**
 * Check entire formulation
 */
export async function checkFormulation(
  ingredients: Ingredient[],
  jurisdictions: string[],
  productInfo: any = {}
): Promise<Record<string, any>> {
  const results: Record<string, any> = {}

  for (const jurisdiction of jurisdictions) {
    const ingredientResults: ComplianceResult[] = []

    for (const ingredient of ingredients) {
      const result = await checkIngredient(ingredient, jurisdiction, productInfo)
      ingredientResults.push(result)
    }

    // Summary
    const statuses = ingredientResults.map(r => r.status)
    let overallStatus = 'compliant'

    if (statuses.includes('banned') || statuses.includes('non_compliant')) {
      overallStatus = 'non_compliant'
    } else if (statuses.includes('restricted_compliant')) {
      overallStatus = 'restricted_compliant'
    } else if (statuses.includes('insufficient_info')) {
      overallStatus = 'insufficient_info'
    }

    results[jurisdiction] = {
      overall_status: overallStatus,
      total_ingredients: ingredients.length,
      ingredient_results: ingredientResults
    }
  }

  return results
}
