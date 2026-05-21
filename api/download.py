import re
import json
import subprocess
import tempfile
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if parsed.path == '/api/download' or parsed.path == '/download':
            url = params.get('url', [''])[0]
            
            if not url:
                self._send_json(400, {"status": False, "error": "No URL provided"})
                return
            
            if not ("instagram.com/reel/" in url or "instagram.com/p/" in url or "instagram.com/reels/" in url):
                self._send_json(400, {"status": False, "error": "Invalid Instagram URL"})
                return
            
            # Extract video using yt-dlp
            video_url = self._extract_with_ytdlp(url)
            
            if video_url:
                self._send_json(200, {"status": True, "video_url": video_url})
            else:
                self._send_json(404, {"status": False, "error": "Failed to fetch video"})
        
        elif parsed.path == '/api/health' or parsed.path == '/health' or parsed.path == '/':
            self._send_json(200, {"status": "ok", "service": "Instagram Downloader API (yt-dlp)"})
        
        else:
            self._send_json(404, {"error": "Not found"})
    
    def do_POST(self):
        if self.path == '/api/download' or self.path == '/download':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body)
                url = data.get('url', '')
            except:
                url = ''
            
            if not url:
                self._send_json(400, {"status": False, "error": "No URL provided"})
                return
            
            if not ("instagram.com/reel/" in url or "instagram.com/p/" in url or "instagram.com/reels/" in url):
                self._send_json(400, {"status": False, "error": "Invalid Instagram URL"})
                return
            
            video_url = self._extract_with_ytdlp(url)
            
            if video_url:
                self._send_json(200, {"status": True, "video_url": video_url})
            else:
                self._send_json(404, {"status": False, "error": "Failed to fetch video"})
        else:
            self._send_json(404, {"error": "Not found"})
    
    def _extract_with_ytdlp(self, url):
        """Extract video URL using yt-dlp"""
        try:
            # Create temp directory
            with tempfile.TemporaryDirectory() as tmpdir:
                # yt-dlp command to get video URL without downloading
                cmd = [
                    "yt-dlp",
                    "-g",  # Get URL only, no download
                    "--no-warnings",
                    url
                ]
                
                print(f"📡 Running: {' '.join(cmd)}")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    video_url = result.stdout.strip()
                    if video_url and video_url.startswith('http'):
                        print(f"✅ Video URL extracted: {video_url[:80]}...")
                        return video_url
                    else:
                        print(f"❌ Invalid URL: {video_url}")
                        return None
                else:
                    print(f"❌ yt-dlp error: {result.stderr}")
                    return None
                    
        except subprocess.TimeoutExpired:
            print("❌ yt-dlp timeout")
            return None
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None
    
    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
