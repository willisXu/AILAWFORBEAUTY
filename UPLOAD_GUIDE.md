# 法规文件上传指南 | Regulatory Documents Upload Guide

## 📋 目录结构 Directory Structure

本项目已为各市场法规文件准备好以下目录：

```
data/raw/
├── EU/pdfs/          # 欧盟法规文件
├── JP/pdfs/          # 日本法规文件
├── CN/pdfs/          # 中国法规文件
├── CA/pdfs/          # 加拿大法规文件
└── ASEAN/pdfs/       # 东盟法规文件
```

---

## 🚀 GitHub 网页上传步骤

### 步骤 1：进入 GitHub 仓库
1. 打开浏览器，访问您的 GitHub 仓库
2. 确保您已登录 GitHub 账号

### 步骤 2：选择上传目标目录

根据您的法规文件所属市场，选择对应的目录：

| 市场 | 上传路径 | 示例文件 |
|------|---------|---------|
| 🇪🇺 欧盟 | `data/raw/EU/pdfs/` | EU_Regulation_1223_2009.pdf |
| 🇯🇵 日本 | `data/raw/JP/pdfs/` | JP_MHLW_Notification_2024.pdf |
| 🇨🇳 中国 | `data/raw/CN/pdfs/` | CN_NMPA_Cosmetics_Regulation.pdf |
| 🇨🇦 加拿大 | `data/raw/CA/pdfs/` | CA_Health_Canada_Guidelines.pdf |
| 🌏 东盟 | `data/raw/ASEAN/pdfs/` | ASEAN_Cosmetic_Directive_Annex_II_2024-2.pdf |

### 步骤 3：上传文件

**方法一：通过 GitHub 网页界面**

1. 在仓库页面，点击进入目标目录（例如：`data/raw/EU/pdfs/`）
2. 点击页面右上角的 **"Add file"** 按钮
3. 选择 **"Upload files"**
4. 将您的文件拖放到上传区域，或点击 **"choose your files"** 选择文件
5. 在页面底部填写提交信息：
   - **Commit message**（必填）：例如 "添加 EU 2024 化妆品法规文件"
   - **Extended description**（可选）：添加更详细的说明
6. 选择提交到的分支（默认为当前分支 `claude/add-regulatory-documents-011CV2LKXQV7zJRyT2453rEs`）
7. 点击 **"Commit changes"** 完成上传

**方法二：批量上传多个文件**

如果您有多个文件需要上传：
1. 可以一次性选择或拖放多个文件
2. GitHub 会自动将它们添加到同一个 commit 中
3. 建议在 commit message 中说明上传的文件数量和类型

### 步骤 4：验证上传

1. 上传完成后，您会看到文件出现在目录列表中
2. 点击文件名可以预览内容（PDF 文件可在线查看）
3. 检查文件大小和名称是否正确

---

## 📝 文件命名规范

为了保持项目的一致性，建议使用以下命名格式：

### PDF 原始文件
```
{市场代码}_{法规名称}_{版本/日期}.pdf
```

**示例：**
- `EU_Regulation_1223_2009_Annex_II.pdf`
- `JP_MHLW_Prohibited_Substances_2024.pdf`
- `CN_NMPA_Restricted_Ingredients_20240101.pdf`
- `CA_Cosmetic_Ingredient_Hotlist_20250228.pdf`
- `ASEAN_Cosmetic_Directive_Annex_II_2024-2.pdf`

### 其他文件类型
- Excel 文件：`{市场代码}_{内容描述}.xlsx`
- Word 文件：`{市场代码}_{内容描述}.docx`
- JSON 数据：`{市场代码}_{时间戳}.json`

---

## ⚠️ 注意事项

### 文件大小限制
- GitHub 单个文件最大 100MB
- 如果文件超过限制，请考虑：
  - 压缩文件
  - 分割成多个小文件
  - 使用 Git LFS（大文件存储）

### 文件格式建议
- ✅ **推荐**：PDF、JSON、Excel (.xlsx)
- ⚠️ **谨慎**：Word (.docx)、压缩文件 (.zip)
- ❌ **避免**：可执行文件、临时文件

### 安全提醒
- 确保上传的文件不包含敏感信息（个人数据、密钥等）
- 法规文件应来自官方或可信来源
- 检查文件是否有版权限制

---

## 🔄 上传后的处理流程

文件上传后，系统会：

1. **自动存储**：文件保存在对应的 `data/raw/{市场}/pdfs/` 目录
2. **版本控制**：Git 会追踪所有文件变更历史
3. **待处理**：后续可通过 Python 脚本提取和解析数据
4. **结构化**：解析后的数据会存储到 `data/rules/{市场}/` 目录

---

## 📞 需要帮助？

如果在上传过程中遇到问题：

1. **文件太大**：联系维护者讨论解决方案
2. **不确定上传位置**：参考上方的"选择上传目标目录"表格
3. **命名规范疑问**：可以先上传，后续可重命名
4. **其他问题**：在仓库中创建 [Issue](../../issues)

---

## 📚 相关资源

- [GitHub 文件上传文档](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)
- [项目 README](./README.md)
- [数据处理脚本](./scripts/)

---

**最后更新时间：** 2025-11-11
**维护者：** AI Law for Beauty 项目团队
