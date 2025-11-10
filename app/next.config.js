/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  basePath: process.env.NODE_ENV === 'production' ? '/AILAWFORBEAUTY' : '',
  assetPrefix: process.env.NODE_ENV === 'production' ? '/AILAWFORBEAUTY/' : '',
  images: {
    unoptimized: true
  },
  trailingSlash: true,
}

module.exports = nextConfig
