# 法规解析系统 V2 使用指南

基于多表架构（Multi-Table Model）的法规解析系统完整使用说明。

## 📋 目录

- [快速开始](#快速开始)
- [系统架构](#系统架构)
- [安装依赖](#安装依赖)
- [解析器使用](#解析器使用)
- [数据整合](#数据整合)
- [数据验证](#数据验证)
- [数据导出](#数据导出)
- [API 使用](#api-使用)
- [测试](#测试)
- [常见问题](#常见问题)

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd scripts
pip install -r requirements.txt
```

### 2. 运行解析

```bash
# 解析所有法规属地
python parsers/parse_all_v2.py --integrate --validate

# 解析特定法规属地
python parsers/parse_all_v2.py --jurisdictions EU JP CN
```

### 3. 导出数据

```python
from utils.data_exporter import DataExporter

exporter = DataExporter('data/integrated')
exporter.export_to_excel('output/regulations.xlsx')
exporter.export_master_view_to_excel('output/comparison.xlsx')
```

---

## 🏗️ 系统架构

```
原始数据 (Raw Data)
    ↓
┌─────────────────────┐
│  解析器 V2          │
│  - EU Parser        │
│  - ASEAN Parser     │
│  - JP Parser        │
│  - CN Parser        │
│  - CA Parser        │
└─────────────────────┘
    ↓
六张分表 (Six Tables)
    ├─ Prohibited
    ├─ Restricted
    ├─ Preservatives
    ├─ UV Filters
    ├─ Colorants
    └─ Whitelist
    ↓
┌─────────────────────┐
│  数据整合器         │
│  - 跨表合并         │
│  - 冲突解决         │
│  - 回填"未规定"     │
└─────────────────────┘
    ↓
统一数据库
    ├─ Six Tables
    ├─ MasterView
    └─ Statistics
    ↓
API / Export
```

---

## 📦 安装依赖

### Python 依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- `pyyaml` - YAML 配置文件支持
- `openpyxl` - Excel 导出支持（可选）
- 其他依赖见 `requirements.txt`

### 可选依赖

Excel 导出功能需要：
```bash
pip install openpyxl
```

---

## 🔧 解析器使用

### 单独运行解析器

#### EU 解析器

```python
from parsers.eu_parser_v2 import EUParserV2

parser = EUParserV2()
result = parser.run('data/raw/EU/latest.json')

print(result['statistics'])
```

#### Japan 解析器（支持三栏矩阵）

```python
from parsers.jp_parser_v2 import JPParserV2

parser = JPParserV2()
result = parser.run('data/raw/JP/latest.json')
```

#### China 解析器（含 IECIC 白名单）

```python
from parsers.cn_parser_v2 import CNParserV2

parser = CNParserV2()
result = parser.run('data/raw/CN/latest.json')
```

### 批量解析

```bash
# 解析所有法规属地
python parsers/parse_all_v2.py

# 仅解析指定法规属地
python parsers/parse_all_v2.py --jurisdictions EU JP

# 同时执行整合和验证
python parsers/parse_all_v2.py --integrate --validate

# 指定输出目录
python parsers/parse_all_v2.py --output-dir /path/to/output
```

---

## 🔗 数据整合

### 基本使用

```python
from integration.data_integrator import DataIntegrator

# 创建整合器
integrator = DataIntegrator(output_dir='data/integrated')

# 添加解析后的数据
integrator.add_records('prohibited', eu_prohibited_records)
integrator.add_records('prohibited', jp_prohibited_records)
integrator.add_records('restricted', eu_restricted_records)

# 执行整合
integrator.integrate()

# 查看统计
stats = integrator.get_statistics()
print(f"Total ingredients: {stats['total_ingredients']}")
```

### 整合功能

1. **跨表合并**：以 CAS + INCI 为主键合并相同成分
2. **冲突解决**：按状态优先级保留（Prohibited > Restricted > Allowed）
3. **回填"未规定"**：自动为缺失的法规属地/表格补充"未规定"状态
4. **生成 MasterView**：创建跨国汇总视图

### 输出文件

整合后会生成以下文件：

```
data/integrated/
├── prohibited.json          # 禁用物质表
├── restricted.json          # 限用物质表
├── preservatives.json       # 防腐剂表
├── uv_filters.json          # UV 过滤剂表
├── colorants.json           # 色料表
├── whitelist.json           # 白名单表
├── master_view.json         # 跨国汇总视图
└── statistics.json          # 统计信息
```

---

## ✓ 数据验证

### 基本使用

```python
from validation.data_validator import DataValidator

# 创建验证器
validator = DataValidator()

# 验证单条记录
is_valid = validator.validate_record(record, 'prohibited')

# 验证整个表
stats = validator.validate_table('prohibited', records)

# 打印报告
validator.print_report()
```

### 验证项目

1. **必填字段验证**：INCI_Name, Jurisdiction, Status
2. **格式验证**：
   - CAS 号码格式（XXXXXXX-XX-X）
   - 浓度范围（0-100%）
   - 日期格式
3. **逻辑一致性**：
   - 状态与表类型匹配
   - 禁用物质不应有最大浓度
   - 限用物质应有浓度或条件
4. **数据完整性**：跨表关联检查

### 验证报告

```python
# 获取详细报告
report = validator.get_report()

print(f"Errors: {report['summary']['total_errors']}")
print(f"Warnings: {report['summary']['total_warnings']}")

# 查看具体错误
for error in report['errors']:
    print(f"[{error['severity']}] {error['code']}: {error['message']}")
```

---

## 📊 数据导出

### 导出为 Excel

```python
from utils.data_exporter import DataExporter

exporter = DataExporter('data/integrated')

# 导出所有表到单个 Excel 文件（多工作表）
exporter.export_to_excel('output/regulations.xlsx')

# 导出指定表
exporter.export_to_excel(
    'output/regulations.xlsx',
    tables=['prohibited', 'restricted', 'preservatives']
)
```

### 导出 MasterView（跨国比对）

```python
# 导出跨国比对表
exporter.export_master_view_to_excel('output/comparison.xlsx')
```

这会创建一个包含所有成分在各法规属地状态的对比表：

| INCI Name | CAS No | EU Status | EU Max Conc | JP Status | JP Max Conc | ... |
|-----------|--------|-----------|-------------|-----------|-------------|-----|
| Triclosan | 3380-34-5 | Allowed | 0.3% | Allowed | 0.1% | ... |

### 导出为 CSV

```python
# 导出为 CSV（每个表一个文件）
exporter.export_to_csv('output/csv')
```

生成文件：
```
output/csv/
├── prohibited.csv
├── restricted.csv
├── preservatives.csv
├── uv_filters.csv
├── colorants.csv
└── whitelist.csv
```

---

## 🌐 API 使用

### 启动 API 服务器

```bash
# 使用 Vercel Dev（如果配置了 vercel.json）
vercel dev

# 或使用 Node.js
node api/regulations.js
```

### API 端点

#### 1. 单成分查询

**请求**：
```bash
curl http://localhost:3000/api/regulations/50-00-0
curl http://localhost:3000/api/regulations/Triclosan
```

**响应**：
```json
{
  "INCI_Name": "Triclosan",
  "CAS_No": "3380-34-5",
  "Regulations": {
    "EU": {
      "Status": "Allowed",
      "Max_Conc_Percent": 0.3,
      "Legal_Basis": "Annex V"
    },
    "JP": {
      "Status": "Allowed",
      "Max_Conc_Percent": 0.1
    }
  }
}
```

#### 2. 多国差异比对

**请求**：
```bash
curl "http://localhost:3000/api/compare?cas=3380-34-5&jurisdictions=EU,JP,CN"
```

**响应**：
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
      "jurisdictions": {"EU": 0.3, "JP": 0.1, "CN": null},
      "severity": "high"
    }
  ]
}
```

#### 3. 统计信息

**请求**：
```bash
curl http://localhost:3000/api/statistics
```

---

## 🧪 测试

### 运行所有测试

```bash
cd scripts
python -m pytest tests/ -v
```

### 运行特定测试

```bash
# 测试单位转换
python -m pytest tests/test_unit_converter.py -v

# 测试 Schema
python -m pytest tests/test_schema.py -v
```

### 使用 unittest

```bash
python tests/test_unit_converter.py
python tests/test_schema.py
```

### 测试覆盖率

```bash
pip install pytest-cov
python -m pytest tests/ --cov=. --cov-report=html
```

---

## ❓ 常见问题

### Q1: Excel 导出失败

**问题**：运行 `export_to_excel()` 时报错

**解决**：
```bash
pip install openpyxl
```

### Q2: 日本三栏矩阵解析错误

**问题**：日本防腐剂/UV 数据解析不正确

**解决**：确保配置文件中定义了三栏字段名：
```yaml
JP:
  preservatives:
    field_mapping:
      Max_Conc_Percent_Rinse: ["粘膜に使用されることがない化粧品のうち洗い流すもの"]
      Max_Conc_Percent_Leave: ["粘膜に使用されることがない化粧品のうち洗い流さないもの"]
      Max_Conc_Percent_Mucosa: ["粘膜に使用されることがある化粧品"]
```

### Q3: CAS 号码验证失败

**问题**：有效的 CAS 号被标记为无效

**解决**：检查格式是否为 `XXXXXXX-XX-X`
```python
from utils.unit_converter import parse_cas_number

# 自动格式化
cas = parse_cas_number('50000')  # → '50-00-0'
```

### Q4: "未规定"记录太多

**问题**：某些成分在所有法规属地都标记为"未规定"

**解决**：这是正常的。如果某个成分确实在某个法规属地没有明确规定，系统会自动标记为"未规定"。可以通过过滤排除：
```python
actual_records = [r for r in records if r.Status != Status.NOT_SPECIFIED]
```

### Q5: 数据整合时出现冲突

**问题**：同一成分在多个表中出现

**解决**：系统会自动按优先级解决：
```
Prohibited > Restricted > Allowed > Listed
```
保留优先级最高的记录，其他记录在 Notes 中标注冲突信息。

---

## 📚 相关文档

- [优化指南](../docs/OPTIMIZATION_GUIDE.md) - 详细的系统架构说明
- [优化总结](../OPTIMIZATION_SUMMARY.md) - 变更记录和技术亮点
- [字段映射配置](config/field_mappings.yaml) - YAML 配置文件
- [Schema 定义](schema/database_schema.py) - 数据模型定义

---

## 💡 最佳实践

### 1. 定期更新配置

当法规更新时，优先更新 `field_mappings.yaml` 而非修改代码。

### 2. 使用版本化数据

保存解析结果时使用版本号：
```python
parser.save_tables(version='20250101')
```

### 3. 验证后再整合

先验证各法规属地的数据，确认无重大错误后再整合：
```bash
python parsers/parse_all_v2.py --validate
# 检查验证报告
python parsers/parse_all_v2.py --integrate
```

### 4. 定期备份

整合后的数据很重要，建议定期备份：
```bash
cp -r data/integrated data/backup/$(date +%Y%m%d)
```

---

## 🔄 更新历史

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| 2.0.0 | 2025-11-12 | 多表架构重构，新增所有解析器 V2 |

---

**文档版本**: 2.0.0
**最后更新**: 2025-11-12
