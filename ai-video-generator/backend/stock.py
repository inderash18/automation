import os
import requests
import sys
import math
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

def generate_fallback_video(output_path: str, duration: int = 30) -> bool:
    """
    Generates a beautiful, vertical dynamic color gradient video using MoviePy and Pillow.
    Used when Pexels API is unavailable or search yields no results.
    """
    print(f"Pexels failed/unavailable. Generating dynamic fallback video ({duration}s)...", flush=True)
    try:
        from PIL import Image, ImageDraw
        import numpy as np
        from moviepy.editor import VideoClip
        
        # Dimensions for standard vertical Short: 540x960 (lightweight and renders quickly)
        width, height = 540, 960
        
        def make_frame(t):
            # Create a smooth color animation by cycling RGB values over time t
            img = Image.new("RGB", (width, height))
            draw = ImageDraw.Draw(img)
            
            # Start and end colors cycle slowly
            r1 = int(40 + 30 * math.sin(t * 0.4))
            g1 = int(25 + 20 * math.cos(t * 0.3))
            b1 = int(90 + 30 * math.sin(t * 0.5))
            
            r2 = int(20 + 15 * math.cos(t * 0.5))
            g2 = int(60 + 25 * math.sin(t * 0.4))
            b2 = int(120 + 40 * math.cos(t * 0.3))
            
            # Draw gradient
            for y in range(height):
                ratio = y / height
                r = int(r1 * (1 - ratio) + r2 * ratio)
                g = int(g1 * (1 - ratio) + g2 * ratio)
                b = int(b1 * (1 - ratio) + b2 * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
                
            # Add some subtle animated accent shapes (e.g. glowing circles) to make it dynamic
            # Draw a slow moving glowing circle in the background
            cx = int(width / 2 + (width / 4) * math.sin(t * 0.8))
            cy = int(height / 2 + (height / 5) * math.cos(t * 0.6))
            radius = int(120 + 20 * math.sin(t * 1.2))
            
            # Draw overlay circle with transparency (blend with gradient)
            # Create overlay image
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                fill=(255, 255, 255, int(15 + 5 * math.sin(t)))
            )
            
            # Composite images
            combined = Image.alpha_composite(img.convert("RGBA"), overlay)
            return np.array(combined.convert("RGB"))

        # Build video clip
        clip = VideoClip(make_frame, duration=duration)
        
        # Ensure target folder exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        # Write to file
        clip.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio=False,
            logger=None  # Suppress moviepy output logs
        )
        # Close clip release resources
        clip.close()
        print(f"Dynamic fallback video successfully generated at: {output_path}", flush=True)
        return True
    except Exception as e:
        print(f"Error generating fallback video: {str(e)}", file=sys.stderr)
        return False


def fetch_stock_video(topic: str, output_path: str, duration: int = 30) -> bool:
    """
    Searches Pexels for a portrait video matching the topic and downloads it.
    Falls back to a dynamic color gradient video if Pexels fails.
    """
    # Verify API key is available
    if not PEXELS_API_KEY:
        print("Warning: PEXELS_API_KEY is not set in .env. Falling back to dynamic video generation.", file=sys.stderr)
        return generate_fallback_video(output_path, duration)

    headers = {
        "Authorization": PEXELS_API_KEY
    }
    
    # Query parameters: vertical orientation (portrait) is perfect for Shorts!
    params = {
        "query": topic,
        "per_page": 5,
        "orientation": "portrait"
    }
    
    url = "https://api.pexels.com/videos/search"
    
    try:
        print(f"Searching Pexels API for vertical video with topic: '{topic}'...", flush=True)
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code != 200:
            print(f"Warning: Pexels API returned status code {response.status_code}. Using fallback.", file=sys.stderr)
            return generate_fallback_video(output_path, duration)
            
        data = response.json()
        videos = data.get("videos", [])
        
        if not videos:
            print(f"Warning: No vertical videos found on Pexels for topic '{topic}'. Trying default search query 'abstract'...", file=sys.stderr)
            # Try a broader generic query
            params["query"] = "abstract"
            response = requests.get(url, headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                videos = response.json().get("videos", [])
                
        if not videos:
            print("Warning: No fallback videos found on Pexels either. Using generated fallback.", file=sys.stderr)
            return generate_fallback_video(output_path, duration)
            
        # Select the best matching file link
        download_url = None
        for video in videos:
            video_files = video.get("video_files", [])
            # Sort files by width so we can prefer HD portrait but avoid extremely high 4K resolution (which causes slow processing)
            # Ideal width is 720 to 1080
            video_files = sorted(video_files, key=lambda f: abs(f.get("width", 0) - 720))
            
            for file in video_files:
                # We want standard mp4 format
                if file.get("file_type") == "video/mp4" or "mp4" in file.get("link", "").lower():
                    download_url = file.get("link")
                    break
            if download_url:
                break
                
        if not download_url:
            print("Warning: Could not extract a valid MP4 download link. Using generated fallback.", file=sys.stderr)
            return generate_fallback_video(output_path, duration)
            
        # Download the file
        print(f"Downloading video from Pexels: {download_url[:60]}...", flush=True)
        
        # Ensure parent directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        video_response = requests.get(download_url, stream=True, timeout=30)
        if video_response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=1024 * 1024): # 1MB chunks
                    if chunk:
                        f.write(chunk)
            print(f"Successfully downloaded stock video to: {output_path}", flush=True)
            return True
        else:
            print(f"Warning: Failed to download video file. HTTP status {video_response.status_code}. Using generated fallback.", file=sys.stderr)
            return generate_fallback_video(output_path, duration)
            
    except Exception as e:
        print(f"Warning: Stock video fetching failed with error: {str(e)}. Using generated fallback.", file=sys.stderr)
        return generate_fallback_video(output_path, duration)

if __name__ == "__main__":
    # Test stock video fetching
    test_output = "output/test_bg.mp4"
    success = fetch_stock_video("nature scenery", test_output)
    print(f"Stock video fetch success status: {success}")
    if success and os.path.exists(test_output):
        print(f"File size: {os.path.getsize(test_output)} bytes")
