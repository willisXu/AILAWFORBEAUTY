// API endpoint for triggering regulation updates
// This can be deployed as a Vercel/Netlify serverless function

export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Trigger GitHub Actions workflow using repository_dispatch
    const response = await fetch(
      'https://api.github.com/repos/willisXu/AILAWFORBEAUTY/dispatches',
      {
        method: 'POST',
        headers: {
          'Accept': 'application/vnd.github.v3+json',
          'Authorization': `token ${process.env.GITHUB_TOKEN}`,
          'Content-Type': 'application/json',
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
      return res.status(200).json({
        success: true,
        message: 'Workflow triggered successfully',
        timestamp: new Date().toISOString(),
      });
    } else {
      throw new Error(`GitHub API returned status ${response.status}`);
    }
  } catch (error) {
    console.error('Error triggering workflow:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to trigger workflow',
      message: error.message,
    });
  }
}
