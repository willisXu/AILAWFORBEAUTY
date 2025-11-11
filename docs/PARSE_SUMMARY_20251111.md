# 法规数据解析结果摘要 Regulation Data Parse Summary

**解析时间 Parse Time:** 2025-11-11 15:08:19 UTC

## 总体统计 Overall Statistics

| 辖区 Jurisdiction | 成分数 Ingredients | 条款数 Clauses | 禁用 Banned | 限制 Restricted | 允许 Allowed |
|------------------|-------------------|----------------|-------------|-----------------|--------------|
| EU               | 8                 | 8              | 3           | 2               | 3            |
| JP               | 6                 | 6              | 3           | 3               | 0            |
| CN               | 0                 | 0              | 0           | 0               | 0            |
| CA               | 7                 | 7              | 3           | 4               | 0            |
| ASEAN            | 12                | 13             | 3           | 3               | 7            |
| **总计 Total**   | **33**            | **34**         | **12**      | **12**          | **10**       |

## 各辖区详情 Jurisdiction Details

### EU (欧盟 European Union)
- **法规:** Regulation (EC) No 1223/2009
- **版本:** 20240424
- **发布日期:** 2024-04-04
- **生效日期:** 2024-04-24
- **数据源:** European Commission - CosIng Database
- **状态:** ✅ 解析成功

### JP (日本 Japan)
- **法规:** Standards for Cosmetics (化粧品基準)
- **版本:** None
- **数据源:** MHLW
- **状态:** ✅ 解析成功

### CN (中国 China)
- **法规:** 化妆品安全技术规范（2015年版）
- **版本:** None
- **数据源:** NMPA
- **状态:** ⚠️ 解析成功但无数据（需要检查原始数据格式）

### CA (加拿大 Canada)
- **法规:** Cosmetic Ingredient Hotlist
- **版本:** 20250228
- **发布日期:** 2025-02
- **生效日期:** 2025-02-28
- **数据源:** Health Canada
- **状态:** ✅ 解析成功

### ASEAN
- **法规:** ASEAN Cosmetic Directive
- **版本:** 2024-2
- **发布日期:** 2024-12-06
- **生效日期:** 2024-12-06
- **数据源:** ASEAN Cosmetic Directive (December 2024)
- **状态:** ✅ 解析成功

## 文件位置 File Locations

### 解析后的规则 Parsed Rules
```
data/rules/
├── EU/
│   ├── 20240424.json
│   └── latest.json
├── JP/
│   ├── None.json
│   └── latest.json
├── CN/
│   ├── None.json
│   └── latest.json
├── CA/
│   ├── 20250228.json
│   └── latest.json
└── ASEAN/
    ├── 2024-2.json
    └── latest.json
```

## 注意事项 Notes

1. **CN (中国)** 的原始数据解析结果为空，需要检查：
   - 原始数据格式是否正确
   - Parser 是否需要更新以支持当前的数据格式
   - 是否需要重新爬取数据

2. 所有其他辖区的数据解析正常，可以用于合规性检查。

3. 每个辖区都生成了两个文件：
   - 版本化文件（如 `20240424.json`）- 用于历史记录
   - `latest.json` - 始终指向最新版本

## 下一步 Next Steps

1. ✅ 解析完成
2. ⏳ 验证结果
3. ⏳ 提交到 GitHub
4. 🔄 调查 CN 数据问题
5. 📊 生成差异报告（如果有多个版本）

---

**解析工具:** parse_all.py  
**解析器版本:** Latest  
**数据哈希算法:** SHA-256
