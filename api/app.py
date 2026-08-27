from flask import Flask, request, jsonify, send_file
import subprocess
import os
import base64
import time
import re
import tempfile
import shutil
import sys
import json
import logging
from urllib.parse import urlparse
import requests

# ============================================================
# SETUP
# ============================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ============================================================
# INSTALL REQUESTS IF MISSING
# ============================================================
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests

# ============================================================
# URL_EXTRACTOR
# ============================================================

def extract_shortcode(url):
    """Extract Instagram shortcode from ANY URL"""
    if not url:
        return None
    
    url = url.strip()
    
    patterns = [
        r'(?:instagram\.com|instagr\.am)/(?:reel|p|tv|share)/([A-Za-z0-9_-]+)',
        r'(?:instagram\.com|instagr\.am)/p/([A-Za-z0-9_-]+)',
        r'(?:instagram\.com|instagr\.am)/reel/([A-Za-z0-9_-]+)',
        r'(?:instagram\.com|instagr\.am)/([A-Za-z0-9_-]{8,})',
        r'igshid=([A-Za-z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            shortcode = match.group(1)
            if shortcode and len(shortcode) >= 5:
                return shortcode
    
    # Try path parsing
    try:
        parsed = urlparse(url)
        if parsed.path:
            parts = parsed.path.split('/')
            for part in parts:
                if part and len(part) >= 5 and re.match(r'^[A-Za-z0-9_-]+$', part):
                    if part not in ['reel', 'p', 'tv', 'share']:
                        return part
    except:
        pass
    
    return None

# ============================================================
# DOWNLOAD_ENGINE
# ============================================================

def download_instagram_video(url, output_path):
    """Download Instagram video - returns (success, message)"""
    
    shortcode = extract_shortcode(url)
    logger.info(f"🎯 Shortcode: {shortcode}")
    
    # METHOD 1: GraphQL Direct
    if shortcode:
        logger.info("🔄 Method 1: GraphQL...")
        try:
            api_url = f'https://www.instagram.com/p/{shortcode}/?__a=1&__d=dis'
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'https://www.instagram.com/p/{shortcode}/',
                'Cookie': f'ig_did={os.urandom(16).hex()}; mid={os.urandom(16).hex()}; csrftoken={os.urandom(16).hex()}',
            }
            
            response = requests.get(api_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                video_url = None
                
                # Extract video URL
                if 'graphql' in data and 'shortcode_media' in data['graphql']:
                    media = data['graphql']['shortcode_media']
                    if 'video_url' in media:
                        video_url = media['video_url']
                    elif 'edge_sidecar_to_children' in media:
                        edges = media['edge_sidecar_to_children']['edges']
                        if edges and 'video_url' in edges[0]['node']:
                            video_url = edges[0]['node']['video_url']
                
                if video_url:
                    logger.info(f"✅ Found video URL")
                    return download_direct(video_url, output_path)
        except Exception as e:
            logger.warning(f"GraphQL failed: {str(e)}")
    
    # METHOD 2: yt-dlp
    logger.info("🔄 Method 2: yt-dlp...")
    
    commands = [
        ['yt-dlp', '-f', 'best[ext=mp4]', '-o', output_path, '--no-playlist', '--quiet', '--no-warnings', '--ignore-errors', '--force-ipv4', '--no-check-certificate', url],
        ['yt-dlp', '-f', 'best[ext=mp4]', '-o', output_path, '--no-playlist', '--quiet', '--no-warnings', '--ignore-errors', '--user-agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)', '--force-ipv4', '--no-check-certificate', url],
        ['yt-dlp', '-f', 'best[ext=mp4]', '-o', output_path, '--no-playlist', '--quiet', '--ignore-errors', '--cookies-from-browser', 'chrome', '--force-ipv4', '--no-check-certificate', url],
    ]
    
    for i, cmd in enumerate(commands, 1):
        try:
            result = subprocess.run(cmd, timeout=120, capture_output=True, text=True)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"✅ yt-dlp success (attempt {i})")
                return True, f"yt-dlp method {i}"
        except Exception as e:
            logger.warning(f"yt-dlp attempt {i} failed: {str(e)}")
    
    # METHOD 3: Page Extraction
    if shortcode:
        logger.info("🔄 Method 3: Page extraction...")
        try:
            page_url = f'https://www.instagram.com/p/{shortcode}/'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = requests.get(page_url, headers=headers, timeout=15)
            if response.status_code == 200:
                html = response.text
                
                patterns = [
                    r'"video_url":"([^"]+)"',
                    r'"video_versions":\[\{"url":"([^"]+)"',
                    r'<meta property="og:video" content="([^"]+)"',
                    r'https://[a-zA-Z0-9.-]+\.cdninstagram\.com/[^"\']+\.mp4[^"\']*',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html)
                    for match in matches:
                        video_url = match.replace('\\/', '/')
                        if video_url.startswith('//'):
                            video_url = 'https:' + video_url
                        if video_url.startswith('http') and ('.mp4' in video_url or 'cdninstagram' in video_url):
                            logger.info(f"✅ Found in page")
                            return download_direct(video_url, output_path)
        except Exception as e:
            logger.warning(f"Page extraction failed: {str(e)}")
    
    return False, "All methods failed"

def download_direct(video_url, output_path):
    """Direct download with retry"""
    
    for attempt in range(3):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'video/mp4,video/webm,video/*;q=0.9,*/*;q=0.8',
                'Accept-Encoding': 'identity',
                'Connection': 'keep-alive',
                'Referer': 'https://www.instagram.com/',
            }
            
            # Resume support
            resume_byte = 0
            if os.path.exists(output_path):
                resume_byte = os.path.getsize(output_path)
                if resume_byte > 0:
                    headers['Range'] = f'bytes={resume_byte}-'
            
            response = requests.get(video_url, headers=headers, timeout=60, stream=True)
            
            if response.status_code in [200, 206]:
                mode = 'ab' if resume_byte > 0 else 'wb'
                with open(output_path, mode) as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info(f"✅ Downloaded: {os.path.getsize(output_path)} bytes")
                    return True, "Download successful"
            
            time.sleep(2 ** attempt)
            
        except Exception as e:
            logger.warning(f"Download attempt {attempt+1} failed: {str(e)}")
            time.sleep(2 ** attempt)
    
    return False, "Download failed"

def ensure_ytdlp():
    """Ensure yt-dlp is installed"""
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True, timeout=10)
        return True
    except:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'yt-dlp'], 
                         check=True, timeout=60)
            return True
        except:
            return False

# ============================================================
# API ONLY ENDPOINTS
# ============================================================

@app.route('/', methods=['GET'])
def root():
    """API info"""
    return jsonify({
        'service': 'Instagram Downloader API',
        'version': '1.0.0',
        'status': 'online',
        'endpoints': {
            '/download': 'GET - Download video file (use ?url=URL)',
            '/api': 'GET - Get video info/JSON (use ?url=URL&format=json|file)',
            '/': 'GET - This info'
        },
        'example': {
            'file': '/download?url=https://www.instagram.com/reel/ABC123/',
            'json': '/api?url=https://www.instagram.com/reel/ABC123/',
            'base64': '/api?url=https://www.instagram.com/reel/ABC123/&format=base64'
        }
    })

@app.route('/download', methods=['GET'])
def download_file():
    """Direct file download endpoint"""
    
    url = request.args.get('url')
    
    if not url:
        return jsonify({
            'error': 'Missing URL parameter',
            'usage': '/download?url=INSTAGRAM_URL'
        }), 400
    
    shortcode = extract_shortcode(url)
    if not shortcode:
        return jsonify({
            'error': 'Invalid Instagram URL',
            'provided': url
        }), 400
    
    logger.info(f"🚀 Downloading: {shortcode}")
    
    ensure_ytdlp()
    
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, f'{shortcode}.mp4')
    
    try:
        success, message = download_instagram_video(url, output_path)
        
        if success and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            file_size = os.path.getsize(output_path)
            logger.info(f"✅ Success: {file_size} bytes")
            
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f'{shortcode}.mp4',
                mimetype='video/mp4'
            )
        
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({
            'error': 'Download failed',
            'reason': message,
            'shortcode': shortcode
        }), 500
        
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({
            'error': str(e),
            'shortcode': shortcode
        }), 500

@app.route('/api', methods=['GET'])
def api_download():
    """API endpoint with multiple formats"""
    
    url = request.args.get('url')
    format_type = request.args.get('format', 'json')
    
    if not url:
        return jsonify({
            'error': 'Missing URL parameter',
            'usage': '/api?url=INSTAGRAM_URL&format=json|file|base64',
            'example': '/api?url=https://www.instagram.com/reel/ABC123/'
        }), 400
    
    shortcode = extract_shortcode(url)
    if not shortcode:
        return jsonify({
            'error': 'Invalid Instagram URL',
            'provided': url
        }), 400
    
    ensure_ytdlp()
    
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, f'{shortcode}.mp4')
    
    try:
        success, message = download_instagram_video(url, output_path)
        
        if success and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            file_size = os.path.getsize(output_path)
            
            # Option 1: Direct file download
            if format_type == 'file':
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=f'{shortcode}.mp4',
                    mimetype='video/mp4'
                )
            
            # Option 2: Base64 encoded
            with open(output_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            if format_type == 'base64':
                return jsonify({
                    'success': True,
                    'shortcode': shortcode,
                    'file_size': file_size,
                    'base64': content
                })
            
            # Default: JSON with metadata (base64 truncated for large files)
            return jsonify({
                'success': True,
                'shortcode': shortcode,
                'file_size': file_size,
                'file_name': f'{shortcode}.mp4',
                'base64_preview': content[:200] + '...' if len(content) > 200 else content,
                'download_url': f'/download?url={url}',
                'method': message
            })
        
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({
            'success': False,
            'error': 'Download failed',
            'reason': message,
            'shortcode': shortcode
        }), 500
        
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'shortcode': shortcode
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🔥 INSTAGRAM DOWNLOADER API")
    print("🔥 STATUS: ONLINE")
    print("🔥 MODE: API ONLY")
    print("=" * 60)
    
    ensure_ytdlp()
    
    port = int(os.environ.get('PORT', 10000))
    print(f"\n🚀 Server: http://0.0.0.0:{port}")
    print(f"\n📌 Endpoints:")
    print(f"   GET /download?url=URL  → Download video file")
    print(f"   GET /api?url=URL       → Get JSON metadata")
    print(f"   GET /api?url=URL&format=file  → Download file")
    print(f"   GET /api?url=URL&format=base64 → Get base64")
    print("\n" + "=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
