from flask import Flask, request, jsonify, send_file
import subprocess
import os
import base64
import time
import re
import io

app = Flask(__name__)

@app.route('/api', methods=['GET'])
def download_reel():
    url = request.args.get('url')
    download = request.args.get('download', 'false').lower() == 'true'
    
    if not url:
        return jsonify({
            'status': '✅ API Running',
            'usage': '/api?url=REEL_URL',
            'auto_download': '/api?url=REEL_URL&download=true'
        })
    
    if not re.search(r'instagram\.com/(reel|p|tv)/[\w-]+', url):
        return jsonify({'error': '❌ Invalid Instagram URL'}), 400
    
    try:
        file_id = str(int(time.time())) + '_' + os.urandom(4).hex()
        file_path = f'/tmp/{file_id}.mp4'
        
        cmd = ['yt-dlp', '-f', 'best[ext=mp4]', '-o', file_path, '--no-playlist', '--quiet', url]
        subprocess.run(cmd, timeout=120, capture_output=True)
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
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
            os.unlink(file_path)
            return jsonify({
                'success': True,
                'file_base64': content,
                'message': '✅ Download successful!',
                'direct_download': f'/api?url={url}&download=true'
            })
        
        return jsonify({'error': 'Download failed'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['GET'])
def download_direct():
    """Direct download endpoint - even simpler!"""
    url = request.args.get('url')
    
    if not url:
        return jsonify({'error': 'URL required', 'usage': '/download?url=REEL_URL'}), 400
    
    if not re.search(r'instagram\.com/(reel|p|tv)/[\w-]+', url):
        return jsonify({'error': '❌ Invalid Instagram URL'}), 400
    
    try:
        file_id = str(int(time.time())) + '_' + os.urandom(4).hex()
        file_path = f'/tmp/{file_id}.mp4'
        
        cmd = ['yt-dlp', '-f', 'best[ext=mp4]', '-o', file_path, '--no-playlist', '--quiet', url]
        subprocess.run(cmd, timeout=120, capture_output=True)
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return send_file(
                file_path,
                as_attachment=True,
                download_name=f'reel_{file_id}.mp4',
                mimetype='video/mp4'
            )
        
        return jsonify({'error': 'Download failed'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        'name': 'Instagram Reel Downloader',
        'version': '2.0.0',
        'endpoints': {
            'api': '/api?url=REEL_URL',
            'auto_download': '/api?url=REEL_URL&download=true',
            'direct_download': '/download?url=REEL_URL'
        },
        'usage': {
            'base64': '/api?url=REEL_URL',
            'auto_download': '/api?url=REEL_URL&download=true',
            'simple_download': '/download?url=REEL_URL'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
