// api/download.js - Serve downloaded file

const fs = require('fs');

module.exports = async (req, res) => {
    const fileId = req.query.file;
    
    if (!fileId) {
        return res.status(400).json({ error: 'File ID required' });
    }

    const filePath = `/tmp/${fileId}.mp4`;

    if (!fs.existsSync(filePath)) {
        return res.status(404).json({ 
            error: 'File not found or expired',
            note: 'Files are temporary and deleted after download'
        });
    }

    const stats = fs.statSync(filePath);
    
    res.setHeader('Content-Type', 'video/mp4');
    res.setHeader('Content-Disposition', `attachment; filename="instagram_reel_${fileId}.mp4"`);
    res.setHeader('Content-Length', stats.size);

    const stream = fs.createReadStream(filePath);
    stream.pipe(res);

    // Delete file after download
    stream.on('end', () => {
        try {
            fs.unlinkSync(filePath);
            console.log(`🗑️ Deleted: ${filePath}`);
        } catch (e) {}
    });
};
