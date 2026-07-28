from flask import Flask, request, jsonify
import subprocess
import os
import base64
import time
import re

app = Flask(__name__)

@app.route('/api', methods=['GET'])
def download_reel():
    url = request.args.get('url')
    
    if not url:
        return jsonify({
            'status': '✅ API Running on Render (Docker)',
            'usage': '/api?url=INSTAGRAM_URL',
            'example': '/api?url=https://www.instagram.com/reel/CxYz123AbCd/'
        })
    
    if not re.search(r'instagram\.com/(reel|p|tv)/[\w-]+', url):
        return jsonify({'error': '❌ Invalid Instagram URL'}), 400
    
    try:
        file_id = str(int(time.time())) + '_' + os.urandom(4).hex()
        file_path = f'/tmp/{file_id}.mp4'
        
        cmd = ['yt-dlp', '-f', 'best[ext=mp4]', '-o', file_path, '--no-playlist', '--quiet', url]
        subprocess.run(cmd, timeout=120, capture_output=True)
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(file_path)
            return jsonify({
                'success': True,
                'file_base64': content,
                'message': '✅ Download successful!'
            })
        
        return jsonify({'error': 'Download failed'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'name': 'Instagram Reel Downloader',
        'version': '2.0.0',
        'status': 'running',
        'endpoints': {
            'download': '/api?url=INSTAGRAM_URL',
            'health': '/health'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
