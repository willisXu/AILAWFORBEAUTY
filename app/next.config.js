/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  // GitHub Pages 項目頁面需要 basePath
  basePath: '/AILAWFORBEAUTY',
  // assetPrefix 確保所有資源正確載入
  assetPrefix: '/AILAWFORBEAUTY/',
  images: {
    unoptimized: true
  },
  trailingSlash: true,
}

module.exports = nextConfig
