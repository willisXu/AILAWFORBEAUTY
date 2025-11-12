/**
 * 解析表格查询 API
 *
 * GET /api/parsed-tables?jurisdiction={code}&version={version}
 *
 * 返回特定辖区的所有解析表格数据（基于V2多表架构）
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 数据文件路径
const DATA_DIR = path.join(__dirname, '..', 'data', 'parsed');

// 六张表的类型
const TABLE_TYPES = [
  'prohibited',
  'restricted',
  'preservatives',
  'uv_filters',
  'colorants',
  'whitelist'
];

// 表格的中英文名称
const TABLE_NAMES = {
  'prohibited': {
    en: 'Prohibited Substances',
    zh: '禁用物质清单'
  },
  'restricted': {
    en: 'Restricted Substances',
    zh: '限用物质清单'
  },
  'preservatives': {
    en: 'Allowed Preservatives',
    zh: '防腐剂允用表'
  },
  'uv_filters': {
    en: 'Allowed UV Filters',
    zh: '紫外线吸收剂允用表'
  },
  'colorants': {
    en: 'Allowed Colorants',
    zh: '色料允用表'
  },
  'whitelist': {
    en: 'General Whitelist',
    zh: '一般白名单（原料名录）'
  }
};

/**
 * 加载特定表格的数据
 */
async function loadTableData(jurisdiction, tableType, version = 'latest') {
  try {
    const fileName = version === 'latest'
      ? `${tableType}_latest.json`
      : `${tableType}_${version}.json`;

    const filePath = path.join(DATA_DIR, jurisdiction, fileName);
    const data = await fs.readFile(filePath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    // 如果文件不存在，返回空数据
    if (error.code === 'ENOENT') {
      return null;
    }
    throw error;
  }
}

/**
 * 加载所有表格数据
 */
async function loadAllTables(jurisdiction, version = 'latest') {
  const tables = {};

  for (const tableType of TABLE_TYPES) {
    const data = await loadTableData(jurisdiction, tableType, version);
    if (data) {
      tables[tableType] = {
        ...data,
        displayName: TABLE_NAMES[tableType]
      };
    }
  }

  return tables;
}

/**
 * 获取可用的版本列表
 */
async function getAvailableVersions(jurisdiction) {
  try {
    const dirPath = path.join(DATA_DIR, jurisdiction);
    const files = await fs.readdir(dirPath);

    // 提取版本号（从文件名中）
    const versions = new Set();
    versions.add('latest');

    for (const file of files) {
      const match = file.match(/_(\d{14})\.json$/);
      if (match) {
        versions.add(match[1]);
      }
    }

    return Array.from(versions).sort().reverse();
  } catch (error) {
    if (error.code === 'ENOENT') {
      return ['latest'];
    }
    throw error;
  }
}

/**
 * 主处理函数
 */
export default async function handler(req, res) {
  // 只允许 GET 请求
  if (req.method !== 'GET') {
    return res.status(405).json({
      error: 'Method not allowed',
      message: 'Only GET requests are supported'
    });
  }

  try {
    const { jurisdiction, version = 'latest', table } = req.query;

    // 验证必需参数
    if (!jurisdiction) {
      return res.status(400).json({
        error: 'Missing parameter',
        message: 'jurisdiction parameter is required'
      });
    }

    // 验证辖区代码
    const validJurisdictions = ['EU', 'JP', 'CN', 'CA', 'ASEAN'];
    if (!validJurisdictions.includes(jurisdiction)) {
      return res.status(400).json({
        error: 'Invalid jurisdiction',
        message: `jurisdiction must be one of: ${validJurisdictions.join(', ')}`
      });
    }

    // 如果指定了单个表格，只返回该表格
    if (table) {
      if (!TABLE_TYPES.includes(table)) {
        return res.status(400).json({
          error: 'Invalid table type',
          message: `table must be one of: ${TABLE_TYPES.join(', ')}`
        });
      }

      const tableData = await loadTableData(jurisdiction, table, version);

      if (!tableData) {
        return res.status(404).json({
          error: 'Table not found',
          message: `No data found for ${jurisdiction} - ${table} (version: ${version})`
        });
      }

      return res.status(200).json({
        success: true,
        jurisdiction,
        table,
        version,
        displayName: TABLE_NAMES[table],
        data: tableData
      });
    }

    // 返回所有表格
    const tables = await loadAllTables(jurisdiction, version);

    if (Object.keys(tables).length === 0) {
      return res.status(404).json({
        error: 'No data found',
        message: `No parsed data found for jurisdiction: ${jurisdiction} (version: ${version})`
      });
    }

    // 获取可用版本列表
    const availableVersions = await getAvailableVersions(jurisdiction);

    // 计算总体统计
    const statistics = {
      total_tables: Object.keys(tables).length,
      total_records: Object.values(tables).reduce((sum, t) => sum + (t.total_records || 0), 0),
      by_table: {}
    };

    for (const [tableType, tableData] of Object.entries(tables)) {
      statistics.by_table[tableType] = {
        count: tableData.total_records || 0,
        name: TABLE_NAMES[tableType]
      };
    }

    return res.status(200).json({
      success: true,
      jurisdiction,
      version,
      available_versions: availableVersions,
      statistics,
      tables
    });

  } catch (error) {
    console.error('Error loading parsed tables:', error);
    return res.status(500).json({
      error: 'Internal server error',
      message: error.message
    });
  }
}
