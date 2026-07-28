<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json');

$url = $_GET['url'] ?? '';

if (!$url) {
    die(json_encode([
        'status' => 'ready',
        'usage' => '/api?url=INSTAGRAM_URL'
    ]));
}

if (!preg_match('/instagram\.com\/(reel|p|tv)\/[\w-]+/i', $url)) {
    die(json_encode(['error' => 'Invalid Instagram URL']));
}

$fileId = uniqid();
$filePath = "/tmp/{$fileId}.mp4";

exec("yt-dlp -f best[ext=mp4] -o $filePath --no-playlist --quiet " . escapeshellarg($url), $out, $code);

if ($code === 0 && file_exists($filePath)) {
    $size = round(filesize($filePath) / 1048576, 2);
    $content = base64_encode(file_get_contents($filePath));
    unlink($filePath);
    
    die(json_encode([
        'success' => true,
        'file_base64' => $content,
        'size' => $size . ' MB'
    ]));
}

die(json_encode(['error' => 'Download failed']));
?>
