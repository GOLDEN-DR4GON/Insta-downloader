<?php
// api.php - Instagram Reel Downloader

header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json');

// Get URL from query
$url = isset($_GET['url']) ? trim($_GET['url']) : '';

// If no URL, show usage
if (empty($url)) {
    die(json_encode([
        'status' => 'ready',
        'usage' => '/api.php?url=INSTAGRAM_REEL_URL',
        'example' => '/api.php?url=https://www.instagram.com/reel/CxYz123AbCd/'
    ]));
}

// Validate Instagram URL
if (!preg_match('/instagram\.com\/(reel|p|tv)\/[\w-]+/i', $url)) {
    die(json_encode(['error' => 'Invalid Instagram URL']));
}

// Download using yt-dlp
$fileId = uniqid();
$outputFile = "/tmp/{$fileId}.mp4";

$command = sprintf(
    'yt-dlp -f "best[ext=mp4]" -o "%s" --no-playlist --quiet %s 2>&1',
    $outputFile,
    escapeshellarg($url)
);

exec($command, $output, $returnCode);

// Check if download succeeded
if ($returnCode === 0 && file_exists($outputFile)) {
    $size = round(filesize($outputFile) / 1048576, 2);
    
    // Return download URL
    echo json_encode([
        'success' => true,
        'download_url' => "https://" . $_SERVER['HTTP_HOST'] . "/download.php?file={$fileId}",
        'file_id' => $fileId,
        'file_size' => $size . ' MB'
    ]);
} else {
    echo json_encode([
        'success' => false,
        'error' => 'Download failed'
    ]);
}
?>
