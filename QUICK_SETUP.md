# ⚡ 5分鐘快速設置 - 啟用一鍵直接觸發

## 🎯 目標

點擊「立即更新」按鈕後，**直接觸發爬蟲**，不跳轉到 GitHub！

---

## 📋 方案選擇（選一個即可）

### 🌟 方案 A: Cloudflare Workers（推薦，100%免費）

**優點**：
- ✅ 完全免費（每天 100,000 次請求）
- ✅ 全球 CDN 加速
- ✅ 5 分鐘完成設置
- ✅ 無需信用卡

**步驟**：

#### 1. 註冊 Cloudflare 帳號
訪問：https://dash.cloudflare.com/sign-up
（使用郵箱註冊，免費）

#### 2. 創建 Worker

1. 登入後，點擊左側 **"Workers & Pages"**
2. 點擊 **"Create application"**
3. 選擇 **"Create Worker"**
4. 名稱輸入：`trigger-regulation-update`
5. 點擊 **"Deploy"**

#### 3. 編輯 Worker 代碼

1. 點擊 **"Edit code"**
2. 刪除所有現有代碼
3. 複製 `cloudflare-worker.js` 的內容並貼上
4. 點擊 **"Save and Deploy"**

#### 4. 設置環境變量

1. 返回 Worker 頁面
2. 點擊 **"Settings"** → **"Variables"**
3. 點擊 **"Add variable"**
4. 添加：
   ```
   Variable name: GITHUB_TOKEN
   Value: (見下方如何獲取)
   ```
5. 點擊 **"Encrypt"**（重要！）
6. 點擊 **"Save"**

#### 5. 獲取 GitHub Token

1. 訪問：https://github.com/settings/tokens/new
2. 名稱：`Cloudflare Worker Trigger`
3. 勾選權限：
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
4. 點擊 **"Generate token"**
5. **複製 token**（只會顯示一次！）
6. 貼到上面的 Cloudflare 環境變量中

#### 6. 獲取 Worker URL

Worker 頁面頂部會顯示 URL，類似：
```
https://trigger-regulation-update.your-name.workers.dev
```

複製這個 URL！

#### 7. 配置前端

編輯文件：`app/src/config/api.ts`

找到這一行：
```typescript
TRIGGER_ENDPOINT: process.env.NEXT_PUBLIC_TRIGGER_ENDPOINT || '',
```

改為：
```typescript
TRIGGER_ENDPOINT: 'https://trigger-regulation-update.your-name.workers.dev',
```

#### 8. 提交並部署

```bash
git add app/src/config/api.ts
git commit -m "feat: Configure direct trigger endpoint"
git push
```

#### 9. 完成！🎉

等待 GitHub Pages 部署完成（約 2-3 分鐘），然後訪問網站測試：

1. 點擊「🚀 立即更新」
2. 看到「✅ 已觸發」
3. **沒有跳轉**，直接成功！

---

### 🔷 方案 B: Vercel（也是免費）

如果您更喜歡 Vercel：

#### 1. 訪問 Vercel
https://vercel.com （用 GitHub 登入）

#### 2. 導入項目
- New Project → 選擇 `AILAWFORBEAUTY`

#### 3. 設置環境變量
在 Project Settings 添加：
```
GITHUB_TOKEN = ghp_xxxxx（您的 token）
```

#### 4. 完成！
Vercel 會自動使用 `api/trigger-update.js`

---

## 🧪 測試是否成功

### 檢查清單：

1. **打開網站**
2. **打開瀏覽器開發者工具**（F12）
3. **切換到 Console 標籤**
4. **點擊「🚀 立即更新」按鈕**
5. **查看 Console 輸出**

#### 成功的輸出：
```
Attempting to trigger via: https://trigger-regulation-update.xxx.workers.dev
✅ Workflow triggered successfully!
```

#### 失敗的輸出（需要配置）：
```
⚠️ Direct trigger not configured
```

---

## 🔧 故障排除

### 問題：點擊後顯示「尚未配置」

**原因**：`api.ts` 中的 `TRIGGER_ENDPOINT` 沒有設置

**解決**：
1. 檢查 `app/src/config/api.ts`
2. 確認 URL 已填入
3. 重新部署

### 問題：顯示「Trigger failed」

**原因**：GitHub Token 權限不足或過期

**解決**：
1. 重新生成 GitHub Token
2. 確認勾選了 `repo` 和 `workflow` 權限
3. 更新 Cloudflare Worker 環境變量

### 問題：Worker 返回 500 錯誤

**原因**：環境變量未設置

**解決**：
1. 檢查 Cloudflare Dashboard
2. Settings → Variables → 確認 `GITHUB_TOKEN` 存在
3. 確認點擊了 "Encrypt"

---

## 📊 對比：設置前 vs 設置後

### 設置前（當前狀態）
```
點擊按鈕 → 跳轉 GitHub → 手動點擊 → 等待
總耗時：~30-60秒
```

### 設置後（目標狀態）
```
點擊按鈕 → 看到「✅ 已觸發」→ 等待數據更新
總耗時：~3-5秒
無需跳轉！✨
```

---

## 💡 安全提示

1. ✅ GitHub Token 加密存儲在 Cloudflare
2. ✅ Token 不會暴露在前端
3. ✅ Worker URL 是公開的，但只能觸發特定 workflow
4. ✅ 可隨時撤銷 token

---

## 🎁 額外好處

配置完成後，您還可以：
- 📱 在手機上直接觸發
- 🔗 分享觸發功能給團隊成員
- 📊 在 Cloudflare 查看使用統計
- ⚡ 享受全球 CDN 加速

---

## 🆘 需要幫助？

如果遇到問題：
1. 查看瀏覽器 Console（F12）的錯誤信息
2. 檢查 Cloudflare Worker 的日誌
3. 確認 GitHub Token 權限正確

---

**預計設置時間**：5-10 分鐘
**完成後體驗**：⭐⭐⭐⭐⭐

立即開始設置，享受一鍵觸發的便利！🚀
