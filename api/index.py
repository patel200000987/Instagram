from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

# Developer info
DEVELOPER = "@KINGITACHI18"
SERVICE_NAME = "Instagram Reel Downloader"

# RapidAPI credentials (hidden)
RAPIDAPI_KEY = "1f06777488mshf1328d62ec5c4f1p199cf4jsn8a99846b3da1"
RAPIDAPI_HOST = "instagram-downloader-download-instagram-videos-stories.p.rapidapi.com"

def get_instagram_video(url):
    """Fetch video URL from Instagram"""
    try:
        api_url = "https://instagram-downloader-download-instagram-videos-stories.p.rapidapi.com/index"
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }
        
        params = {"url": url}
        
        response = requests.get(api_url, headers=headers, params=params, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            
            video_url = data.get("video_url") or data.get("video") or data.get("url") or data.get("download_url")
            
            if not video_url and data.get("result"):
                video_url = data["result"].get("video_url") or data["result"].get("url")
            
            if not video_url and data.get("data"):
                if isinstance(data["data"], dict):
                    video_url = data["data"].get("video_url") or data["data"].get("url")
            
            return video_url
        else:
            return None
            
    except Exception as e:
        return None

@app.route('/')
def home():
    return jsonify({
        "service": SERVICE_NAME,
        "developer": DEVELOPER,
        "status": "active",
        "endpoints": {
            "/api/download?url=INSTAGRAM_URL": "Download Instagram Reel",
            "/health": "Health check"
        },
        "example": "/api/download?url=https://www.instagram.com/reel/xxxxx"
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "service": SERVICE_NAME,
        "developer": DEVELOPER
    })

@app.route('/api/download')
def download():
    url = request.args.get('url', '')
    
    if not url:
        return jsonify({
            "status": False,
            "error": "No URL provided",
            "developer": DEVELOPER
        }), 400
    
    if not ("instagram.com/reel/" in url or "instagram.com/p/" in url):
        return jsonify({
            "status": False,
            "error": "Invalid URL. Please provide Instagram Reel URL",
            "developer": DEVELOPER
        }), 400
    
    video_url = get_instagram_video(url)
    
    if video_url:
        return jsonify({
            "status": True,
            "video_url": video_url,
            "developer": DEVELOPER,
            "message": "Video fetched successfully"
        })
    else:
        return jsonify({
            "status": False,
            "error": "Failed to fetch video. Try another URL or check if reel is public",
            "developer": DEVELOPER
        }), 404

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "error": "Endpoint not found",
        "developer": DEVELOPER
    }), 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
