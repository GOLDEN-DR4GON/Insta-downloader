from flask import Flask, request, jsonify, send_file
import subprocess
import os
import base64
import time
import re
import io
import json
import tempfile
import shutil
import requests

app = Flask(__name__)

# Ensure yt-dlp is installed and updated
def ensure_ytdlp():
    try:
        # Check if yt-dlp is installed
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
        # Try to update yt-dlp
        subprocess.run(['yt-dlp', '-U'], capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Install yt-dlp if not found
        subprocess.run(['pip', 'install', '--upgrade', 'yt-dlp'], check=True)

# Try different methods to download Instagram content
def download_instagram_video(url, output_path):
    methods = [
        # Method 1: Standard yt-dlp with cookies
        ['yt-dlp', '-f', 'best[ext=mp4]', '-o', output_path, '--no-playlist', '--quiet', 
         '--no-check-certificate', '--no-warnings', '--ignore-errors', url],
        
        # Method 2: yt-dlp with user-agent
        ['yt-dlp', '-f', 'best[ext=mp4]', '-o', output_path, '--no-playlist', '--quiet',
         '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
         '--no-check-certificate', '--ignore-errors', url],
        
        # Method 3: Try without format specification
        ['yt-dlp', '-o', output_path, '--no-playlist', '--quiet', '--no-check-certificate',
         '--ignore-errors', url],
        
        # Method 4: Use cookies from browser (if available)
        ['yt-dlp', '-f', 'best[ext=mp4]', '-o', output_path, '--no-playlist', '--quiet',
         '--cookies-from-browser', 'chrome', '--no-check-certificate', '--ignore-errors', url]
    ]
    
    for i, cmd in enumerate(methods):
        try:
            print(f"Attempting method {i+1}: {' '.join(cmd)}")
            result = subprocess.run(cmd, timeout=120, capture_output=True, text=True)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"Method {i+1} succeeded! File size: {os.path.getsize(output_path)} bytes")
                return True, "Download successful"
            else:
                print(f"Method {i+1} failed: {result.stderr}")
        except Exception as e:
            print(f"Method {i+1} error: {str(e)}")
            continue
    
    return False, "All download methods failed"

@app.route('/api', methods=['GET'])
def download_reel():
    url = request.args.get('url')
    download = request.args.get('download', 'false').lower() == 'true'
    
    if not url:
        return jsonify({
            'status': '✅ API Running',
            'usage': '/api?url=REEL_URL',
            'auto_download': '/api?url=REEL_URL&download=true',
            'version': '2.0.0'
        })
    
    # More comprehensive URL validation
    instagram_patterns = [
        r'instagram\.com/(reel|p|tv)/[\w-]+',
        r'instagram\.com/[\w.]+\?igsh=[\w]+',
        r'www\.instagram\.com/(reel|p|tv)/[\w-]+',
        r'instagram\.com/share/[\w-]+'
    ]
    
    url_valid = False
    for pattern in instagram_patterns:
        if re.search(pattern, url):
            url_valid = True
            break
    
    if not url_valid:
        return jsonify({'error': '❌ Invalid Instagram URL'}), 400
    
    # Ensure yt-dlp is available
    ensure_ytdlp()
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    file_id = str(int(time.time())) + '_' + os.urandom(4).hex()
    file_path = os.path.join(temp_dir, f'{file_id}.mp4')
    
    try:
        # Try downloading with multiple methods
        success, message = download_instagram_video(url, file_path)
        
        if success and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            # If download=true, send file directly
            if download:
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=f'reel_{file_id}.mp4',
                    mimetype='video/mp4'
                )
            
            # Otherwise return base64
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            shutil.rmtree(temp_dir)
            return jsonify({
                'success': True,
                'file_base64': content,
                'message': '✅ Download successful!',
                'file_size': os.path.getsize(file_path),
                'direct_download': f'/api?url={url}&download=true',
                'simple_download': f'/download?url={url}'
            })
        
        shutil.rmtree(temp_dir)
        return jsonify({
            'error': 'Download failed',
            'details': message,
            'suggestions': [
                'Make sure the URL is correct and the reel is public',
                'Try using the direct download endpoint: /download?url=URL',
                'Some Instagram reels may have region restrictions'
            ]
        }), 500
        
    except Exception as e:
        shutil.rmtree(temp_dir)
        return jsonify({
            'error': str(e),
            'message': 'Download failed due to an unexpected error',
            'debug': 'Check if yt-dlp is properly installed'
        }), 500

@app.route('/download', methods=['GET'])
def download_direct():
    """Direct download endpoint - even simpler!"""
    url = request.args.get('url')
    
    if not url:
        return jsonify({'error': 'URL required', 'usage': '/download?url=REEL_URL'}), 400
    
    # Validate URL
    instagram_patterns = [
        r'instagram\.com/(reel|p|tv)/[\w-]+',
        r'instagram\.com/[\w.]+\?igsh=[\w]+',
        r'www\.instagram\.com/(reel|p|tv)/[\w-]+'
    ]
    
    url_valid = False
    for pattern in instagram_patterns:
        if re.search(pattern, url):
            url_valid = True
            break
    
    if not url_valid:
        return jsonify({'error': '❌ Invalid Instagram URL'}), 400
    
    ensure_ytdlp()
    temp_dir = tempfile.mkdtemp()
    file_id = str(int(time.time())) + '_' + os.urandom(4).hex()
    file_path = os.path.join(temp_dir, f'{file_id}.mp4')
    
    try:
        success, message = download_instagram_video(url, file_path)
        
        if success and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return send_file(
                file_path,
                as_attachment=True,
                download_name=f'reel_{file_id}.mp4',
                mimetype='video/mp4'
            )
        
        shutil.rmtree(temp_dir)
        return jsonify({
            'error': 'Download failed',
            'details': message,
            'suggestions': [
                'Check if the reel is public',
                'Try using the API endpoint: /api?url=URL',
                'Some reels might require login to view'
            ]
        }), 500
        
    except Exception as e:
        shutil.rmtree(temp_dir)
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        'name': 'Instagram Reel Downloader',
        'version': '2.0.1',
        'status': '✅ Running',
        'endpoints': {
            'api': '/api?url=REEL_URL',
            'auto_download': '/api?url=REEL_URL&download=true',
            'direct_download': '/download?url=REEL_URL'
        },
        'requirements': {
            'yt-dlp': 'Installed and updated automatically',
            'dependencies': 'Flask, requests, yt-dlp'
        },
        'notes': [
            'Public reels only - private reels require login',
            'Multiple download methods attempted automatically',
            'Temporary files are cleaned up after download'
        ]
    })

if __name__ == '__main__':
    print("Starting Instagram Reel Downloader...")
    print("Ensuring yt-dlp is installed and updated...")
    ensure_ytdlp()
    port = int(os.environ.get('PORT', 10000))
    print(f"Server running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
