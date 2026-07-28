from flask import Flask, request, jsonify
import subprocess, os, base64, time, re

app = Flask(__name__)

@app.route('/api')
def download():
    url = request.args.get('url')
    
    if not url:
        return jsonify({
            'status': '✅ Ready',
            'usage': '/api?url=INSTAGRAM_URL',
            'note': 'For private reels, use cookies'
        })
    
    if not re.search(r'instagram\.com/(reel|p|tv)/[\w-]+', url):
        return jsonify({'error': '❌ Invalid URL'}), 400
    
    try:
        fid = str(int(time.time()))
        path = f'/tmp/{fid}.mp4'
        
        # Add user-agent to avoid blocks
        cmd = [
            'yt-dlp',
            '-f', 'best[ext=mp4]',
            '-o', path,
            '--no-playlist',
            '--quiet',
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            url
        ]
        
        result = subprocess.run(cmd, timeout=120, capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = result.stderr[:300]
            return jsonify({'error': f'Download failed: {error_msg}'}), 500
        
        if os.path.exists(path) and os.path.getsize(path) > 0:
            with open(path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode()
            os.unlink(path)
            return jsonify({
                'success': True,
                'file_base64': b64,
                'message': '✅ Download successful!'
            })
        
        return jsonify({'error': 'File not created'}), 500
        
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Timeout'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        'name': 'Reel Downloader',
        'version': '3.0',
        'endpoint': '/api?url=URL'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
