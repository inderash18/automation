import os
import sys
import textwrap
from PIL import Image, ImageDraw, ImageFont

# Monkeypatch Pillow for compatibility with older MoviePy versions
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import numpy as np
from dotenv import load_dotenv

# Load moviepy modules
from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy.video.fx.crop import crop
from moviepy.video.fx.loop import loop

load_dotenv()

def time_to_seconds(t_str: str) -> float:
    """Converts a SRT/VTT timestamp to float seconds."""
    t_str = t_str.strip().replace(",", ".")
    parts = t_str.split(":")
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    elif len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    try:
        return float(t_str)
    except ValueError:
        return 0.0

def parse_srt(srt_path: str) -> list:
    """Parses an SRT file and returns a list of dictionaries with start, end, and text."""
    if not os.path.exists(srt_path):
        print(f"Warning: SRT file {srt_path} does not exist. Captions will be estimated.", file=sys.stderr)
        return []
    
    segments = []
    try:
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading SRT file {srt_path}: {e}", file=sys.stderr)
        return []
        
    lines = content.splitlines()
    current_start = None
    current_end = None
    current_text = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_start is not None and current_text:
                segments.append({
                    "start": current_start,
                    "end": current_end,
                    "text": " ".join(current_text)
                })
                current_start = None
                current_end = None
                current_text = []
            continue
            
        if line.isdigit():
            # Skip SRT index numbers
            continue
            
        if "-->" in line:
            parts = line.split("-->")
            try:
                current_start = time_to_seconds(parts[0])
                current_end = time_to_seconds(parts[1])
            except Exception:
                pass
        else:
            current_text.append(line)
            
    # Capture the last segment
    if current_start is not None and current_text:
        segments.append({
            "start": current_start,
            "end": current_end,
            "text": " ".join(current_text)
        })
        
    return segments

def get_fallback_segments(script: str, total_duration: float) -> list:
    """Generates linear timestamped segments from the raw script when no VTT is available."""
    words = script.split()
    if not words:
        return []
        
    # Group words into chunks of 3 for quick-reading Shorts subtitles
    chunk_size = 3
    segments = []
    words_per_sec = len(words) / total_duration
    
    for i in range(0, len(words), chunk_size):
        chunk = words[i:i + chunk_size]
        text = " ".join(chunk)
        start_time = i / words_per_sec
        end_time = min((i + chunk_size) / words_per_sec, total_duration)
        segments.append({
            "start": start_time,
            "end": end_time,
            "text": text
        })
    return segments

def get_system_font(font_size: int):
    """Searches common operating system locations for a clean, thick font."""
    font_paths = [
        "C:/Windows/Fonts/impact.ttf",        # Impact - Very popular for Shorts
        "C:/Windows/Fonts/arialbd.ttf",       # Arial Bold
        "C:/Windows/Fonts/trebucbd.ttf",      # Trebuchet MS Bold
        "C:/Windows/Fonts/comicbd.ttf",       # Comic Sans Bold
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, font_size)
            except Exception:
                continue
    # Fallback to Pillow default
    try:
        return ImageFont.load_default(size=font_size)
    except TypeError:
        # Older pillow versions don't support size in load_default
        return ImageFont.load_default()

def draw_text_with_outline(draw, text, cx, cy, font, text_color, outline_color, outline_width):
    """Draws centered multiline text with a bold outline for readability."""
    lines = text.split("\n")
    
    # Calculate dimensions and draw line by line
    line_heights = []
    line_widths = []
    for line in lines:
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
        except AttributeError:
            # Fallback for older Pillow
            w, h = draw.textsize(line, font=font)
        line_widths.append(w)
        line_heights.append(h)
        
    total_height = sum(line_heights) + 6 * (len(lines) - 1)
    
    # Start drawing from top of the block
    current_y = cy - total_height // 2
    
    for i, line in enumerate(lines):
        w = line_widths[i]
        h = line_heights[i]
        lx = cx - w // 2
        
        # Draw outline
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((lx + dx, current_y + dy), line, font=font, fill=outline_color)
                    
        # Draw main text
        draw.text((lx, current_y), line, font=font, fill=text_color)
        current_y += h + 6

def build_video(bg_path: str, audio_path: str, script: str, output_path: str) -> bool:
    """
    Combines the background video and voiceover audio.
    Applies vertical cropping, trims to match audio duration (max 30s),
    and burns in uppercase centered captions using Pillow.
    """
    try:
        print(f"Loading files in MoviePy...", flush=True)
        # Load audio clip
        audio_clip = AudioFileClip(audio_path)
        audio_duration = min(audio_clip.duration, 30.0) # Capped at 30 seconds
        audio_clip = audio_clip.subclip(0, audio_duration)

        # Load video clip
        video_clip = VideoFileClip(bg_path)
        
        # Loop video if it is shorter than the audio
        if video_clip.duration < audio_duration:
            print(f"Background video ({video_clip.duration:.1f}s) is shorter than audio ({audio_duration:.1f}s). Looping video...", flush=True)
            video_clip = loop(video_clip, duration=audio_duration)
        else:
            video_clip = video_clip.subclip(0, audio_duration)

        # Apply target resolution: 720x1280 (9:16 portrait)
        target_w, target_h = 720, 1280
        
        # Scale to cover the target resolution
        scale_factor = max(target_w / video_clip.w, target_h / video_clip.h)
        print(f"Rescaling background video from {video_clip.w}x{video_clip.h} (scale: {scale_factor:.3f})...", flush=True)
        video_resized = video_clip.resize(scale_factor)
        
        # Center crop to target dimensions
        x_center = video_resized.w / 2
        y_center = video_resized.h / 2
        video_cropped = crop(
            video_resized,
            x_center=x_center,
            y_center=y_center,
            width=target_w,
            height=target_h
        )
        
        # Read and prepare subtitles
        srt_path = os.path.splitext(audio_path)[0] + ".srt"
        segments = parse_srt(srt_path)
        if not segments:
            segments = get_fallback_segments(script, audio_duration)
            
        print(f"Loaded {len(segments)} subtitle segments. Beginning rendering...", flush=True)
        
        # Load font once
        font_size = int(target_w * 0.075) # 7.5% of width is ideal for Shorts text readability
        font = get_system_font(font_size)

        # Function to process each frame and burn-in text
        def add_captions(frame_img, t):
            # Find the active segment
            active_text = ""
            for seg in segments:
                if seg["start"] <= t <= seg["end"]:
                    active_text = seg["text"].strip().upper() # Uppercase looks very premium
                    break
                    
            if not active_text:
                return frame_img
                
            # Convert frame numpy array to PIL Image
            img = Image.fromarray(frame_img)
            draw = ImageDraw.Draw(img)
            
            # Wrap text to ensure it stays in screen boundaries
            wrapped_text = "\n".join(textwrap.wrap(active_text, width=15))
            
            # Subtitles centered horizontally, and ~60% down the screen (above Shorts overlays)
            cx = target_w // 2
            cy = int(target_h * 0.60)
            
            # Draw uppercase yellow text with black stroke
            text_color = (255, 242, 0)      # High-visibility neon yellow
            outline_color = (0, 0, 0)      # Deep black border
            outline_width = 4
            
            draw_text_with_outline(draw, wrapped_text, cx, cy, font, text_color, outline_color, outline_width)
            
            return np.array(img)

        # Apply the frame processing function
        final_video = video_cropped.fl(lambda gf, t: add_captions(gf(t), t))
        
        # Set audio
        final_video = final_video.set_audio(audio_clip)

        # Create output directory
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Write final file
        print(f"Writing final video file to: {output_path}...", flush=True)
        final_video.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            logger=None  # Suppress moviepy stdout logs
        )
        
        # Release resources
        final_video.close()
        video_clip.close()
        audio_clip.close()
        
        print(f"Video synthesis complete! Saved to: {output_path}", flush=True)
        return True
        
    except Exception as e:
        print(f"Error in video generation pipeline: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test video builder
    bg = "output/test_bg.mp4"
    audio = "output/test_voice.mp3"
    script = "This is a test script with subtitles overlaying the video."
    output = "output/final.mp4"
    if os.path.exists(bg) and os.path.exists(audio):
        success = build_video(bg, audio, script, output)
        print(f"Video builder test status: {success}")
    else:
        print("Test background or audio file is missing. Run stock.py and voice.py first.")
