import os
import re
import math
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Try importing from the new MoviePy v2.x path, fall back to v1.x
try:
    from moviepy import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, VideoClip, concatenate_videoclips
except ImportError:
    from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, VideoClip, concatenate_videoclips

# Compatibility wrappers for MoviePy v1.x and v2.x
def with_duration(clip, duration):
    return clip.with_duration(duration) if hasattr(clip, "with_duration") else clip.set_duration(duration)

def with_audio(clip, audio_clip):
    return clip.with_audio(audio_clip) if hasattr(clip, "with_audio") else clip.set_audio(audio_clip)

def with_start(clip, start_time):
    return clip.with_start(start_time) if hasattr(clip, "with_start") else clip.set_start(start_time)

def with_mask(clip, mask_clip):
    return clip.with_mask(mask_clip) if hasattr(clip, "with_mask") else clip.set_mask(mask_clip)

def subclipped(clip, start_time, end_time):
    return clip.subclipped(start_time, end_time) if hasattr(clip, "subclipped") else clip.subclip(start_time, end_time)

def make_mask_clip(mask_array):
    try:
        return ImageClip(mask_array, is_mask=True)
    except TypeError:
        return ImageClip(mask_array, ismask=True)

def resized(clip, size):
    if hasattr(clip, "resized"):
        return clip.resized(size)
    if hasattr(clip, "resize"):
        return clip.resize(size)
    return clip

def parse_srt(srt_path: str):
    """
    Parses a standard SRT file into a list of subtitle dictionaries.
    Each dictionary has: 'start', 'end', and 'text'.
    """
    if not os.path.exists(srt_path):
        print(f"[Warning] SRT file not found at: {srt_path}")
        return []

    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # Split into blocks by blank lines
    blocks = re.split(r'\n\s*\n', content)
    subtitles = []

    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) >= 3:
            timecode = lines[1]
            text = " ".join(lines[2:])
            
            # Parse times: e.g. 00:00:01,120 --> 00:00:03,450
            match = re.match(r'(\d+):(\d+):(\d+),(\d+)\s*-->\s*(\d+):(\d+):(\d+),(\d+)', timecode)
            if match:
                g = match.groups()
                start_sec = int(g[0])*3600 + int(g[1])*60 + int(g[2]) + int(g[3])/1000.0
                end_sec = int(g[4])*3600 + int(g[5])*60 + int(g[6]) + int(g[7])/1000.0
                
                subtitles.append({
                    "start": start_sec,
                    "end": end_sec,
                    "text": text
                })
    
    return subtitles

def wrap_text(text: str, font, max_width: int, draw: ImageDraw.ImageDraw):
    """
    Wraps text into lines that fit within a given maximum pixel width.
    """
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                
    if current_line:
        lines.append(" ".join(current_line))
        
    return lines

def find_font(font_size: int):
    """
    Looks for common bold/impactful fonts on Windows, falling back to default.
    """
    possible_paths = [
        "C:\\Windows\\Fonts\\impact.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, font_size)
            except Exception:
                continue
    return ImageFont.load_default()

def create_animated_fallback_bg(duration: float, width: int, height: int):
    """
    Creates a beautiful, slowly animating gradient background.
    """
    print("Background video (bg.mp4) not found. Generating animated gradient background...")
    
    def make_frame(t):
        phase = t * 0.5
        r1 = int(25 + 15 * math.sin(phase))
        g1 = int(15 + 10 * math.cos(phase))
        b1 = int(45 + 15 * math.cos(phase))
        
        r2 = int(10 + 5 * math.cos(phase))
        g2 = int(35 + 15 * math.sin(phase))
        b2 = int(55 + 20 * math.sin(phase))
        
        grid = np.zeros((8, 8, 3), dtype=np.uint8)
        for y in range(8):
            for x in range(8):
                factor = (x + y) / 14.0
                grid[y, x, 0] = int(r1 + (r2 - r1) * factor)
                grid[y, x, 1] = int(g1 + (g2 - g1) * factor)
                grid[y, x, 2] = int(b1 + (b2 - b1) * factor)
                
        img = Image.fromarray(grid)
        img_resized = img.resize((width, height), Image.Resampling.BILINEAR)
        return np.array(img_resized)

    clip = VideoClip(make_frame)
    return with_duration(clip, duration)

def build_video(bg_path: str, audio_path: str, srt_path: str, output_path: str, width: int = 1080, height: int = 1920, font_size: int = 60, highlight_color: str = "#FFD700"):
    """
    Composites the video background and voiceover audio.
    Optimized: Pre-renders subtitles into a single composite VideoClip layer to prevent MoviePy lag.
    Approximate word-level timings are derived from sentence timings to show dynamic captions.
    """
    print(f"Building video composition...")
    
    # 1. Load Audio
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    print(f"Audio duration: {duration:.2f} seconds")

    # 2. Load or Create Background Video
    if bg_path and os.path.exists(bg_path):
        print(f"Loading background video: {bg_path}")
        bg_clip = VideoFileClip(bg_path)
        
        if bg_clip.duration < duration:
            print("Background video is shorter than audio. Looping background...")
            n_loops = int(np.ceil(duration / bg_clip.duration))
            bg_clip = subclipped(concatenate_videoclips([bg_clip] * n_loops), 0, duration)
        else:
            bg_clip = subclipped(bg_clip, 0, duration)
            
        bg_clip = resized(bg_clip, (width, height))
    else:
        bg_clip = create_animated_fallback_bg(duration, width, height)

    bg_clip = with_audio(bg_clip, audio_clip)

    # 3. Pre-process Subtitle Word Timings
    subtitles = parse_srt(srt_path)
    print(f"Parsed {len(subtitles)} subtitle sentences.")
    
    for sub in subtitles:
        sub["words"] = sub["text"].split()
        sub["duration"] = sub["end"] - sub["start"]

    # 4. Single-Layer Pre-rendered Subtitles with Caching & Word Highlighting
    frame_cache = {}
    font = find_font(font_size)

    def render_subtitle_layer_frame(t):
        # Find active sentence
        active_sub = None
        sub_idx = -1
        for i, sub in enumerate(subtitles):
            if sub["start"] <= t <= sub["end"]:
                active_sub = sub
                sub_idx = i
                break
                
        if not active_sub or not active_sub["words"]:
            # Transparent frame
            return np.zeros((height, width, 4), dtype=np.uint8)
            
        words = active_sub["words"]
        num_words = len(words)
        
        # Approximate word index based on linear interpolation over sentence duration
        rel_t = t - active_sub["start"]
        word_duration = active_sub["duration"] / num_words
        active_word_idx = min(int(rel_t / word_duration), num_words - 1)
        
        # Check cache
        cache_key = (sub_idx, active_word_idx)
        if cache_key in frame_cache:
            return frame_cache[cache_key]
            
        # Draw subtitles with Pillow
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Word wrapping layout
        lines_words = []
        current_line = []
        max_text_width = int(width * 0.8)
        
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            if w <= max_text_width:
                current_line.append(word)
            else:
                if current_line:
                    lines_words.append(current_line)
                    current_line = [word]
                else:
                    lines_words.append([word])
        if current_line:
            lines_words.append(current_line)
            
        # Calculate total paragraph height
        line_heights = []
        for line in lines_words:
            line_str = " ".join(line)
            bbox = draw.textbbox((0, 0), line_str, font=font)
            line_heights.append(bbox[3] - bbox[1])
        total_height = sum(line_heights) + (len(lines_words) - 1) * 10
        
        # Position text at ~65% height of the video canvas
        current_y = int(height * 0.65) - (total_height // 2)
        stroke_w = max(1, int(font_size * 0.08))
        
        global_word_idx = 0
        for line in lines_words:
            word_widths = []
            for word in line:
                bbox = draw.textbbox((0, 0), word, font=font)
                word_widths.append(bbox[2] - bbox[0])
                
            space_bbox = draw.textbbox((0, 0), " ", font=font)
            space_width = space_bbox[2] - space_bbox[0]
            line_height = draw.textbbox((0, 0), " ".join(line), font=font)[3] - draw.textbbox((0, 0), " ".join(line), font=font)[1]
            
            total_line_width = sum(word_widths) + space_width * (len(line) - 1)
            current_x = (width - total_line_width) // 2
            
            for w_i, word in enumerate(line):
                is_active = (global_word_idx == active_word_idx)
                text_color = highlight_color if is_active else "white"
                
                draw.text(
                    (current_x, current_y),
                    word,
                    font=font,
                    fill=text_color,
                    stroke_width=stroke_w,
                    stroke_fill="black"
                )
                current_x += word_widths[w_i] + space_width
                global_word_idx += 1
                
            current_y += line_height + 10
            
        frame_array = np.array(img)
        frame_cache[cache_key] = frame_array
        return frame_array

    # Split RGBA generator into separate RGB and Mask tracks for MoviePy performance
    def make_subtitle_rgb(t):
        return render_subtitle_layer_frame(t)[:, :, :3]

    def make_subtitle_mask(t):
        return render_subtitle_layer_frame(t)[:, :, 3] / 255.0

    print("Pre-rendering optimized subtitle layers...")
    sub_rgb_clip = VideoClip(make_subtitle_rgb)
    sub_rgb_clip = with_duration(sub_rgb_clip, duration)
    
    sub_mask_clip = VideoClip(make_subtitle_mask, is_mask=True)
    sub_mask_clip = with_duration(sub_mask_clip, duration)
    
    subtitle_clip = with_mask(sub_rgb_clip, sub_mask_clip)

    # 5. Composite and Export
    print("Compositing background track and subtitle track...")
    final_video = CompositeVideoClip([bg_clip, subtitle_clip])
    
    print(f"Writing final video to: {output_path}...")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    final_video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",  # Fast compression preset for automation
        logger="bar"
    )
    
    bg_clip.close()
    audio_clip.close()
    final_video.close()
    print("Video building completed successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create final video by overlaying audio and subtitles on background.")
    parser.add_argument("--bg", type=str, default="assets/bg.mp4", help="Path to background video (optional)")
    parser.add_argument("--audio", type=str, default="assets/voice.mp3", help="Path to input audio file")
    parser.add_argument("--srt", type=str, default="assets/voice.srt", help="Path to input SRT file")
    parser.add_argument("--output", type=str, default="assets/final.mp4", help="Path to save final output video")
    parser.add_argument("--width", type=int, default=1080, help="Video width")
    parser.add_argument("--height", type=int, default=1920, help="Video height")
    parser.add_argument("--font-size", type=int, default=60, help="Font size of subtitles")
    args = parser.parse_args()

    try:
        build_video(
            bg_path=args.bg,
            audio_path=args.audio,
            srt_path=args.srt,
            output_path=args.output,
            width=args.width,
            height=args.height,
            font_size=args.font_size
        )
    except Exception as e:
        print(f"Failed to build video: {e}")
        exit(1)
