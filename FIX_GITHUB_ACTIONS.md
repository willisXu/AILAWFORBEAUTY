# 🔧 GitHub Actions 權限修復指南

## 📋 問題總結

經過詳細診斷，我發現：

✅ **代碼完全沒有問題** - 本地構建 100% 成功
❌ **問題在於 GitHub Actions 權限配置**

## 🎯 核心問題

**GitHub Actions 的 GITHUB_TOKEN 預設只有讀取權限**，無法：
- 創建 gh-pages 分支
- 推送構建結果
- 部署到 GitHub Pages

## ✅ 解決方案

我已經準備好所有修復，您只需要執行以下步驟：

### 方法 1：合併 PR + 配置權限（推薦）

#### 步驟 1：合併包含權限修復的 PR

1. **訪問 PR 比較頁面**：
   ```
   https://github.com/willisXu/AILAWFORBEAUTY/compare/main...claude/cosmetics-compliance-audit-system-011CUyVS38cuTHs1sBC1aJQD
   ```

2. **創建並合併 PR**：
   - 點擊 "Create pull request"
   - 標題：`fix: Add workflow permissions to enable deployment`
   - 直接合併：點擊 "Merge pull request" → "Confirm merge"

#### 步驟 2：配置倉庫的 Actions 權限

**重要**：即使 workflow 文件中設置了權限，倉庫層級的設置可能會覆蓋它。

1. **訪問 Actions 設置**：
   ```
   https://github.com/willisXu/AILAWFORBEAUTY/settings/actions
   ```

2. **配置 Workflow 權限**：
   - 找到 **"Workflow permissions"** 區域
   - 選擇：✅ **"Read and write permissions"**
   - 勾選：✅ **"Allow GitHub Actions to create and approve pull requests"**
   - 點擊 **"Save"** 按鈕

#### 步驟 3：配置 GitHub Pages

1. **訪問 Pages 設置**：
   ```
   https://github.com/willisXu/AILAWFORBEAUTY/settings/pages
   ```

2. **配置部署來源**：
   - **Source**: 選擇 "Deploy from a branch"
   - **Branch**: 選擇 "gh-pages" 和 "/ (root)"
   - 點擊 **"Save"**

   **注意**：如果 gh-pages 分支還不存在，先執行步驟 4，然後回來配置。

#### 步驟 4：手動觸發部署

1. **訪問 Workflows 頁面**：
   ```
   https://github.com/willisXu/AILAWFORBEAUTY/actions/workflows/deploy.yml
   ```

2. **手動運行 Workflow**：
   - 點擊右上角 **"Run workflow"** 按鈕
   - 確保選擇 **"main"** 分支
   - 點擊綠色 **"Run workflow"** 按鈕

3. **監控執行**：
   - 等待 3-5 分鐘
   - 頁面會自動刷新顯示進度
   - 應該會看到：
     ```
     ✓ Checkout
     ✓ Setup Node.js
     ✓ Install dependencies
     ✓ Build
     ✓ Copy data directory
     ✓ Add .nojekyll
     ✓ Deploy
     ```

#### 步驟 5：驗證部署成功

1. **檢查 gh-pages 分支**：
   ```
   https://github.com/willisXu/AILAWFORBEAUTY/tree/gh-pages
   ```
   - 應該會看到構建後的靜態文件

2. **訪問網站**：
   ```
   https://willisxu.github.io/AILAWFORBEAUTY/
   ```
   - 應該看到化妝品法規自動稽核系統的主頁
   - 不再是 404 錯誤

### 方法 2：直接在 GitHub 上編輯（快速修復）

如果不想建立 PR，可以直接編輯：

1. **編輯 workflow 文件**：
   ```
   https://github.com/willisXu/AILAWFORBEAUTY/edit/main/.github/workflows/deploy.yml
   ```

2. **在第 7 行後添加**（在 `workflow_dispatch:` 和 `jobs:` 之間）：
   ```yaml
   # 設置 GITHUB_TOKEN 權限以允許推送到 gh-pages 分支
   permissions:
     contents: write
   ```

   完整結構應該是：
   ```yaml
   name: Deploy to GitHub Pages

   on:
     push:
       branches: [main]
     workflow_dispatch:

   # 設置 GITHUB_TOKEN 權限以允許推送到 gh-pages 分支
   permissions:
     contents: write

   jobs:
     deploy:
       runs-on: ubuntu-latest
       ...
   ```

3. **提交更改**：
   - Commit message: `fix: Add workflow permissions to enable deployment`
   - 點擊 "Commit changes"

4. **然後執行方法 1 的步驟 2-5**

## 📊 已修復的內容

我已經完成以下修復：

### 1. ✅ 移除 Google Fonts 依賴
**文件**: `app/src/app/layout.tsx`
- 移除了會導致構建失敗的 Google Fonts 引用
- 改用系統字體

### 2. ✅ 移除 package-lock.json 依賴
**文件**: `.github/workflows/deploy.yml`
- 移除了 npm cache 配置
- 改用 `npm install` 而不是 `npm ci`

### 3. ✅ 添加 Workflow 權限
**文件**: `.github/workflows/deploy.yml`
- 添加了 `permissions: contents: write`
- 允許 Actions 創建和推送到 gh-pages 分支

### 4. ✅ basePath 配置正確
**文件**: `app/next.config.js`
- basePath 設為 `/AILAWFORBEAUTY`
- assetPrefix 設為 `/AILAWFORBEAUTY`
- 適配 GitHub Pages 項目頁面

### 5. ✅ 所有數據文件完整
**目錄**: `data/rules/`
- EU、JP、CN、CA、ASEAN 所有市場的法規數據都存在
- 包含完整的禁用、限用、監測成分列表

## 🔍 本地驗證結果

```bash
✓ npm install          - 成功
✓ npm run build        - 成功
✓ 構建輸出             - 完整
✓ 所有資源文件         - 存在
✓ 數據文件             - 完整
✓ 配置文件             - 正確
```

**構建輸出**：
```
✓ Compiled successfully
✓ Generating static pages (4/4)
Route (app)                              Size     First Load JS
┌ ○ /                                    238 kB          323 kB
└ ○ /_not-found                          882 B          85.4 kB
```

## ⚠️ 關鍵注意事項

1. **必須配置倉庫權限**
   - 即使 workflow 中設置了權限
   - 倉庫設置中的 "Workflow permissions" 可能會覆蓋
   - 必須設為 "Read and write permissions"

2. **必須配置 GitHub Pages**
   - 必須在 Settings > Pages 中選擇 gh-pages 分支
   - 否則即使 workflow 成功，網站也無法訪問

3. **首次部署需要手動觸發**
   - 合併 PR 後可能不會自動觸發（如果倉庫權限還沒配置）
   - 建議手動觸發一次 workflow

## 🚀 預期結果

完成所有步驟後：

1. ✅ GitHub Actions workflow 成功運行
2. ✅ gh-pages 分支被創建
3. ✅ 靜態文件被推送到 gh-pages
4. ✅ GitHub Pages 自動部署
5. ✅ 網站可以訪問：https://willisxu.github.io/AILAWFORBEAUTY/
6. ✅ 所有功能正常工作：
   - 成分上傳
   - 多市場合規檢查
   - 風險矩陣顯示
   - PDF/CSV 匯出
   - 法規更新查看

## 📞 如果還是失敗

如果完成所有步驟後還是失敗，請提供：

1. **Actions 執行日誌**
   - 訪問：https://github.com/willisXu/AILAWFORBEAUTY/actions
   - 點擊最新的失敗 run
   - 複製完整錯誤訊息

2. **截圖**
   - Actions 權限設置的截圖
   - GitHub Pages 設置的截圖
   - Workflow 執行狀態的截圖

3. **網站訪問結果**
   - 訪問 https://willisxu.github.io/AILAWFORBEAUTY/
   - 描述看到了什麼（404 / 空白頁 / 其他錯誤）

---

## 🎓 技術說明

### 為什麼需要權限配置？

GitHub Actions 的安全模型：

1. **GITHUB_TOKEN** 是自動生成的臨時令牌
2. **預設只有讀取權限**（為了安全）
3. **peaceiris/actions-gh-pages** 需要寫入權限來：
   - 創建 gh-pages 分支
   - 推送構建產物
   - 觸發 GitHub Pages 部署

### 權限配置的兩個層級

1. **Workflow 文件層級** (`.github/workflows/deploy.yml`)
   ```yaml
   permissions:
     contents: write
   ```

2. **倉庫層級** (Settings > Actions)
   - "Workflow permissions"
   - 可以覆蓋 workflow 中的設置

**兩者都需要正確配置**，部署才能成功。

---

**現在就開始修復吧！** 🚀

快速連結：
- 合併 PR: https://github.com/willisXu/AILAWFORBEAUTY/compare/main...claude/cosmetics-compliance-audit-system-011CUyVS38cuTHs1sBC1aJQD
- Actions 設置: https://github.com/willisXu/AILAWFORBEAUTY/settings/actions
- Pages 設置: https://github.com/willisXu/AILAWFORBEAUTY/settings/pages
- 手動運行: https://github.com/willisXu/AILAWFORBEAUTY/actions/workflows/deploy.yml
