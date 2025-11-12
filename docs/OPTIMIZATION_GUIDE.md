# 法规解析系统优化指南

本文档说明基于多表架构（Multi-Table Model）的法规解析系统优化方案。

## 📋 目录

- [核心原则](#核心原则)
- [系统架构](#系统架构)
- [数据模型](#数据模型)
- [解析流程](#解析流程)
- [API 接口](#api-接口)
- [使用指南](#使用指南)
- [文件结构](#文件结构)

---

## 🎯 核心原则

### 1. 分表架构（Multi-Table Model）
将法规数据分为**六张主表**管理，每张表对应特定类型的法规要求：

| 表名 | 用途 | 法规来源 |
|------|------|---------|
| `Prohibited_Table` | 禁用物质清单 | EU Annex II, ASEAN Annex II, JP Appendix 1, CN STSC Annex 2 |
| `Restricted_Table` | 限用物质清单 | EU Annex III, ASEAN Annex III, JP Appendix 2, CN STSC Annex 3 |
| `Allowed_Preservatives` | 防腐剂允用表 | EU Annex V, ASEAN Annex VI, JP Appendix 3, CN STSC Annex 4 |
| `Allowed_UV_Filters` | 紫外线吸收剂允用表 | EU Annex VI, ASEAN Annex VII, JP Appendix 4, CN STSC Annex 5 |
| `Allowed_Colorants` | 色料允用表 | EU Annex IV, ASEAN Annex IV, CN STSC Annex 6 |
| `General_Whitelist` | 一般白名单（原料名录） | CN IECIC 2021 |

### 2. 五国数据对应
系统支持以下五个法规属地：
- 🇪🇺 **EU** - 欧盟（Regulation EC No 1223/2009）
- 🌏 **ASEAN** - 东盟（ASEAN Cosmetic Directive）
- 🇯🇵 **JP** - 日本（MHLW Notification No.331）
- 🇨🇦 **CA** - 加拿大（Health Canada Hotlist）
- 🇨🇳 **CN** - 中国（NMPA STSC + IECIC）

### 3. "未规定"标示
对于某个法规属地未涵盖的成分/表格，系统自动标记为 `"未规定"`，确保数据完整性。

### 4. 完全正规化
- **单位统一**：所有浓度值转换为百分比（%）
- **字段标准化**：使用统一的枚举类型（Status, ProductType, Jurisdiction）
- **语义一致**：相同概念在不同法规属地使用相同字段名

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                       数据采集层                              │
│  Scrapers (EU, ASEAN, JP, CA, CN) → Raw Data (JSON)        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                       解析层                                  │
│  Parsers V2 (基于 YAML 配置) → 六张表 (JSON)                │
│  - 字段映射                                                   │
│  - 单位转换                                                   │
│  - 数据正规化                                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                       整合层                                  │
│  Data Integrator                                            │
│  - 跨表合并（以 CAS + INCI 为主键）                          │
│  - 冲突解决（状态优先级）                                     │
│  - 回填"未规定"                                               │
│  - 生成 MasterView                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                       数据层                                  │
│  - 六张主表 JSON 文件                                         │
│  - MasterView (跨国汇总)                                     │
│  - Statistics (统计信息)                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                       API 层                                  │
│  GET /api/regulations/{cas_or_inci}  - 单成分查询           │
│  GET /api/compare?cas=XXX&jurisdictions=EU,JP - 多国比对    │
│  GET /api/statistics - 统计信息                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 数据模型

### 通用字段（所有表共有）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `INCI_Name` | TEXT | NOT NULL | 成分国际命名 |
| `CAS_No` | TEXT | UNIQUE (可为 NULL) | 化学登录号 |
| `Jurisdiction` | ENUM | NOT NULL | 法规属地（EU/ASEAN/JP/CA/CN） |
| `Status` | ENUM | NOT NULL | 状态（Prohibited/Restricted/Allowed/Listed/Not_Listed/未规定） |
| `Product_Type` | ENUM | 可为 NULL | 产品类别（Hair/Skin/Eye/Rinse_Off/Leave_On等） |
| `Max_Conc_Percent` | DECIMAL(6,3) | 可为 NULL | 最大允用浓度（%） |
| `Conditions` | TEXT | 可为 NULL | 使用条件 |
| `Legal_Basis` | TEXT | 可为 NULL | 法规依据 |
| `Update_Date` | DATE | 可为 NULL | 官方版本日期 |
| `Notes` | TEXT | 可为 NULL | 备注 |

### 特殊字段（依表而异）

#### Allowed_Preservatives / Allowed_UV_Filters
- `Label_Warnings`: 特殊标示语要求

#### Allowed_Colorants
- `Colour_Index`: CI 编号
- `Body_Area`: 可用部位

#### General_Whitelist
- `List_Name`: 白名单来源（如 IECIC 2021）
- `IECIC_Status`: 特定状态

---

## 🔄 解析流程

### 1. 配置驱动解析

所有解析器基于 `field_mappings.yaml` 配置文件：

```yaml
EU:
  prohibited:
    source: "Annex II"
    field_mapping:
      INCI_Name: ["Reference number", "Ingredient Name"]
      CAS_No: ["CAS No", "CAS Number"]
    default_status: "Prohibited"
```

### 2. 单位转换规则

| 源单位 | 转换系数 | 目标单位 |
|--------|---------|---------|
| g/100g | 1.0 | % |
| ppm | 0.0001 | % |
| % | 1.0 | % |

### 3. 日本特殊符号处理

| 符号 | 含义 | 处理方式 |
|------|------|---------|
| ○ | 无上限 | `Max_Conc_Percent=NULL`, `Notes="No Limit"` |
| 空白 | 禁止 | 不创建记录 |
| - | 不适用 | `Notes="Not Applicable"` |

### 4. 状态优先级

当同一成分在多个表中出现时，保留优先级最高的状态：

```
Prohibited > Restricted > Allowed > Listed > Not_Listed > 未规定
```

---

## 🔌 API 接口

### 1. 单成分查询

**请求**：
```
GET /api/regulations/{cas_or_inci}
```

**响应示例**：
```json
{
  "INCI_Name": "Triclosan",
  "CAS_No": "3380-34-5",
  "Regulations": {
    "EU": {
      "Status": "Allowed",
      "Max_Conc_Percent": 0.3,
      "Legal_Basis": "Annex V",
      "Update_Date": "2025-10-31"
    },
    "ASEAN": {
      "Status": "Allowed",
      "Max_Conc_Percent": 0.3,
      "Legal_Basis": "Annex VI"
    },
    "JP": {
      "Status": "Allowed",
      "Max_Conc_Percent": 0.1,
      "Product_Type": "Non_Mucosa",
      "Legal_Basis": "Appendix 3"
    },
    "CA": {"Status": "未规定"},
    "CN": {"Status": "未规定"}
  }
}
```

### 2. 多国差异比对

**请求**：
```
GET /api/compare?cas=3380-34-5&jurisdictions=EU,JP,CN
```

**响应示例**：
```json
{
  "INCI_Name": "Triclosan",
  "CAS_No": "3380-34-5",
  "Comparison": {
    "EU": {"Status": "Allowed", "Max_Conc_Percent": 0.3},
    "JP": {"Status": "Allowed", "Max_Conc_Percent": 0.1},
    "CN": {"Status": "未规定"}
  },
  "Differences": [
    {
      "field": "Max_Conc_Percent",
      "jurisdictions": {
        "EU": 0.3,
        "JP": 0.1,
        "CN": null
      },
      "severity": "high"
    }
  ]
}
```

### 3. 统计信息

**请求**：
```
GET /api/statistics
```

**响应示例**：
```json
{
  "generated_at": "2025-11-12T10:30:00Z",
  "statistics": {
    "total_ingredients": 15234,
    "tables": {
      "prohibited": {
        "total": 5430,
        "by_jurisdiction": {
          "EU": 1200,
          "JP": 850,
          "CN": 1100
        }
      }
    }
  }
}
```

---

## 📖 使用指南

### 安装依赖

```bash
# Python 依赖
cd scripts
pip install -r requirements.txt

# API 依赖
cd ../api
npm install
```

### 运行解析器

```python
from parsers.eu_parser_v2 import EUParserV2

# 创建解析器
parser = EUParserV2()

# 解析原始数据
result = parser.run('data/raw/EU/latest.json')

# 查看结果
print(result['statistics'])
```

### 数据整合

```python
from integration.data_integrator import DataIntegrator

# 创建整合器
integrator = DataIntegrator(output_dir='data/integrated')

# 添加各国解析后的数据
# (假设已经解析完成)
integrator.add_records('prohibited', eu_prohibited_records)
integrator.add_records('prohibited', jp_prohibited_records)

# 执行整合
integrator.integrate()
```

### 数据验证

```python
from validation.data_validator import DataValidator

# 创建验证器
validator = DataValidator()

# 验证表
stats = validator.validate_table('prohibited', records)

# 打印报告
validator.print_report()
```

---

## 📁 文件结构

```
AILAWFORBEAUTY/
├── scripts/
│   ├── schema/
│   │   └── database_schema.py          # Schema 定义
│   ├── config/
│   │   └── field_mappings.yaml         # 字段映射配置
│   ├── parsers/
│   │   ├── base_parser_v2.py           # 基础解析器 V2
│   │   ├── eu_parser_v2.py             # EU 解析器
│   │   └── jp_parser_v2.py             # JP 解析器
│   ├── integration/
│   │   └── data_integrator.py          # 数据整合器
│   ├── validation/
│   │   └── data_validator.py           # 数据验证器
│   └── utils/
│       └── unit_converter.py           # 单位转换工具
├── api/
│   └── regulations.js                  # API 端点
├── data/
│   ├── raw/                            # 原始数据
│   ├── parsed/                         # 解析后数据（六张表）
│   └── integrated/                     # 整合数据（MasterView）
└── docs/
    └── OPTIMIZATION_GUIDE.md           # 本文档
```

---

## 🔧 配置说明

### YAML 配置示例

```yaml
# EU 禁用物质配置
EU:
  prohibited:
    source: "Annex II"
    field_mapping:
      INCI_Name: ["Reference number", "Ingredient Name", "Chemical name"]
      CAS_No: ["CAS No", "CAS Number", "EC No"]
      Conditions: ["Scope", "Field of application and/or use"]
    default_status: "Prohibited"
    product_type: "未规定"
```

### Python Schema 示例

```python
from schema.database_schema import ProhibitedRecord, Jurisdiction

record = ProhibitedRecord(
    INCI_Name="Formaldehyde",
    CAS_No="50-00-0",
    Jurisdiction=Jurisdiction.EU,
    Notes="全面禁用"
)
```

---

## 🚀 后续优化方向

1. **数据库迁移**：将 JSON 文件迁移到关系型数据库（PostgreSQL）
2. **增量更新**：支持增量更新和版本快照
3. **自动监控**：自动检测法规版本更新
4. **多语言支持**：支持中文、英文、日文等多语言显示
5. **AI 辅助**：使用 AI 辅助解析复杂的法规文本

---

## 📞 联系方式

如有问题或建议，请联系开发团队。

---

**更新日期**: 2025-11-12
**版本**: 2.0.0
