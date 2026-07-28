from flask import Flask, request, jsonify
import subprocess
import os
import base64
import time

app = Flask(__name__)

@app.route('/api')
def download_reel():
    url = request.args.get('url')
    
    if not url:
        return jsonify({
            'status': '✅ API Running on Render (Python)',
            'usage': '/api?url=INSTAGRAM_URL',
            'example': '/api?url=https://www.instagram.com/reel/CxYz123AbCd/'
        })
    
    if 'instagram.com' not in url:
        return jsonify({'error': '❌ Invalid Instagram URL'}), 400
    
    try:
        file_id = str(int(time.time())) + '_' + os.urandom(4).hex()
        file_path = f'/tmp/{file_id}.mp4'
        
        # Download using yt-dlp
        cmd = ['yt-dlp', '-f', 'best[ext=mp4]', '-o', file_path, '--no-playlist', '--quiet', url]
        subprocess.run(cmd, timeout=60, capture_output=True)
        
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            os.unlink(file_path)
            
            return jsonify({
                'success': True,
                'file_base64': content,
                'message': '✅ Download successful!'
            })
        
        return jsonify({'error': 'Download failed'}), 500
        
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Download timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        'name': 'Instagram Reel Downloader',
        'version': '1.0.0',
        'endpoints': {
            'download': '/api?url=INSTAGRAM_URL'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
