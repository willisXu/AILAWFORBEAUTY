// API Configuration
// 配置您的 Cloudflare Worker URL 或其他 serverless endpoint

export const API_CONFIG = {
  // 方案 1: Cloudflare Worker (推薦，完全免費)
  // 部署後將 Worker URL 填入這裡
  // 例如: https://trigger-regulation-update.your-name.workers.dev
  TRIGGER_ENDPOINT: process.env.NEXT_PUBLIC_TRIGGER_ENDPOINT || '',

  // 方案 2: Vercel Serverless Function
  // 部署到 Vercel 後會自動使用 /api/trigger-update

  // 回退選項: GitHub 手動觸發頁面
  GITHUB_WORKFLOW_URL: 'https://github.com/willisXu/AILAWFORBEAUTY/actions/workflows/fetch-regulations.yml'
}

// 檢查是否配置了直接觸發端點
export const hasDirectTrigger = () => {
  return !!API_CONFIG.TRIGGER_ENDPOINT && API_CONFIG.TRIGGER_ENDPOINT !== ''
}
