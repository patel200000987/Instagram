import re
import requests
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if parsed.path == '/api/download':
            url = params.get('url', [''])[0]
            
            if not url:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": False,
                    "error": "No URL provided",
                    "message": "Please provide ?url=INSTAGRAM_REEL_URL"
                }).encode())
                return
            
            # Validate Instagram URL
            if not ("instagram.com/reel/" in url or "instagram.com/p/" in url):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": False,
                    "error": "Invalid URL",
                    "message": "Please provide a valid Instagram Reel URL"
                }).encode())
                return
            
            # Get video URL
            video_url = self.extract_video(url)
            
            if video_url:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": True,
                    "video_url": video_url,
                    "thumbnail": None,
                    "message": "Video fetched successfully"
                }).encode())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": False,
                    "error": "Failed to fetch video",
                    "message": "Could not extract video. Try another URL."
                }).encode())
        
        elif parsed.path == '/api/health' or parsed.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "service": "Instagram Downloader API",
                "endpoints": {
                    "download": "/api/download?url=INSTAGRAM_URL",
                    "health": "/api/health"
                }
            }).encode())
        
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/download':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body)
                url = data.get('url', '')
            except:
                url = ''
            
            if not url:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": False,
                    "error": "No URL provided"
                }).encode())
                return
            
            # Validate Instagram URL
            if not ("instagram.com/reel/" in url or "instagram.com/p/" in url):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": False,
                    "error": "Invalid URL"
                }).encode())
                return
            
            video_url = self.extract_video(url)
            
            if video_url:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": True,
                    "video_url": video_url
                }).encode())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": False,
                    "error": "Failed to fetch video"
                }).encode())
    
    def extract_video(self, url):
        """Extract video URL from Instagram"""
        
        # Clean URL
        url = url.split('?')[0].rstrip('/')
        
        # Extract shortcode
        shortcode_match = re.search(r'instagram\.com/(?:reel|p)/([a-zA-Z0-9_-]+)', url)
        if not shortcode_match:
            return None
        
        shortcode = shortcode_match.group(1)
        print(f"📡 Shortcode: {shortcode}")
        
        # Try embed page method
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        
        embed_url = f"https://www.instagram.com/p/{shortcode}/embed/"
        
        try:
            resp = requests.get(embed_url, headers=headers, timeout=15)
            if resp.status_code == 200:
                # Search for video URL
                video_patterns = [
                    r'"video_url":"([^"]+)"',
                    r'<meta property="og:video" content="([^"]+)"',
                ]
                for pattern in video_patterns:
                    match = re.search(pattern, resp.text)
                    if match:
                        video_url = match.group(1).replace('\\/', '/')
                        return video_url
        except:
            pass
        
        # Try Instagram API
        api_headers = {
            "User-Agent": "Instagram 123.0.0.21.114 (iPhone; iOS 15_0; en_US; en)",
            "Accept": "application/json",
        }
        
        api_url = f"https://www.instagram.com/api/v1/media/{shortcode}/info/"
        
        try:
            resp = requests.get(api_url, headers=api_headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                if items:
                    video_versions = items[0].get("video_versions", [])
                    if video_versions:
                        return video_versions[0].get("url")
        except:
            pass
        
        return None


def extract_video_url(url):
    """Simple function for direct import"""
    shortcode_match = re.search(r'instagram\.com/(?:reel|p)/([a-zA-Z0-9_-]+)', url)
    if not shortcode_match:
        return None
    
    shortcode = shortcode_match.group(1)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    
    embed_url = f"https://www.instagram.com/p/{shortcode}/embed/"
    
    try:
        resp = requests.get(embed_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            match = re.search(r'"video_url":"([^"]+)"', resp.text)
            if match:
                return match.group(1).replace('\\/', '/')
    except:
        pass
    
    return None
