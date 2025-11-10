/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  // 移除 basePath，讓 GitHub Pages 自動處理
  images: {
    unoptimized: true
  },
  trailingSlash: true,
}

module.exports = nextConfig
