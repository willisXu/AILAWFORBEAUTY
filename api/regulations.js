/**
 * 法规查询 API
 *
 * 提供两个主要端点：
 * 1. GET /api/regulations/{cas_or_inci} - 单成分查询
 * 2. GET /api/compare - 多国差异比对
 *
 * 基于新的多表架构（Multi-Table Model）
 */

const fs = require('fs').promises;
const path = require('path');

// 数据文件路径
const DATA_DIR = path.join(__dirname, '..', 'data', 'integrated');
const MASTER_VIEW_FILE = path.join(DATA_DIR, 'master_view.json');

/**
 * 加载主视图数据
 */
async function loadMasterView() {
  try {
    const data = await fs.readFile(MASTER_VIEW_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Failed to load master view:', error);
    return null;
  }
}

/**
 * 查找成分（通过 INCI 名称或 CAS 号）
 */
function findIngredient(masterView, query) {
  if (!masterView || !masterView.data) {
    return null;
  }

  const queryLower = query.toLowerCase().trim();

  // 查找匹配的成分
  return masterView.data.find(item => {
    const inciMatch = item.INCI_Name && item.INCI_Name.toLowerCase() === queryLower;
    const casMatch = item.CAS_No && item.CAS_No === query;
    return inciMatch || casMatch;
  });
}

/**
 * 模糊搜索成分
 */
function searchIngredients(masterView, query, limit = 10) {
  if (!masterView || !masterView.data) {
    return [];
  }

  const queryLower = query.toLowerCase().trim();
  const results = [];

  for (const item of masterView.data) {
    let score = 0;

    // 完全匹配
    if (item.INCI_Name && item.INCI_Name.toLowerCase() === queryLower) {
      score = 100;
    }
    // CAS 号完全匹配
    else if (item.CAS_No && item.CAS_No === query) {
      score = 95;
    }
    // 包含查询字符串
    else if (item.INCI_Name && item.INCI_Name.toLowerCase().includes(queryLower)) {
      score = 50;
    }
    // CAS 号部分匹配
    else if (item.CAS_No && item.CAS_No.includes(query)) {
      score = 45;
    }

    if (score > 0) {
      results.push({ ...item, _score: score });
    }
  }

  // 按得分排序
  results.sort((a, b) => b._score - a._score);

  // 移除 _score 字段并返回
  return results.slice(0, limit).map(({ _score, ...item }) => item);
}

/**
 * 单成分查询处理器
 *
 * GET /api/regulations/{cas_or_inci}
 *
 * Response:
 * {
 *   "INCI_Name": "Triclosan",
 *   "CAS_No": "3380-34-5",
 *   "Regulations": {
 *     "EU": {...},
 *     "ASEAN": {...},
 *     "JP": {...},
 *     "CA": {...},
 *     "CN": {...}
 *   }
 * }
 */
async function handleSingleIngredientQuery(request, response) {
  try {
    // 从 URL 中提取参数
    const url = new URL(request.url, `http://${request.headers.host}`);
    const pathParts = url.pathname.split('/');
    const query = decodeURIComponent(pathParts[pathParts.length - 1]);

    if (!query) {
      return response.status(400).json({
        error: 'Missing ingredient identifier (INCI name or CAS number)',
      });
    }

    // 加载主视图
    const masterView = await loadMasterView();

    if (!masterView) {
      return response.status(500).json({
        error: 'Failed to load regulation data',
      });
    }

    // 查找成分
    const ingredient = findIngredient(masterView, query);

    if (!ingredient) {
      // 尝试模糊搜索
      const suggestions = searchIngredients(masterView, query, 5);

      return response.status(404).json({
        error: 'Ingredient not found',
        query: query,
        suggestions: suggestions.map(item => ({
          INCI_Name: item.INCI_Name,
          CAS_No: item.CAS_No,
        })),
      });
    }

    // 返回成分信息
    return response.status(200).json({
      INCI_Name: ingredient.INCI_Name,
      CAS_No: ingredient.CAS_No,
      Regulations: ingredient.Regulations,
      _metadata: {
        generated_at: masterView.generated_at,
        jurisdictions: masterView.jurisdictions,
      },
    });

  } catch (error) {
    console.error('Error handling single ingredient query:', error);
    return response.status(500).json({
      error: 'Internal server error',
      message: error.message,
    });
  }
}

/**
 * 多国差异比对处理器
 *
 * GET /api/compare?cas={cas_no}&jurisdictions=EU,JP,CN
 * 或
 * GET /api/compare?inci={inci_name}&jurisdictions=EU,JP,CN
 *
 * Response:
 * {
 *   "INCI_Name": "Triclosan",
 *   "CAS_No": "3380-34-5",
 *   "Comparison": {
 *     "EU": {...},
 *     "JP": {...},
 *     "CN": {...}
 *   },
 *   "Differences": [
 *     {
 *       "field": "Max_Conc_Percent",
 *       "jurisdictions": {
 *         "EU": 0.3,
 *         "JP": 0.1,
 *         "CN": "未规定"
 *       },
 *       "severity": "high"
 *     }
 *   ]
 * }
 */
async function handleComparisonQuery(request, response) {
  try {
    // 解析查询参数
    const url = new URL(request.url, `http://${request.headers.host}`);
    const params = url.searchParams;

    const cas = params.get('cas');
    const inci = params.get('inci');
    const jurisdictionsParam = params.get('jurisdictions');

    // 验证参数
    if (!cas && !inci) {
      return response.status(400).json({
        error: 'Missing required parameter: cas or inci',
      });
    }

    // 解析法规属地列表
    const jurisdictions = jurisdictionsParam
      ? jurisdictionsParam.split(',').map(j => j.trim().toUpperCase())
      : ['EU', 'ASEAN', 'JP', 'CA', 'CN'];

    // 验证法规属地
    const validJurisdictions = ['EU', 'ASEAN', 'JP', 'CA', 'CN'];
    const invalidJurisdictions = jurisdictions.filter(j => !validJurisdictions.includes(j));

    if (invalidJurisdictions.length > 0) {
      return response.status(400).json({
        error: 'Invalid jurisdictions',
        invalid: invalidJurisdictions,
        valid: validJurisdictions,
      });
    }

    // 加载主视图
    const masterView = await loadMasterView();

    if (!masterView) {
      return response.status(500).json({
        error: 'Failed to load regulation data',
      });
    }

    // 查找成分
    const query = cas || inci;
    const ingredient = findIngredient(masterView, query);

    if (!ingredient) {
      return response.status(404).json({
        error: 'Ingredient not found',
        query: query,
      });
    }

    // 提取指定法规属地的信息
    const comparison = {};
    for (const jurisdiction of jurisdictions) {
      comparison[jurisdiction] = ingredient.Regulations[jurisdiction] || {
        Status: '未规定',
      };
    }

    // 分析差异
    const differences = analyzeDifferences(comparison, jurisdictions);

    // 返回比对结果
    return response.status(200).json({
      INCI_Name: ingredient.INCI_Name,
      CAS_No: ingredient.CAS_No,
      Comparison: comparison,
      Differences: differences,
      _metadata: {
        generated_at: masterView.generated_at,
        jurisdictions_compared: jurisdictions,
      },
    });

  } catch (error) {
    console.error('Error handling comparison query:', error);
    return response.status(500).json({
      error: 'Internal server error',
      message: error.message,
    });
  }
}

/**
 * 分析多国法规差异
 */
function analyzeDifferences(comparison, jurisdictions) {
  const differences = [];

  // 比较的字段
  const fieldsToCompare = [
    { name: 'Status', severity: 'high' },
    { name: 'Max_Conc_Percent', severity: 'high' },
    { name: 'Product_Type', severity: 'medium' },
    { name: 'Conditions', severity: 'medium' },
    { name: 'Legal_Basis', severity: 'low' },
  ];

  for (const field of fieldsToCompare) {
    const values = {};
    let hasDifference = false;

    // 收集每个法规属地的值
    for (const jurisdiction of jurisdictions) {
      const value = comparison[jurisdiction][field.name];
      values[jurisdiction] = value !== undefined ? value : null;

      // 检查是否有差异
      if (Object.keys(values).length > 1) {
        const firstValue = Object.values(values)[0];
        if (value !== firstValue) {
          hasDifference = true;
        }
      }
    }

    // 如果有差异，添加到结果
    if (hasDifference) {
      differences.push({
        field: field.name,
        jurisdictions: values,
        severity: field.severity,
      });
    }
  }

  return differences;
}

/**
 * 统计信息查询处理器
 *
 * GET /api/statistics
 */
async function handleStatisticsQuery(request, response) {
  try {
    const statisticsFile = path.join(DATA_DIR, 'statistics.json');
    const data = await fs.readFile(statisticsFile, 'utf8');
    const statistics = JSON.parse(data);

    return response.status(200).json(statistics);

  } catch (error) {
    console.error('Error handling statistics query:', error);
    return response.status(500).json({
      error: 'Failed to load statistics',
      message: error.message,
    });
  }
}

/**
 * 主路由处理器
 */
module.exports = async (request, response) => {
  // 设置 CORS 头
  response.setHeader('Access-Control-Allow-Origin', '*');
  response.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  response.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // 处理 OPTIONS 请求
  if (request.method === 'OPTIONS') {
    return response.status(200).end();
  }

  // 只允许 GET 请求
  if (request.method !== 'GET') {
    return response.status(405).json({
      error: 'Method not allowed',
      allowed: ['GET'],
    });
  }

  const url = new URL(request.url, `http://${request.headers.host}`);

  // 路由
  if (url.pathname.startsWith('/api/compare')) {
    return handleComparisonQuery(request, response);
  } else if (url.pathname === '/api/statistics') {
    return handleStatisticsQuery(request, response);
  } else if (url.pathname.startsWith('/api/regulations/')) {
    return handleSingleIngredientQuery(request, response);
  } else {
    return response.status(404).json({
      error: 'Not found',
      available_endpoints: [
        'GET /api/regulations/{cas_or_inci}',
        'GET /api/compare?cas={cas_no}&jurisdictions=EU,JP,CN',
        'GET /api/statistics',
      ],
    });
  }
};
