        // api/index.js
const { exec } = require('child_process');
const fs = require('fs');
const { promisify } = require('util');
const execPromise = promisify(exec);

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Content-Type', 'application/json');

    const url = req.query.url;

    if (!url) {
        return res.status(200).json({
            status: '✅ API Running on Render',
            usage: '/api?url=INSTAGRAM_URL'
        });
    }

    if (!/instagram\.com\/(reel|p|tv)\/[\w-]+/i.test(url)) {
        return res.status(400).json({ error: '❌ Invalid Instagram URL' });
    }

    try {
        const fileId = Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
        const filePath = `/tmp/${fileId}.mp4`;

        // Install yt-dlp if not available (fallback)
        await execPromise('pip3 install yt-dlp --quiet', { timeout: 30000 });

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
                    file_size: fileSizeMB + ' MB'
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
};
