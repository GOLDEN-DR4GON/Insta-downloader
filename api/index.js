// api/index.js - Instagram Reel Downloader (Vercel version)
module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Content-Type', 'application/json');

    const url = req.query.url;

    // Show API info
    if (!url) {
        return res.status(200).json({
            status: '✅ API Running on Vercel',
            usage: '/api?url=INSTAGRAM_URL',
            example: '/api?url=https://www.instagram.com/reel/CxYz123AbCd/'
        });
    }

    // Validate URL
    if (!/instagram\.com\/(reel|p|tv)\/[\w-]+/i.test(url)) {
        return res.status(400).json({ error: '❌ Invalid Instagram URL' });
    }

    try {
        // Use public API to get video
        const response = await fetch(`https://api.instagram.com/oembed?url=${encodeURIComponent(url)}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch video info');
        }

        const data = await response.json();

        return res.status(200).json({
            success: true,
            title: data.title || 'Instagram Reel',
            thumbnail: data.thumbnail_url || '',
            author: data.author_name || 'Unknown',
            note: 'Vercel cannot download videos directly. For actual downloads, use Railway.app or a VPS.'
        });

    } catch (error) {
        console.error('Error:', error);
        return res.status(500).json({
            error: 'Failed to process URL',
            details: error.message
        });
    }
};
