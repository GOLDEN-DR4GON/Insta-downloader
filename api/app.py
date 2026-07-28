from flask import Flask, request, jsonify
import subprocess
import os
import base64
import time
import re
import shutil

app = Flask(__name__)

# Find yt-dlp path
def get_ytdlp_path():
    # Common locations
    paths = [
        '/usr/local/bin/yt-dlp',
        '/usr/bin/yt-dlp',
        '/opt/render/.local/bin/yt-dlp',
        '/home/user/.local/bin/yt-dlp'
    ]
    
    # Try to find it
    for path in paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    # Try which command
    try:
        result = subprocess.run(['which', 'yt-dlp'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    return 'yt-dlp'  # Fallback

YTDLP_PATH = get_ytdlp_path()

@app.route('/api')
def download_reel():
    url = request.args.get('url')
    
    if not url:
        return jsonify({
            'status': '✅ API Running',
            'usage': '/api?url=INSTAGRAM_URL',
            'ytdlp_path': YTDLP_PATH
        })
    
    if not re.search(r'instagram\.com/(reel|p|tv)/[\w-]+', url):
        return jsonify({'error': '❌ Invalid URL'}), 400
    
    try:
        file_id = str(int(time.time())) + '_' + os.urandom(4).hex()
        file_path = f'/tmp/{file_id}.mp4'
        
        # Use full path to yt-dlp
        cmd = [
            YTDLP_PATH,
            '-f', 'best[ext=mp4]',
            '-o', file_path,
            '--no-playlist',
            '--quiet',
            url
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, timeout=120, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"yt-dlp error: {result.stderr}")
            return jsonify({'error': f'yt-dlp failed: {result.stderr[:200]}'}), 500
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(file_path)
            return jsonify({
                'success': True,
                'file_base64': content,
                'message': '✅ Download successful!'
            })
        
        return jsonify({'error': 'File not created'}), 500
        
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Download timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'ytdlp_path': YTDLP_PATH,
        'ytdlp_exists': os.path.exists(YTDLP_PATH) if YTDLP_PATH != 'yt-dlp' else False
    })

@app.route('/')
def home():
    return jsonify({
        'name': 'Instagram Reel Downloader',
        'version': '3.0.0',
        'endpoints': {
            'download': '/api?url=INSTAGRAM_URL',
            'health': '/health'
        },
        'ytdlp_path': YTDLP_PATH
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting server on port {port}")
    print(f"yt-dlp path: {YTDLP_PATH}")
    app.run(host='0.0.0.0', port=port, debug=False)
