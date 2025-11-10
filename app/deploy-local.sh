#!/bin/bash
set -e

echo "🚀 開始本地建置 Starting local build..."

# 進入 app 目錄
cd app

# 安裝依賴（如果需要）
if [ ! -d "node_modules" ]; then
    echo "📦 安裝依賴 Installing dependencies..."
    npm install
fi

# 建置靜態網站
echo "🔨 建置靜態網站 Building static site..."
npm run build

echo "✅ 建置完成！Build completed!"
echo ""
echo "📁 輸出目錄 Output directory: app/out/"
echo ""
echo "下一步 Next steps:"
echo "1. 將 app/out/ 目錄的內容複製到 GitHub Pages 分支"
echo "2. 或使用 GitHub Desktop 提交並推送"
echo ""
