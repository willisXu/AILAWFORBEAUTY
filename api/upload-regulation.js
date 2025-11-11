// API endpoint for uploading regulation files
// This serverless function receives files and triggers processing

import { Octokit } from '@octokit/rest';
import formidable from 'formidable';
import fs from 'fs';
import path from 'path';

// Disable Next.js body parser for file uploads
export const config = {
  api: {
    bodyParser: false,
  },
};

export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Parse the multipart form data
    const form = formidable({
      maxFileSize: 50 * 1024 * 1024, // 50MB limit
    });

    const [fields, files] = await new Promise((resolve, reject) => {
      form.parse(req, (err, fields, files) => {
        if (err) reject(err);
        resolve([fields, files]);
      });
    });

    // Extract parameters
    const jurisdiction = Array.isArray(fields.jurisdiction)
      ? fields.jurisdiction[0]
      : fields.jurisdiction;
    const fileType = Array.isArray(fields.fileType)
      ? fields.fileType[0]
      : (fields.fileType || 'pdf');
    const annex = Array.isArray(fields.annex)
      ? fields.annex[0]
      : fields.annex;
    const version = Array.isArray(fields.version)
      ? fields.version[0]
      : fields.version;

    // Get the uploaded file
    const uploadedFile = Array.isArray(files.file)
      ? files.file[0]
      : files.file;

    if (!uploadedFile) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    if (!jurisdiction) {
      return res.status(400).json({ error: 'Jurisdiction is required' });
    }

    // Validate jurisdiction
    const validJurisdictions = ['EU', 'JP', 'CN', 'CA', 'ASEAN'];
    if (!validJurisdictions.includes(jurisdiction)) {
      return res.status(400).json({
        error: `Invalid jurisdiction. Must be one of: ${validJurisdictions.join(', ')}`
      });
    }

    // Read file content
    const fileContent = fs.readFileSync(uploadedFile.filepath);
    const base64Content = fileContent.toString('base64');

    // Generate filename
    const timestamp = new Date().toISOString().replace(/[-:]/g, '').split('.')[0];
    const ext = path.extname(uploadedFile.originalFilename || uploadedFile.newFilename);
    const filename = annex
      ? `${timestamp}_${annex}${ext}`
      : `${timestamp}_regulation${ext}`;

    // Upload to GitHub
    const octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN,
    });

    const owner = 'willisXu';
    const repo = 'AILAWFORBEAUTY';
    const branch = process.env.GITHUB_BRANCH || 'main';
    const filePath = `data/raw/${jurisdiction}/uploads/${filename}`;

    // Check if file exists
    let sha;
    try {
      const { data } = await octokit.repos.getContent({
        owner,
        repo,
        path: filePath,
        ref: branch,
      });
      sha = data.sha;
    } catch (error) {
      // File doesn't exist, which is fine
    }

    // Create or update file
    await octokit.repos.createOrUpdateFileContents({
      owner,
      repo,
      path: filePath,
      message: `Upload regulation file: ${jurisdiction} ${annex || ''} (${timestamp})`,
      content: base64Content,
      branch,
      ...(sha && { sha }),
    });

    // Trigger processing workflow
    await octokit.actions.createWorkflowDispatch({
      owner,
      repo,
      workflow_id: 'process-uploaded-regulation.yml',
      ref: branch,
      inputs: {
        jurisdiction,
        file_type: fileType,
        annex: annex || '',
        version: version || timestamp,
        file_path: filePath,
      },
    });

    // Clean up temporary file
    fs.unlinkSync(uploadedFile.filepath);

    return res.status(200).json({
      success: true,
      message: 'File uploaded and processing triggered',
      data: {
        jurisdiction,
        filename,
        file_path: filePath,
        timestamp,
      },
    });

  } catch (error) {
    console.error('Error uploading file:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to upload file',
      message: error.message,
    });
  }
}
