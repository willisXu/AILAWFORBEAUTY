# 部署指南 / Deployment Guide

## 🚀 一鍵直接更新功能設置

本指南說明如何啟用前端一鍵直接觸發更新功能（無需跳轉到 GitHub）。

---

## 📋 當前狀態

**智能觸發系統已啟用！**

系統會自動：
1. ✅ 首先嘗試通過 API 直接觸發（如果有配置）
2. ✅ 如果 API 不可用，自動回退到 GitHub 頁面
3. ✅ 全程有視覺反饋（載入動畫、成功提示）

---

## 🎯 啟用完整功能（可選）

如果想要**真正的一鍵觸發**（不跳轉 GitHub），需要部署到支持 serverless functions 的平台。

### 推薦：Vercel 部署 ⭐

**步驟**：

1. **訪問 [vercel.com](https://vercel.com) 並用 GitHub 登入**

2. **導入項目**：New Project → 選擇 `AILAWFORBEAUTY`

3. **設置環境變量**：
   ```
   GITHUB_TOKEN = ghp_xxxxxxxxxxxxx
   ```

4. **創建 GitHub Token**：
   - 訪問：https://github.com/settings/tokens/new
   - 權限：`repo` + `workflow`
   - 複製 token 到 Vercel

5. **完成！** 現在點擊按鈕會直接觸發，無需跳轉

---

## 📊 體驗對比

| 模式 | GitHub Pages | Vercel |
|------|-------------|--------|
| 點擊按鈕 | ✅ | ✅ |
| 需要跳轉 | ✅ 是 | ❌ 否 |
| 手動操作 | 需要 | 不需要 |
| 總耗時 | ~30秒 | ~5秒 |

---

**當前版本**：智能回退模式  
**完整功能**：需部署 Vercel
