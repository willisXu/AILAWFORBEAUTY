// Cloudflare Worker - 直接觸發 GitHub Actions
// 部署後提供一個公開 URL，前端可以直接調用

export default {
  async fetch(request, env) {
    // 處理 CORS
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        }
      });
    }

    // 只允許 POST 請求
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    try {
      // 觸發 GitHub Actions repository_dispatch
      const response = await fetch(
        'https://api.github.com/repos/willisXu/AILAWFORBEAUTY/dispatches',
        {
          method: 'POST',
          headers: {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': `token ${env.GITHUB_TOKEN}`,
            'Content-Type': 'application/json',
            'User-Agent': 'Cloudflare-Worker',
          },
          body: JSON.stringify({
            event_type: 'trigger-fetch',
            client_payload: {
              triggered_by: 'web_ui',
              timestamp: new Date().toISOString(),
            },
          }),
        }
      );

      if (response.ok || response.status === 204) {
        return new Response(JSON.stringify({
          success: true,
          message: 'Workflow triggered successfully',
          timestamp: new Date().toISOString(),
        }), {
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          }
        });
      } else {
        throw new Error(`GitHub API error: ${response.status}`);
      }
    } catch (error) {
      return new Response(JSON.stringify({
        success: false,
        error: error.message,
      }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        }
      });
    }
  }
};
