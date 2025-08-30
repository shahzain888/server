# from flask import Flask, jsonify
# import requests
# import time
# import yt_dlp
# import random
# import json
# import os

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

# # ---- File-based cache ----
# CACHE_FILE = "songs_cache.json"

# def save_cache_to_file(data):
#     try:
#         with open(CACHE_FILE, "w", encoding="utf-8") as f:
#             json.dump(data, f, ensure_ascii=False, indent=2)
#     except Exception as e:
#         print(f"Error saving cache file: {e}")

# def load_cache_from_file():
#     if os.path.exists(CACHE_FILE):
#         try:
#             with open(CACHE_FILE, "r", encoding="utf-8") as f:
#                 return json.load(f)
#         except Exception as e:
#             print(f"Error reading cache file: {e}")
#     return None


# # ---- YouTube API Config ----
# YOUTUBE_API_KEY = "AIzaSyDTAQXdKQGjb6bsELXWU3ABG7vEBBDOeM8"
# SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
# VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"

# # ---- Music Categories ----
# MUSIC_CATEGORIES = {
#     "Trending": {"chart": "mostPopular", "videoCategoryId": "10"},
#     "Explore": {"query": "new music 2025"},
#     "Live Performance": {"query": "live performance music"},
#     "Top Hits": {"query": "top music hits"}
# }

# MAX_RESULTS_PER_CATEGORY = 200
# MAX_RESULTS_PER_PAGE = 50

# # ---- Helper: Fetch YouTube Videos ----
# def fetch_videos_for_category(cat_name, cat_info):
#     results = []
#     next_page_token = None

#     while len(results) < MAX_RESULTS_PER_CATEGORY:
#         if "chart" in cat_info:
#             params = {
#                 "part": "snippet,contentDetails,statistics",
#                 "chart": cat_info["chart"],
#                 "regionCode": "US",
#                 "videoCategoryId": cat_info.get("videoCategoryId", "10"),
#                 "maxResults": MAX_RESULTS_PER_PAGE,
#                 "pageToken": next_page_token,
#                 "key": YOUTUBE_API_KEY
#             }
#             resp = requests.get(VIDEO_URL, params=params).json()
#             items = resp.get("items", [])

#         else:
#             params = {
#                 "part": "snippet",
#                 "q": cat_info["query"],
#                 "type": "video",
#                 "order": "viewCount",
#                 "maxResults": MAX_RESULTS_PER_PAGE,
#                 "videoCategoryId": "10",
#                 "pageToken": next_page_token,
#                 "key": YOUTUBE_API_KEY
#             }
#             resp = requests.get(SEARCH_URL, params=params).json()
#             items = resp.get("items", [])

#         for item in items:
#             vid = (
#                 item["id"]["videoId"]
#                 if "id" in item and isinstance(item["id"], dict) and "videoId" in item["id"]
#                 else item.get("id")
#             )
#             if not vid:
#                 continue
#             title = item["snippet"]["title"]
#             thumbnail = item["snippet"]["thumbnails"].get("high", {}).get("url", "")
#             results.append({
#                 "id": vid,
#                 "title": title,
#                 "video_url": f"https://www.youtube.com/watch?v={vid}",
#                 "thumbnail": thumbnail
#             })

#             if len(results) >= MAX_RESULTS_PER_CATEGORY:
#                 break

#         next_page_token = resp.get("nextPageToken")
#         if not next_page_token:
#             break

#     random.shuffle(results)
#     return results


# # ---- API Route: Songs ----
# @app.route("/songs")
# def get_songs():
#     cache_key = "songs_pool"
#     cached = cache_get(cache_key)
#     if cached:
#         return jsonify(cached), 200

#     try:
#         all_categories = {}
#         for cat_name, cat_info in MUSIC_CATEGORIES.items():
#             all_categories[cat_name] = fetch_videos_for_category(cat_name, cat_info)

#         # Save to memory + file
#         cache_setex(cache_key, 7200, all_categories)
#         save_cache_to_file(all_categories)

#         return jsonify(all_categories), 200

#     except Exception as e:
#         print(f"API Error: {e}")
#         # Fallback to file cache
#         fallback = load_cache_from_file()
#         if fallback:
#             return jsonify(fallback), 200
#         else:
#             return jsonify({"error": "Failed to fetch songs and no cache available"}), 500


# # ---- API Route: Play Stream URL ----
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
#     import os
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port, debug=True)
from flask import Flask, jsonify
import requests
import time
import yt_dlp
import random
import json
import os

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

# ---- File-based cache ----
CACHE_FILE = "songs_cache.json"

def save_cache_to_file(data):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving cache file: {e}")

def load_cache_from_file():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading cache file: {e}")
    return None

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
MAX_RESULTS_PER_CATEGORY = 400
MAX_RESULTS_PER_PAGE = 50

# ---- Helper: Fetch YouTube Videos ----
def fetch_videos_for_category(cat_name, cat_info):
    results = []
    next_page_token = None

    while len(results) < MAX_RESULTS_PER_CATEGORY:
        try:
            if "chart" in cat_info:
                params = {
                    "part": "snippet,contentDetails,statistics",
                    "chart": cat_info["chart"],
                    "regionCode": "US",
                    "videoCategoryId": cat_info.get("videoCategoryId", "10"),
                    "maxResults": MAX_RESULTS_PER_PAGE,
                    "pageToken": next_page_token,
                    "key": YOUTUBE_API_KEY
                }
                resp = requests.get(VIDEO_URL, params=params).json()
                items = resp.get("items", [])

            else:
                params = {
                    "part": "snippet",
                    "q": cat_info["query"],
                    "type": "video",
                    "order": "viewCount",
                    "regionCode": "US",
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
            return results

    random.shuffle(results)
    return results

# ---- API Route: Songs ----
@app.route("/songs")
def get_songs():
    cache_key = "songs_pool"
    cached = cache_get(cache_key)
    if cached:
        return jsonify(cached), 200

    backup_data = load_cache_from_file() or {}
    all_categories = {}

    try:
        for cat_name, cat_info in MUSIC_CATEGORIES.items():
            videos = fetch_videos_for_category(cat_name, cat_info)

            # If any non-Trending category is empty → fallback to cache
            if cat_name != "Trending" and not videos:
                print(f"Category '{cat_name}' empty, returning cached data")
                return jsonify(backup_data), 200

            all_categories[cat_name] = videos

        # Save to memory + file
        cache_setex(cache_key, 7200, all_categories)
        save_cache_to_file(all_categories)
        return jsonify(all_categories), 200

    except Exception as e:
        print(f"API Error: {e}")
        if backup_data:
            return jsonify(backup_data), 200
        else:
            return jsonify({"error": "Failed to fetch songs and no cache available"}), 500

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
            "noplaylist": True,
            "force_ipv4": True,
             "source_address": "192.168.88.3" 
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
import requests

@app.route("/myip")
def myip():
    ip = requests.get("https://ifconfig.me", timeout=5).text
    return jsonify({"ip_seen_by_websites": ip})
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
