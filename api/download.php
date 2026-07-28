<?php
// api/download.php - Serve downloaded file

$fileId = isset($_GET['file']) ? $_GET['file'] : '';
$filePath = "/tmp/{$fileId}.mp4";

if (file_exists($filePath)) {
    header('Content-Type: video/mp4');
    header('Content-Disposition: attachment; filename="instagram_reel.mp4"');
    header('Content-Length: ' . filesize($filePath));
    readfile($filePath);
    unlink($filePath); // Delete after download
    exit();
} else {
    http_response_code(404);
    echo "File not found or expired";
}
?>
