<?php
// download.php - Serve the downloaded file

$fileId = isset($_GET['file']) ? $_GET['file'] : '';
$filePath = "/tmp/{$fileId}.mp4";

if (file_exists($filePath)) {
    header('Content-Type: video/mp4');
    header('Content-Disposition: attachment; filename="instagram_reel.mp4"');
    readfile($filePath);
    unlink($filePath); // Delete after download
} else {
    http_response_code(404);
    echo "File not found";
}
?>
