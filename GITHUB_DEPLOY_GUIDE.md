# 🎯 GitHub 網頁操作部署指南

## 看不到 Actions 選項？沒關係！

如果您在 GitHub 上看不到 "Deploy to GitHub Pages" workflow，這是正常的，因為 workflow 文件還在功能分支上。

以下是**最簡單的部署方式**：

---

## 📝 方案 1：在 GitHub 網頁上手動啟用（推薦）

### 步驟 1：設置 GitHub Pages 使用分支部署

1. 前往您的 GitHub 倉庫：
   ```
   https://github.com/willisXu/AILAWFORBEAUTY
   ```

2. 點擊 **Settings**（設置）標籤

3. 在左側菜單找到 **Pages**

4. 在 "Build and deployment" 部分：
   - **Source**: 改選 `Deploy from a branch`（從分支部署）
   - **Branch**: 選擇 `claude/cosmetics-compliance-audit-system-011CUyVS38cuTHs1sBC1aJQD`
   - **Folder**: 選擇 `/docs` 或 `/ (root)`
   - 點擊 **Save**

5. 等待 2-3 分鐘，頁面上方會顯示：
   ```
   Your site is published at https://willisxu.github.io/AILAWFORBEAUTY/
   ```

---

## 📝 方案 2：創建 Pull Request 合併到 main

如果您希望使用 GitHub Actions 自動部署：

### 步驟 1：創建 Pull Request

1. 前往倉庫首頁：
   ```
   https://github.com/willisXu/AILAWFORBEAUTY
   ```

2. 點擊上方的 **Pull requests** 標籤

3. 點擊綠色的 **New pull request** 按鈕

4. 設置：
   - **base**: `main`
   - **compare**: `claude/cosmetics-compliance-audit-system-011CUyVS38cuTHs1sBC1aJQD`

5. 點擊 **Create pull request**

6. 填寫標題和說明，然後點擊 **Create pull request**

### 步驟 2：合併 Pull Request

1. 檢查 PR 頁面，確認沒有衝突

2. 點擊 **Merge pull request**

3. 點擊 **Confirm merge**

### 步驟 3：啟用 GitHub Pages (GitHub Actions)

1. 合併後，前往 **Settings** → **Pages**

2. **Source**: 選擇 `GitHub Actions`

3. 點擊 **Save**

### 步驟 4：等待自動部署

1. 前往 **Actions** 標籤

2. 等待 "Deploy to GitHub Pages" workflow 自動執行

3. 完成後（顯示綠色 ✓），訪問：
   ```
   https://willisxu.github.io/AILAWFORBEAUTY/
   ```

---

## 📝 方案 3：使用現成的靜態文件（最快）

如果您只想快速看到效果：

### 在本地建置（需要 Node.js）

1. 克隆倉庫到本地：
   ```bash
   git clone https://github.com/willisXu/AILAWFORBEAUTY.git
   cd AILAWFORBEAUTY
   git checkout claude/cosmetics-compliance-audit-system-011CUyVS38cuTHs1sBC1aJQD
   ```

2. 安裝依賴並建置：
   ```bash
   cd app
   npm install
   npm run build
   ```

3. 建置完成後，`app/out/` 目錄包含所有靜態文件

4. 手動複製 `app/out/` 的內容到 `docs/` 目錄：
   ```bash
   cd ..
   cp -r app/out/* docs/
   git add docs/
   git commit -m "feat: Add static build files"
   git push
   ```

5. 在 GitHub Settings → Pages 選擇從 `docs` 文件夾部署

---

## ✅ 推薦方案選擇

| 方案 | 難度 | 速度 | 推薦度 |
|-----|------|------|--------|
| 方案 1：分支直接部署 | ⭐ 簡單 | ⚡ 最快 (2-3分鐘) | ⭐⭐⭐⭐⭐ |
| 方案 2：PR + Actions | ⭐⭐ 中等 | ⚡⚡ 中等 (5-10分鐘) | ⭐⭐⭐⭐ |
| 方案 3：本地建置 | ⭐⭐⭐ 較難 | ⚡⚡⚡ 需要環境 | ⭐⭐⭐ |

**建議選擇方案 1** - 最簡單快速！

---

## 🎯 測試 URL

無論使用哪個方案，您的網站都會在這個 URL 上線：

```
https://willisxu.github.io/AILAWFORBEAUTY/
```

---

## 🐛 常見問題

### Q: 為什麼看不到 "Deploy from a branch" 選項？

**A**: 請確認：
1. 您有倉庫的管理員權限
2. 倉庫是 public（公開）的
3. 在 Settings → Pages 頁面

### Q: 顯示 404 錯誤

**A**: 請等待 3-5 分鐘讓 GitHub Pages 完成部署，然後刷新頁面。

### Q: 樣式錯亂或功能不正常

**A**:
1. 確認選擇了正確的分支：`claude/cosmetics-compliance-audit-system-011CUyVS38cuTHs1sBC1aJQD`
2. 清除瀏覽器緩存
3. 嘗試方案 2 或方案 3

---

## 📞 需要協助？

如果以上方案都遇到問題，請：

1. 截圖您看到的 GitHub Pages 設置頁面
2. 在 GitHub Issues 提問：
   ```
   https://github.com/willisXu/AILAWFORBEAUTY/issues/new
   ```

---

**開始部署** → 選擇上面的**方案 1**，只需要 2-3 分鐘！🚀
