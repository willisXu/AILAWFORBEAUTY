// API Configuration

export const API_CONFIG = {
  // 法規文件上傳端點。留空時使用同源 /api/upload-regulation（僅在 Vercel 部署可用；
  // GitHub Pages 為純靜態站點，無法提供此 API）
  UPLOAD_ENDPOINT: '',
}

export const getUploadEndpoint = () => {
  return API_CONFIG.UPLOAD_ENDPOINT || '/api/upload-regulation'
}
