// api/index.js - Instagram Reel Downloader (with full path)
const express = require('express');
const { exec } = require('child_process');
const fs = require('fs');
const { promisify } = require('util');
const execPromise = promisify(exec);

const app = express();
const PORT = process.env.PORT || 10000;

app.use(express.json());

// Helper to check if yt-dlp exists
async function checkYtDlp() {
    try {
        await execPromise('python3 -c "import yt_dlp"', { timeout: 5000 });
        return true;
    } catch {
        try {
            await execPromise('which yt-dlp', { timeout: 5000 });
            return true;
        } catch {
            return false;
        }
    }
}

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
        // Check if yt-dlp is available
        const hasYtDlp = await checkYtDlp();
        if (!hasYtDlp) {
            return res.status(500).json({
                error: 'yt-dlp not installed',
                fix: 'Run: pip3 install yt-dlp',
                note: 'Check Render build logs for errors'
            });
        }

        const fileId = Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
        const filePath = `/tmp/${fileId}.mp4`;

        console.log(`📥 Downloading: ${url}`);

        // Use python3 with full path
        const command = `python3 -m yt_dlp -f "best[ext=mp4]" -o "${filePath}" --no-playlist --quiet "${url}"`;
        console.log(`Running: ${command}`);

        const { stdout, stderr } = await execPromise(command, { timeout: 60000 });

        if (stderr && !stderr.includes('WARNING')) {
            console.error('stderr:', stderr);
        }

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

        return res.status(500).json({ 
            error: 'Download failed',
            details: stderr || 'File not created'
        });

    } catch (error) {
        console.error('Error:', error);
        return res.status(500).json({ 
            error: 'Download failed',
            details: error.message
        });
    }
});

app.get('/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

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

app.listen(PORT, '0.0.0.0', () => {
    console.log(`✅ Server running on port ${PORT}`);
    checkYtDlp().then(has => {
        console.log(`yt-dlp available: ${has ? '✅' : '❌'}`);
    });
});
