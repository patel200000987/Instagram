import re
import json
import requests
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if parsed.path == '/api/download' or parsed.path == '/':
            url = params.get('url', [''])[0]
            
            if not url:
                self._send_json(400, {"status": False, "error": "No URL provided"})
                return
            
            # Support Instagram Reel URLs
            if not ("instagram.com/reel/" in url or "instagram.com/p/" in url):
                self._send_json(400, {"status": False, "error": "Invalid Instagram URL"})
                return
            
            video_url = self._get_video_url(url)
            
            if video_url:
                self._send_json(200, {"status": True, "video_url": video_url})
            else:
                self._send_json(404, {"status": False, "error": "Failed to fetch video"})
        
        elif parsed.path == '/health':
            self._send_json(200, {"status": "ok"})
        
        else:
            self._send_json(404, {"error": "Not found"})
    
    def _get_video_url(self, url):
        """Extract video URL from Instagram"""
        
        # Extract shortcode
        shortcode_match = re.search(r'instagram\.com/(?:reel|p)/([a-zA-Z0-9_-]+)', url)
        if not shortcode_match:
            return None
        
        shortcode = shortcode_match.group(1)
        
        # Method 1: Instagram oEmbed API
        try:
            oembed_url = f"https://api.instagram.com/oembed?url=https://www.instagram.com/reel/{shortcode}/"
            resp = requests.get(oembed_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # oEmbed doesn't give direct video URL, but gives thumbnail
                thumbnail = data.get('thumbnail_url', '')
                if thumbnail:
                    # Convert thumbnail to video URL (works sometimes)
                    video_candidate = thumbnail.replace('.jpg', '.mp4')
                    if video_candidate != thumbnail:
                        return video_candidate
        except:
            pass
        
        # Method 2: Embed page extraction
        try:
            embed_url = f"https://www.instagram.com/p/{shortcode}/embed/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.get(embed_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                # Search for video URL in HTML
                match = re.search(r'"video_url":"([^"]+)"', resp.text)
                if match:
                    return match.group(1).replace('\\/', '/')
        except:
            pass
        
        # Method 3: GraphQL API (with public query)
        try:
            graphql_url = f"https://www.instagram.com/graphql/query/?query_hash=69cba40317214236af40e7efa697781d&variables={{\"shortcode\":\"{shortcode}\"}}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.get(graphql_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # Navigate to video URL
                try:
                    video_url = data['data']['shortcode_media']['video_url']
                    if video_url:
                        return video_url
                except:
                    pass
        except:
            pass
        
        return None
    
    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
