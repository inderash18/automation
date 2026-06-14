import os
import sys
import shutil

# Reconfigure standard streams to support Unicode output (emojis) on Windows terminals
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv

# Ensure the backend directory is in the python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

# Import module functions
from script_generator import generate_script
from voice import generate_voice
from stock import fetch_stock_video
from video_builder import build_video

# Import optimization functions
from viral_scoring import choose_best
from title_generator import generate_title
from seo import generate_hashtags
from trend_engine import get_trending_topic

# Load env variables
load_dotenv()

# Set up paths relative to project root
BASE_DIR = os.path.dirname(backend_dir)
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# Ensure required directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Initialize Flask app serving frontend as static folder
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

@app.route("/")
def index():
    """Serves the frontend dashboard page."""
    return app.send_static_file("index.html")

@app.route("/trend", methods=["GET"])
def trend():
    """Returns a random trending topic."""
    topic = get_trending_topic()
    return jsonify({"topic": topic})

@app.route("/generate", methods=["POST"])
def generate():
    """
    Triggers the automated Shorts generation pipeline.
    Steps:
    1. Generates 3 script variations (curiosity, secrets, motivational)
    2. Ranks scripts using Viral Scoring Engine and selects the best one
    3. Generates high-retention Title Hook & SEO Hashtags
    4. TTS Audio Conversion on selected script
    5. Pexels Stock Video Fetching (or Dynamic Fallback)
    6. MoviePy Compilation and Caption Rendering
    """
    data = request.get_json()
    if not data or "topic" not in data or not data["topic"].strip():
        return jsonify({"status": "error", "message": "Missing topic in request parameters."}), 400

    topic = data["topic"].strip()
    print(f"\n=== Starting Upgraded Shorts Generation Pipeline for: '{topic}' ===", flush=True)

    # Temporary step files
    temp_voice = os.path.join(TEMP_DIR, "voice.mp3")
    temp_bg = os.path.join(TEMP_DIR, "bg.mp4")
    final_output = os.path.join(OUTPUT_DIR, "final.mp4")

    # Clean previous temp files to avoid caching/mixing
    for path in [temp_voice, os.path.splitext(temp_voice)[0] + ".srt", temp_bg]:
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Warning: Could not remove temp file {path}: {e}", file=sys.stderr)

    try:
        # Step 1: Generate 3 script variations
        scripts = []
        for idx in range(3):
            script_candidate = generate_script(topic, style_index=idx)
            scripts.append(script_candidate)
            
        # Step 2: Choose best script using the Viral Scoring Engine
        best_script, best_score, all_scored = choose_best(scripts)
        print(f"Viral Scorer: Best script chosen with score {best_score}%", flush=True)

        # Step 3: Generate optimized Title Hook and SEO Hashtags
        title = generate_title(topic)
        tags = generate_hashtags(topic)
        tags_str = " ".join(tags)
        print(f"Title Hook: {title}", flush=True)
        print(f"SEO Hashtags: {tags_str}", flush=True)

        # Step 4: Convert script to neural voiceover audio
        voice_success = generate_voice(best_script, temp_voice)
        if not voice_success or not os.path.exists(temp_voice):
            return jsonify({"status": "error", "message": "Failed to synthesize voiceover audio."}), 500

        # Step 5: Fetch vertical stock video
        stock_success = fetch_stock_video(topic, temp_bg)
        if not stock_success or not os.path.exists(temp_bg):
            return jsonify({"status": "error", "message": "Failed to retrieve background stock video."}), 500

        # Step 6: Compile audio, video, and burn captions
        video_success = build_video(temp_bg, temp_voice, best_script, final_output)
        if not video_success or not os.path.exists(final_output):
            return jsonify({"status": "error", "message": "Failed to render and export final video compilation."}), 500

        print("=== Upgraded Shorts Generation Pipeline Completed Successfully! ===\n", flush=True)
        return jsonify({
            "status": "success",
            "message": "Shorts video successfully generated!",
            "video_url": "/download",
            "script": best_script,
            "title": title,
            "hashtags": tags_str,
            "score": best_score
        })

    except Exception as e:
        print(f"Error in generation endpoint: {str(e)}", file=sys.stderr)
        return jsonify({"status": "error", "message": f"Server processing error: {str(e)}"}), 500

import threading
from youtube_uploader import upload_video

# Global dict to track background upload progress
yt_upload_state = {
    "status": "idle",       # "idle", "authenticating", "uploading", "success", "error"
    "message": "",
    "progress": 0,
    "video_id": ""
}
yt_upload_lock = threading.Lock()

def bg_upload_worker(video_path, title, description, tags, privacy_status):
    global yt_upload_state
    
    def progress_callback(percent):
        with yt_upload_lock:
            yt_upload_state["progress"] = percent
            yt_upload_state["status"] = "uploading"
            yt_upload_state["message"] = f"Transferring video to YouTube: {percent}%"
            
    try:
        client_secrets_path = os.path.join(BASE_DIR, "client_secrets.json")
        if not os.path.exists(client_secrets_path):
            with yt_upload_lock:
                yt_upload_state["status"] = "error"
                yt_upload_state["message"] = "client_secrets.json not found in the root folder."
            return
            
        token_path = os.path.join(backend_dir, "token.pickle")
        with yt_upload_lock:
            if not os.path.exists(token_path):
                yt_upload_state["status"] = "authenticating"
                yt_upload_state["message"] = "Please complete Google authorization in the browser window."
            else:
                yt_upload_state["status"] = "uploading"
                yt_upload_state["message"] = "Initializing YouTube API connection..."
                
        video_id = upload_video(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy_status,
            progress_callback=progress_callback
        )
        
        with yt_upload_lock:
            if video_id:
                yt_upload_state["status"] = "success"
                yt_upload_state["message"] = "Video successfully uploaded to YouTube!"
                yt_upload_state["progress"] = 100
                yt_upload_state["video_id"] = video_id
            else:
                yt_upload_state["status"] = "error"
                yt_upload_state["message"] = "YouTube upload failed. Check the server logs."
                
    except Exception as err:
        with yt_upload_lock:
            yt_upload_state["status"] = "error"
            yt_upload_state["message"] = f"Upload failed: {str(err)}"

@app.route("/upload_youtube", methods=["POST"])
def upload_youtube():
    global yt_upload_state
    
    with yt_upload_lock:
        if yt_upload_state["status"] in ["authenticating", "uploading"]:
            return jsonify({"status": "error", "message": "An upload is already in progress."}), 400
            
    data = request.get_json() or {}
    title = data.get("title", "Generated Short").strip()
    description = data.get("description", "").strip()
    privacy = data.get("privacy", "private").strip()
    
    raw_tags = data.get("tags", "")
    tags = []
    for t in raw_tags.replace(",", " ").split(" "):
        cleaned = t.strip().lstrip("#")
        if cleaned:
            tags.append(cleaned)
            
    final_output = os.path.join(OUTPUT_DIR, "final.mp4")
    if not os.path.exists(final_output) or os.path.getsize(final_output) == 0:
        return jsonify({"status": "error", "message": "No compiled final.mp4 video file found."}), 404
        
    with yt_upload_lock:
        yt_upload_state["status"] = "uploading"
        yt_upload_state["message"] = "Spawning upload task thread..."
        yt_upload_state["progress"] = 0
        yt_upload_state["video_id"] = ""
        
    t = threading.Thread(target=bg_upload_worker, args=(final_output, title, description, tags, privacy))
    t.daemon = True
    t.start()
    
    return jsonify({"status": "success", "message": "Upload thread started."})

@app.route("/upload_status", methods=["GET"])
def upload_status():
    global yt_upload_state
    
    client_secrets_path = os.path.join(BASE_DIR, "client_secrets.json")
    secrets_exists = os.path.exists(client_secrets_path)
    
    with yt_upload_lock:
        return jsonify({
            "client_secrets_exist": secrets_exists,
            "status": yt_upload_state["status"],
            "message": yt_upload_state["message"],
            "progress": yt_upload_state["progress"],
            "video_id": yt_upload_state["video_id"]
        })

@app.route("/download", methods=["GET"])
def download():
    """Serves the generated final.mp4 video file for client download."""
    final_output = os.path.join(OUTPUT_DIR, "final.mp4")
    if os.path.exists(final_output) and os.path.getsize(final_output) > 0:
        return send_file(final_output, as_attachment=True, download_name="shorts_video.mp4", mimetype="video/mp4")
    else:
        return jsonify({"status": "error", "message": "No generated video file is available for download."}), 404

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    
    print(f"Starting server in directory: {BASE_DIR}")
    print(f"Serving frontend from: {FRONTEND_DIR}")
    print(f"Output files stored in: {OUTPUT_DIR}")
    
    app.run(host="0.0.0.0", port=port, debug=debug)
