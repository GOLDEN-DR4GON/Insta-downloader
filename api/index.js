// api/index.js - Full server for Render
const express = require('express');
const { exec } = require('child_process');
const fs = require('fs');
const { promisify } = require('util');
const execPromise = promisify(exec);

const app = express();
const PORT = process.env.PORT || 10000;

// Middleware
app.use(express.json());

// API endpoint
app.get('/api', async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Content-Type', 'application/json');

    const url = req.query.url;

    if (!url) {
        return res.status(200).json({
            status: '✅ API Running on Render',
            usage: '/api?url=INSTAGRAM_URL',
            example: '/api?url=https://www.instagram.com/reel/CxYz123AbCd/'
        });
    }

    if (!/instagram\.com\/(reel|p|tv)\/[\w-]+/i.test(url)) {
        return res.status(400).json({ error: '❌ Invalid Instagram URL' });
    }

    try {
        const fileId = Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
        const filePath = `/tmp/${fileId}.mp4`;

        console.log(`📥 Downloading: ${url}`);

        const command = `yt-dlp -f "best[ext=mp4]" -o "${filePath}" --no-playlist --quiet "${url}"`;
        await execPromise(command, { timeout: 60000 });

        if (fs.existsSync(filePath)) {
            const stats = fs.statSync(filePath);
            const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);

            if (stats.size < 25 * 1024 * 1024) {
                const content = fs.readFileSync(filePath);
                fs.unlinkSync(filePath);
                return res.status(200).json({
                    success: true,
                    file_base64: content.toString('base64'),
                    file_size: fileSizeMB + ' MB',
                    message: '✅ Download successful!'
                });
            }

            return res.status(200).json({
                success: true,
                file_size: fileSizeMB + ' MB',
                message: 'File too large for base64. Use a VPS for large files.'
            });
        }

        return res.status(500).json({ error: 'Download failed' });

    } catch (error) {
        console.error('Error:', error);
        return res.status(500).json({ 
            error: 'Download failed',
            details: error.message
        });
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Root endpoint
app.get('/', (req, res) => {
    res.json({
        name: 'Instagram Reel Downloader',
        version: '2.0.0',
        endpoints: {
            download: '/api?url=INSTAGRAM_URL',
            health: '/health'
        }
    });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`✅ Server running on port ${PORT}`);
});
