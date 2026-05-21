from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)
DEVELOPER = "@KINGITACHI18"

def get_video_url(url):
    """Multiple fallback methods"""
    
    # Method 1: instasave API
    try:
        api_url = "https://instasave.icu/api/ajax"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest"
        }
        data = {"url": url}
        resp = requests.post(api_url, headers=headers, data=data, timeout=15)
        if resp.status_code == 200:
            result = resp.json()
            video = result.get("video_url") or result.get("video")
            if video:
                return video
    except:
        pass
    
    # Method 2: Instagram embed
    try:
        shortcode = re.search(r'instagram\.com/(?:reel|p)/([a-zA-Z0-9_-]+)', url).group(1)
        embed_url = f"https://www.instagram.com/p/{shortcode}/embed/"
        resp = requests.get(embed_url, timeout=10)
        if resp.status_code == 200:
            match = re.search(r'"video_url":"([^"]+)"', resp.text)
            if match:
                return match.group(1).replace('\\/', '/')
    except:
        pass
    
    return None

@app.route('/')
def home():
    return jsonify({
        "service": "Instagram Reel Downloader",
        "developer": DEVELOPER,
        "status": "active",
        "endpoint": "/api/download?url=INSTAGRAM_URL"
    })

@app.route('/api/download')
def download():
    url = request.args.get('url', '')
    
    if not url:
        return jsonify({"status": False, "error": "No URL provided", "developer": DEVELOPER}), 400
    
    if not ("instagram.com/reel/" in url or "instagram.com/p/" in url):
        return jsonify({"status": False, "error": "Invalid Instagram URL", "developer": DEVELOPER}), 400
    
    video_url = get_video_url(url)
    
    if video_url:
        return jsonify({
            "status": True,
            "video_url": video_url,
            "developer": DEVELOPER
        })
    else:
        return jsonify({
            "status": False,
            "error": "Failed to fetch video. Try another URL",
            "developer": DEVELOPER
        }), 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
