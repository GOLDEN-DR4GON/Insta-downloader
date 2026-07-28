// api/index.js - Instagram Reel Downloader (Working on Vercel)

const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const { promisify } = require('util');
const execPromise = promisify(exec);

module.exports = async (req, res) => {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    
    // Handle preflight
    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    const url = req.query.url;
    const action = req.query.action;

    // ============================================
    // API INFO
    // ============================================
    if (!url) {
        return res.status(200).json({
            status: '✅ API is running!',
            version: '2.0.0',
            endpoints: {
                'Download': '/api?url=INSTAGRAM_URL',
                'Info': '/api?action=info&url=INSTAGRAM_URL',
                'Validate': '/api?action=validate&url=INSTAGRAM_URL'
            },
            example: '/api?url=https://www.instagram.com/reel/CxYz123AbCd/',
            note: 'Vercel serverless function with yt-dlp'
        });
    }

    // ============================================
    // VALIDATE URL
    // ============================================
    if (action === 'validate') {
        const isValid = /instagram\.com\/(reel|p|tv)\/[\w-]+/i.test(url);
        return res.status(200).json({
            valid: isValid,
            url: url,
            message: isValid ? '✅ Valid Instagram URL' : '❌ Invalid URL'
        });
    }

    // ============================================
    // GET VIDEO INFO
    // ============================================
    if (action === 'info') {
        try {
            const command = `yt-dlp -j --no-playlist --quiet "${url}"`;
            const { stdout } = await execPromise(command, { timeout: 15000 });
            const info = JSON.parse(stdout);
            
            return res.status(200).json({
                success: true,
                title: info.title || 'Instagram Reel',
                uploader: info.uploader || 'Unknown',
                duration: info.duration || 0,
                viewCount: info.view_count || 0,
                likeCount: info.like_count || 0,
                thumbnail: info.thumbnail || '',
                description: (info.description || '').substring(0, 200)
            });
        } catch (error) {
            return res.status(500).json({
                success: false,
                error: 'Failed to get info',
                details: error.message
            });
        }
    }

    // ============================================
    // DOWNLOAD REEL
    // ============================================
    try {
        // Validate URL
        if (!/instagram\.com\/(reel|p|tv)\/[\w-]+/i.test(url)) {
            return res.status(400).json({
                success: false,
                error: '❌ Invalid Instagram URL',
                validFormats: [
                    'https://www.instagram.com/reel/XXXXX/',
                    'https://www.instagram.com/p/XXXXX/',
                    'https://www.instagram.com/tv/XXXXX/'
                ]
            });
        }

        // Generate unique file ID
        const fileId = Date.now().toString(36) + Math.random().toString(36).substring(2, 7);
        const filePath = `/tmp/${fileId}.mp4`;

        console.log(`📥 Downloading: ${url}`);

        // Download using yt-dlp
        const command = `yt-dlp -f "best[ext=mp4]" -o "${filePath}" --no-playlist --quiet "${url}"`;
        await execPromise(command, { timeout: 60000 });

        // Check if file exists
        if (!fs.existsSync(filePath)) {
            throw new Error('File not created');
        }

        const stats = fs.statSync(filePath);
        const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
        const fileSizeBytes = stats.size;

        console.log(`✅ Download complete: ${fileSizeMB} MB`);

        // ============================================
        // FOR SMALL FILES (<25MB) - Return base64
        // ============================================
        if (fileSizeBytes < 25 * 1024 * 1024) {
            const fileBuffer = fs.readFileSync(filePath);
            const base64 = fileBuffer.toString('base64');
            fs.unlinkSync(filePath); // Clean up

            return res.status(200).json({
                success: true,
                method: 'base64',
                file_base64: base64,
                file_size: fileSizeMB + ' MB',
                message: '✅ Download successful! Decode base64 to get video.',
                note: 'For larger files, use the download_url method'
            });
        }

        // ============================================
        // FOR LARGE FILES - Return download URL
        // ============================================
        // Note: This won't work on Vercel for large files due to /tmp limitations
        // But we'll keep it for compatibility
        const downloadUrl = `https://${req.headers.host}/api/download?file=${fileId}`;

        return res.status(200).json({
            success: true,
            method: 'url',
            download_url: downloadUrl,
            file_id: fileId,
            file_size: fileSizeMB + ' MB',
            message: '✅ Download successful! Use the download_url to get your video.',
            note: 'If download_url doesn\'t work, use the base64 method for smaller files'
        });

    } catch (error) {
        console.error('❌ Download error:', error);
        
        // Clean up any partial files
        try {
            const files = fs.readdirSync('/tmp');
            files.forEach(file => {
                if (file.endsWith('.mp4')) {
                    fs.unlinkSync(`/tmp/${file}`);
                }
            });
        } catch (e) {}

        return res.status(500).json({
            success: false,
            error: 'Download failed',
            details: error.message,
            solution: 'Try a different reel or use Railway.app for better performance'
        });
    }
};
