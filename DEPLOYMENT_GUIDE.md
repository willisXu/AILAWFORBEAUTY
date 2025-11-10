# 部署指南 Deployment Guide

## 🚀 GitHub Pages 部署步驟

### 步驟 1：啟用 GitHub Pages

1. 前往您的 GitHub 倉庫：
   ```
   https://github.com/willisXu/AILAWFORBEAUTY
   ```

2. 點擊 **Settings** (設置) 標籤

3. 在左側菜單找到 **Pages**

4. 在 "Build and deployment" 部分：
   - **Source**: 選擇 `GitHub Actions`
   - 點擊 **Save** (保存)

### 步驟 2：觸發首次部署

有兩種方式觸發部署：

#### 方式 A：自動觸發（推薦）

1. 合併 PR 或直接推送到 main 分支會自動觸發部署

2. 或者修改 `app/` 目錄下的任何文件並推送

#### 方式 B：手動觸發

1. 前往 **Actions** 標籤

2. 選擇 **Deploy to GitHub Pages** workflow

3. 點擊 **Run workflow** 按鈕

4. 選擇分支（建議使用 main）

5. 點擊綠色的 **Run workflow** 按鈕

### 步驟 3：等待部署完成

1. 在 **Actions** 標籤下查看部署進度

2. 部署通常需要 2-5 分鐘

3. 成功後會顯示綠色的 ✓ 標記

### 步驟 4：訪問您的網站

部署完成後，您的網站將可在以下 URL 訪問：

```
https://willisxu.github.io/AILAWFORBEAUTY/
```

## 📱 測試 URL

### 生產環境 Production

```
https://willisxu.github.io/AILAWFORBEAUTY/
```

### 主要功能頁面

- **首頁（成分比對）**: https://willisxu.github.io/AILAWFORBEAUTY/
- **法規更新中心**: https://willisxu.github.io/AILAWFORBEAUTY/ (切換到 "法規更新" 標籤)

## 🧪 測試清單

### 基本功能測試

- [ ] 網站正常加載
- [ ] 選擇產品類型
- [ ] 選擇目標市場（EU, JP, CN, CA, ASEAN）
- [ ] 上傳測試 CSV 檔案
- [ ] 查看合規矩陣結果
- [ ] 匯出 CSV 報告
- [ ] 匯出 PDF 報告
- [ ] 切換到法規更新標籤
- [ ] 多語言顯示正常（繁中/英文）

### 測試用 CSV 檔案

創建一個測試檔案 `test_ingredients.csv`：

```csv
ingredient_name,concentration,role
Aqua,75.5,Solvent
Glycerin,5.0,Humectant
Salicylic Acid,1.5,Exfoliant
Benzoic Acid,0.5,Preservative
Formaldehyde,0.1,Preservative
Hydroquinone,0.2,Skin lightening
```

預期結果：
- Aqua, Glycerin: ✓ 合規（所有市場）
- Salicylic Acid: ⚠ 限用-合規（需檢查產品類型）
- Benzoic Acid: ✓ 合規（作為防腐劑）
- Formaldehyde: ⊗ 禁用（大多數市場）
- Hydroquinone: ⊗ 禁用（大多數市場）

## 🔧 故障排除

### 問題：GitHub Pages 顯示 404

**解決方案：**
1. 確認 GitHub Pages 已啟用
2. 檢查 Settings → Pages → Source 是否設為 "GitHub Actions"
3. 確認部署 workflow 已成功執行
4. 等待 5-10 分鐘讓 DNS 生效

### 問題：網站樣式錯亂

**解決方案：**
1. 清除瀏覽器緩存
2. 檢查 `next.config.js` 中的 `basePath` 設置
3. 確認 `.nojekyll` 文件存在

### 問題：無法載入法規資料

**解決方案：**
1. 確認 `data/rules/` 目錄下有各市場的 `latest.json` 文件
2. 檢查瀏覽器控制台是否有錯誤訊息
3. 確認 GitHub Pages 部署了完整的 `data/` 目錄

### 問題：上傳檔案後沒有反應

**解決方案：**
1. 檢查瀏覽器控制台錯誤
2. 確認檔案格式正確（CSV 或 Excel）
3. 確認檔案包含必要的 `ingredient_name` 欄位
4. 嘗試使用上面提供的測試 CSV

## 📊 監控部署狀態

### 查看部署歷史

1. 前往 **Actions** 標籤
2. 查看 **Deploy to GitHub Pages** workflow
3. 點擊任一執行查看詳細日誌

### 查看當前部署狀態

1. 前往 **Settings** → **Pages**
2. 查看 "Your site is live at" 訊息
3. 確認顯示綠色的 ✓ 標記

## 🔄 更新部署

### 自動更新

每當您推送到 main 分支且修改了以下目錄時，會自動觸發重新部署：
- `app/` - 前端代碼
- `data/` - 法規資料
- `.github/workflows/deploy-pages.yml` - 部署配置

### 法規資料更新

法規資料會每週一自動更新（通過 GitHub Actions），或者您可以：

1. 前往 **Actions** 標籤
2. 選擇 **Fetch Regulations** workflow
3. 點擊 **Run workflow**
4. 等待資料更新完成
5. 部署會自動觸發

## 📝 下一步

部署成功後，您可以：

1. ✅ 分享測試 URL 給團隊成員
2. ✅ 上傳真實的產品配方進行測試
3. ✅ 設定自動法規更新（已配置每週一執行）
4. ✅ 自定義前端樣式和品牌
5. ✅ 添加自定義網域（可選）

## 🎯 重要提醒

- ⚠️ 所有比對在瀏覽器端完成，不會上傳資料
- ⚠️ 法規資料僅供參考，實際應用請諮詢專業法規顧問
- ⚠️ 建議定期檢查法規更新
- ⚠️ 測試報告可能包含敏感配方資訊，請妥善保管

## 📧 支援

如有問題，請在 GitHub 開啟 Issue：
https://github.com/willisXu/AILAWFORBEAUTY/issues

---

**部署時間**: 約 2-5 分鐘
**預計網址**: https://willisxu.github.io/AILAWFORBEAUTY/
**狀態檢查**: https://github.com/willisXu/AILAWFORBEAUTY/actions
