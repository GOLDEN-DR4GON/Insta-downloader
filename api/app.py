from flask import Flask, request, jsonify
import subprocess
import os
import base64
import time
import re

app = Flask(__name__)

@app.route('/api', methods=['GET'])
def download_reel():
    # Get URL from query parameter
    url = request.args.get('url')
    
    # If no URL, show API info
    if not url:
        return jsonify({
            'status': '✅ API Running on Render',
            'usage': '/api?url=INSTAGRAM_URL',
            'example': '/api?url=https://www.instagram.com/reel/CxYz123AbCd/',
            'endpoints': {
                'download': '/api?url=REEL_URL',
                'health': '/health'
            }
        })
    
    # Validate Instagram URL
    if not re.search(r'instagram\.com/(reel|p|tv)/[\w-]+', url):
        return jsonify({
            'error': '❌ Invalid Instagram URL',
            'valid_formats': [
                'https://www.instagram.com/reel/XXXXX/',
                'https://www.instagram.com/p/XXXXX/',
                'https://www.instagram.com/tv/XXXXX/'
            ]
        }), 400
    
    try:
        # Generate unique file ID
        file_id = str(int(time.time())) + '_' + os.urandom(4).hex()
        file_path = f'/tmp/{file_id}.mp4'
        
        # Download using yt-dlp
        cmd = [
            'yt-dlp',
            '-f', 'best[ext=mp4]',
            '-o', file_path,
            '--no-playlist',
            '--quiet',
            url
        ]
        
        result = subprocess.run(cmd, timeout=120, capture_output=True)
        
        # Check if download succeeded
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            # Read and encode file
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            
            # Clean up
            os.unlink(file_path)
            
            return jsonify({
                'success': True,
                'file_base64': content,
                'message': '✅ Download successful!',
                'note': 'Decode base64 to get video file'
            })
        else:
            error_msg = result.stderr.decode() if result.stderr else 'Unknown error'
            return jsonify({
                'error': 'Download failed',
                'details': error_msg[:200]
            }), 500
        
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Download timed out (120s limit)'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'name': 'Instagram Reel Downloader',
        'version': '2.0.0',
        'status': 'running',
        'endpoints': {
            'download': '/api?url=INSTAGRAM_URL',
            'health': '/health',
            'info': '/'
        },
        'example': '/api?url=https://www.instagram.com/reel/CxYz123AbCd/'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
