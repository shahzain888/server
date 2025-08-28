# from flask import Flask, jsonify, request
# import requests
# import time
# import yt_dlp
# import random

# app = Flask(__name__)

# # ---- In-Memory Cache ----
# cache = {}

# def cache_get(key):
#     entry = cache.get(key)
#     if not entry:
#         return None
#     value, expires = entry
#     if expires < time.time():
#         del cache[key]
#         return None
#     return value

# def cache_setex(key, ttl, value):
#     cache[key] = (value, time.time() + ttl)

# # ---- YouTube API Config ----
# YOUTUBE_API_KEY = "AIzaSyBCkBmOPQeHtOHv_VkrsqZHwJm9mmLp1Wc"
# SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
# VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"

# # ---- Genres/queries for variety ----
# MUSIC_QUERIES = [
#     "top music hits", "popular music", "latest music", 
#     "music video", "trending music", "hot music 2025"
# ]

# MUSIC_CATEGORIES = {
#     "Trending": {"chart": "mostPopular", "videoCategoryId": "10"},  # music category
#     "Explore": {"query": "new music 2025"},
#     "Live Performance": {"query": "live performance music"},
#     "Top Hits": {"query": "top music hits"},
# }
# @app.route("/songs")
# def get_songs():
#     cache_key = "songs_pool"
#     cached = cache_get(cache_key)
#     if cached:
#         return jsonify(cached), 200

#     all_categories = {}

#     for cat_name, cat_info in MUSIC_CATEGORIES.items():
#         results = []

#         try:
#             if "chart" in cat_info:
#                 # Most popular videos endpoint
#                 params = {
#                     "part": "snippet,contentDetails,statistics",
#                     "chart": cat_info["chart"],
#                     "regionCode": "US",
#                     "videoCategoryId": cat_info.get("videoCategoryId", "10"),
#                     "maxResults": 50,
#                     "key": YOUTUBE_API_KEY
#                 }
#                 resp = requests.get(VIDEO_URL, params=params).json()
#                 items = resp.get("items", [])

#             else:
#                 # Search endpoint for query
#                 params = {
#                     "part": "snippet",
#                     "q": cat_info["query"],
#                     "type": "video",
#                     "order": "viewCount",
#                     "maxResults": 50,
#                     "videoCategoryId": "10",
#                     "key": YOUTUBE_API_KEY
#                 }
#                 resp = requests.get(SEARCH_URL, params=params).json()
#                 items = resp.get("items", [])

#             for item in items:
#                 vid = item["id"]["videoId"] if "id" in item and "videoId" in item["id"] else item.get("id")
#                 title = item["snippet"]["title"]
#                 thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
#                 results.append({
#                     "id": vid,
#                     "title": title,
#                     "video_url": f"https://www.youtube.com/watch?v={vid}",
#                     "thumbnail": thumbnail
#                 })

#         except Exception as e:
#             print(f"Error fetching {cat_name}: {e}")
#             continue

#         all_categories[cat_name] = results[:50]  # limit per category

#     # Cache for 2 hours
#     cache_setex(cache_key, 7200, all_categories)

#     return jsonify(all_categories), 200

# @app.route("/play/<video_id>")
# def get_play_url(video_id):
#     if not video_id:
#         return jsonify({"error": "Missing video id"}), 400

#     video_url = f"https://www.youtube.com/watch?v={video_id}"

#     try:
#         ydl_opts = {
#             "format": "best[ext=mp4]/best",
#             "quiet": True,
#             "noplaylist": True
#         }

#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             info = ydl.extract_info(video_url, download=False)
#             stream_url = info.get("url")
#             if not stream_url:
#                 return jsonify({"error": "No playable stream found"}), 404

#         return jsonify({
#             "video_id": video_id,
#             "title": info.get("title"),
#             "stream_url": stream_url
#         }), 200

#     except yt_dlp.utils.DownloadError as e:
#         return jsonify({"error": f"Failed to fetch video: {str(e)}"}), 404
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)

from flask import Flask, jsonify, request
import requests
import time
import yt_dlp
import random

app = Flask(__name__)

# ---- In-Memory Cache ----
cache = {}

def cache_get(key):
    entry = cache.get(key)
    if not entry:
        return None
    value, expires = entry
    if expires < time.time():
        del cache[key]
        return None
    return value

def cache_setex(key, ttl, value):
    cache[key] = (value, time.time() + ttl)

# ---- YouTube API Config ----
YOUTUBE_API_KEY = "AIzaSyA_kFB3npZFQ6qV3GirzPl9xHXySZFhMtI"
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"

# ---- Music Categories ----
MUSIC_CATEGORIES = {
    "Trending": {"chart": "mostPopular", "videoCategoryId": "10"},
    "Explore": {"query": "new music 2025"},
    "Live Performance": {"query": "live performance music"},
    "Top Hits": {"query": "top music hits"}
}

MAX_RESULTS_PER_CATEGORY = 900  # cap per category
MAX_RESULTS_PER_PAGE = 50       # API max

# ---- Helper: Fetch YouTube Videos ----
def fetch_videos_for_category(cat_name, cat_info):
    results = []
    next_page_token = None

    try:
        while len(results) < MAX_RESULTS_PER_CATEGORY:
            if "chart" in cat_info:
                # Most popular videos
                params = {
                    "part": "snippet,contentDetails,statistics",
                    "chart": cat_info["chart"],
                    "regionCode": "US",   # force US to avoid India-only bias
                    "videoCategoryId": cat_info.get("videoCategoryId", "10"),
                    "maxResults": MAX_RESULTS_PER_PAGE,
                    "pageToken": next_page_token,
                    "key": YOUTUBE_API_KEY
                }
                resp = requests.get(VIDEO_URL, params=params).json()
                items = resp.get("items", [])

            else:
                # Search by query
                params = {
                    "part": "snippet",
                    "q": cat_info["query"],
                    "type": "video",
                    "order": "viewCount",
                    "maxResults": MAX_RESULTS_PER_PAGE,
                    "videoCategoryId": "10",
                    "pageToken": next_page_token,
                    "key": YOUTUBE_API_KEY
                }
                resp = requests.get(SEARCH_URL, params=params).json()
                items = resp.get("items", [])

            for item in items:
                vid = (
                    item["id"]["videoId"]
                    if "id" in item and isinstance(item["id"], dict) and "videoId" in item["id"]
                    else item.get("id")
                )
                if not vid:
                    continue
                title = item["snippet"]["title"]
                thumbnail = item["snippet"]["thumbnails"].get("high", {}).get("url", "")
                results.append({
                    "id": vid,
                    "title": title,
                    "video_url": f"https://www.youtube.com/watch?v={vid}",
                    "thumbnail": thumbnail
                })

                if len(results) >= MAX_RESULTS_PER_CATEGORY:
                    break

            next_page_token = resp.get("nextPageToken")
            if not next_page_token:
                break

    except Exception as e:
        print(f"Error fetching {cat_name}: {e}")

    # Shuffle results for variety
    random.shuffle(results)
    return results

# ---- API Route: Songs ----
@app.route("/songs")
def get_songs():
    cache_key = "songs_pool"
    cached = cache_get(cache_key)
    if cached:
        return jsonify(cached), 200

    all_categories = {}

    for cat_name, cat_info in MUSIC_CATEGORIES.items():
        all_categories[cat_name] = fetch_videos_for_category(cat_name, cat_info)

    # Cache for 2 hours
    cache_setex(cache_key, 7200, all_categories)

    return jsonify(all_categories), 200

# ---- API Route: Play Stream URL ----
@app.route("/play/<video_id>")
def get_play_url(video_id):
    if not video_id:
        return jsonify({"error": "Missing video id"}), 400

    video_url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "quiet": True,
            "noplaylist": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            stream_url = info.get("url")
            if not stream_url:
                return jsonify({"error": "No playable stream found"}), 404

        return jsonify({
            "video_id": video_id,
            "title": info.get("title"),
            "stream_url": stream_url
        }), 200

    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": f"Failed to fetch video: {str(e)}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
