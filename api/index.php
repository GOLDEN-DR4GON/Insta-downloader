<?php
// api/index.php - Instagram Reel Downloader for Vercel

header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json');

// Get URL from query string
$url = isset($_GET['url']) ? trim($_GET['url']) : '';
$action = isset($_GET['action']) ? $_GET['action'] : '';

// If no URL, show API info
if (empty($url)) {
    echo json_encode([
        'status' => '✅ API Running on Vercel',
        'version' => '1.0.0',
        'endpoints' => [
            'download' => '/api?url=INSTAGRAM_URL',
            'info' => '/api?action=info&url=INSTAGRAM_URL',
            'validate' => '/api?action=validate&url=INSTAGRAM_URL'
        ],
        'example' => '/api?url=https://www.instagram.com/reel/CxYz123AbCd/'
    ], JSON_PRETTY_PRINT);
    exit();
}

// Validate URL
if ($action === 'validate') {
    $isValid = preg_match('/instagram\.com\/(reel|p|tv)\/[\w-]+/i', $url);
    echo json_encode([
        'valid' => (bool)$isValid,
        'url' => $url,
        'message' => $isValid ? '✅ Valid Instagram URL' : '❌ Invalid Instagram URL'
    ], JSON_PRETTY_PRINT);
    exit();
}

// Get video info
if ($action === 'info') {
    if (!preg_match('/instagram\.com\/(reel|p|tv)\/[\w-]+/i', $url)) {
        echo json_encode(['error' => 'Invalid Instagram URL']);
        exit();
    }
    
    $command = sprintf('yt-dlp -j --no-playlist --quiet %s 2>&1', escapeshellarg($url));
    $output = shell_exec($command);
    
    if ($output) {
        $info = json_decode($output, true);
        if ($info) {
            echo json_encode([
                'success' => true,
                'title' => $info['title'] ?? 'Instagram Reel',
                'uploader' => $info['uploader'] ?? 'Unknown',
                'duration' => $info['duration'] ?? 0,
                'thumbnail' => $info['thumbnail'] ?? ''
            ], JSON_PRETTY_PRINT);
            exit();
        }
    }
    
    echo json_encode(['error' => 'Could not fetch video info']);
    exit();
}

// ============================================
// DOWNLOAD REEL (Main functionality)
// ============================================
if (!preg_match('/instagram\.com\/(reel|p|tv)\/[\w-]+/i', $url)) {
    echo json_encode([
        'error' => '❌ Invalid Instagram URL',
        'formats' => [
            'https://www.instagram.com/reel/XXXXX/',
            'https://www.instagram.com/p/XXXXX/'
        ]
    ]);
    exit();
}

// Generate unique file ID
$fileId = uniqid() . '_' . time();
$outputFile = "/tmp/{$fileId}.mp4";

// Download using yt-dlp
$command = sprintf(
    'yt-dlp -f "best[ext=mp4]" -o "%s" --no-playlist --quiet %s 2>&1',
    $outputFile,
    escapeshellarg($url)
);

exec($command, $output, $returnCode);

// Check if download was successful
if ($returnCode === 0 && file_exists($outputFile)) {
    $fileSize = filesize($outputFile);
    $fileSizeMB = round($fileSize / (1024 * 1024), 2);
    
    // For small files, return base64 encoded
    if ($fileSize < 25 * 1024 * 1024) { // Under 25MB
        $content = base64_encode(file_get_contents($outputFile));
        unlink($outputFile); // Clean up
        
        echo json_encode([
            'success' => true,
            'file_base64' => $content,
            'file_size' => $fileSizeMB . ' MB',
            'message' => '✅ Download successful! Decode base64 to get video.'
        ], JSON_PRETTY_PRINT);
    } else {
        // For larger files, return download URL
        $downloadUrl = "https://" . $_SERVER['HTTP_HOST'] . "/api/download.php?file={$fileId}";
        
        echo json_encode([
            'success' => true,
            'download_url' => $downloadUrl,
            'file_id' => $fileId,
            'file_size' => $fileSizeMB . ' MB',
            'message' => '✅ Download successful! Use the download_url to get your video.'
        ], JSON_PRETTY_PRINT);
    }
} else {
    echo json_encode([
        'error' => '❌ Download failed',
        'details' => implode("\n", $output)
    ]);
}
?>
