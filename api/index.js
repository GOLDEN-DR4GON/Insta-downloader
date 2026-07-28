const express = require('express');
const { exec } = require('child_process');
const fs = require('fs');
const { promisify } = require('util');
const execPromise = promisify(exec);

const app = express();
const PORT = process.env.PORT || 10000;

app.get('/api', async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Content-Type', 'application/json');

    const url = req.query.url;

    if (!url) {
        return res.status(200).json({
            status: '✅ API Running on Render (Docker)',
            usage: '/api?url=INSTAGRAM_URL'
        });
    }

    if (!/instagram\.com\/(reel|p|tv)\/[\w-]+/i.test(url)) {
        return res.status(400).json({ error: '❌ Invalid URL' });
    }

    try {
        const fileId = Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
        const filePath = `/tmp/${fileId}.mp4`;

        await execPromise(`yt-dlp -f "best[ext=mp4]" -o "${filePath}" --no-playlist --quiet "${url}"`, { timeout: 60000 });

        if (fs.existsSync(filePath)) {
            const content = fs.readFileSync(filePath);
            fs.unlinkSync(filePath);
            return res.status(200).json({
                success: true,
                file_base64: content.toString('base64'),
                message: '✅ Download successful!'
            });
        }

        return res.status(500).json({ error: 'Download failed' });

    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
});

app.get('/', (req, res) => {
    res.json({
        name: 'Instagram Reel Downloader',
        version: '1.0.0',
        endpoints: {
            download: '/api?url=INSTAGRAM_URL'
        }
    });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`✅ Server running on port ${PORT}`);
});
