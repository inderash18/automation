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
    # size is (width, height)
    if hasattr(clip, "resized"):
        return clip.resized(size)
    if hasattr(clip, "resize"):
        return clip.resize(size)
    # Fallback just in case
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
            # First line is index, second line is timecode, rest is text
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
        # Measure text width
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

def render_subtitle_image(text: str, width: int, height: int, font_size: int, highlight_color: str = "#FFD700"):
    """
    Renders text to a transparent PIL Image.
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = find_font(font_size)

    # Set maximum width for text (80% of video width)
    max_text_width = int(width * 0.8)
    lines = wrap_text(text, font, max_text_width, draw)

    # Calculate height of all lines combined
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])
        
    total_text_height = sum(line_heights) + (len(lines) - 1) * 10 # 10px spacing
    
    # Position text at ~65% height of the video (standard for TikTok/Reels)
    start_y = int(height * 0.65) - (total_text_height // 2)

    current_y = start_y
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (width - w) // 2
        
        # Add stroke outline (8% of font size)
        stroke_w = max(1, int(font_size * 0.08))
        
        # Draw text with outline
        # Color: Highlight the entire subtitle in yellow/gold, or keep it white
        text_color = "white"
        if i == len(lines) - 1 or len(lines) == 1:
            # Highlight final line/words to emphasize spoken parts
            text_color = highlight_color

        draw.text(
            (x, current_y),
            line,
            font=font,
            fill=text_color,
            stroke_width=stroke_w,
            stroke_fill="black",
            align="center"
        )
        current_y += h + 10 # move down for next line

    return img

def create_animated_fallback_bg(duration: float, width: int, height: int):
    """
    Creates a beautiful, slowly animating gradient background using Pillow and MoviePy.
    """
    print("Background video (bg.mp4) not found. Generating an animated gradient fallback background...")
    
    def make_frame(t):
        phase = t * 0.5 # speed of movement
        
        # Slow breathing colors (Dark Violet/Blue space theme)
        r1 = int(25 + 15 * math.sin(phase))
        g1 = int(15 + 10 * math.cos(phase))
        b1 = int(45 + 15 * math.cos(phase))
        
        r2 = int(10 + 5 * math.cos(phase))
        g2 = int(35 + 15 * math.sin(phase))
        b2 = int(55 + 20 * math.sin(phase))
        
        # Build 8x8 low-res grid for fast generation
        grid = np.zeros((8, 8, 3), dtype=np.uint8)
        for y in range(8):
            for x in range(8):
                # Interpolate from top-left to bottom-right
                factor = (x + y) / 14.0
                grid[y, x, 0] = int(r1 + (r2 - r1) * factor)
                grid[y, x, 1] = int(g1 + (g2 - g1) * factor)
                grid[y, x, 2] = int(b1 + (b2 - b1) * factor)
                
        # Resize low-res grid to full scale using Bilinear interpolation for smooth look
        img = Image.fromarray(grid)
        img_resized = img.resize((width, height), Image.Resampling.BILINEAR)
        return np.array(img_resized)

    # In v2 we construct first and set duration
    clip = VideoClip(make_frame)
    return with_duration(clip, duration)

def build_video(bg_path: str, audio_path: str, srt_path: str, output_path: str, width: int = 1080, height: int = 1920, font_size: int = 60):
    """
    Composites the video background, voiceover audio, and Pillow-rendered subtitles.
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
        
        # Loop background if it's shorter than audio
        if bg_clip.duration < duration:
            print("Background video is shorter than audio. Looping background...")
            # We construct loops manually to avoid moviepy loop function quirks
            n_loops = int(np.ceil(duration / bg_clip.duration))
            bg_clip = subclipped(concatenate_videoclips([bg_clip] * n_loops), 0, duration)
        else:
            bg_clip = subclipped(bg_clip, 0, duration)
            
        # Resize background to target resolution
        bg_clip = resized(bg_clip, (width, height))
    else:
        bg_clip = create_animated_fallback_bg(duration, width, height)

    # Set audio to background
    bg_clip = with_audio(bg_clip, audio_clip)

    # 3. Process Subtitles
    subtitles = parse_srt(srt_path)
    print(f"Parsed {len(subtitles)} subtitle clips.")
    
    txt_clips = []
    for sub in subtitles:
        start_time = sub["start"]
        end_time = sub["end"]
        text = sub["text"]
        
        if end_time <= start_time:
            continue
            
        # Render transparent PIL Image of subtitles
        sub_img = render_subtitle_image(text, width, height, font_size)
        
        # Convert PIL RGBA to MoviePy ImageClip with Mask
        sub_rgb = sub_img.convert("RGB")
        sub_alpha = sub_img.split()[-1]
        
        mask_array = np.array(sub_alpha) / 255.0
        mask_clip = make_mask_clip(mask_array)
        mask_clip = with_duration(mask_clip, end_time - start_time)
        
        txt_clip = ImageClip(np.array(sub_rgb))
        txt_clip = with_duration(txt_clip, end_time - start_time)
        txt_clip = with_mask(txt_clip, mask_clip)
        txt_clip = with_start(txt_clip, start_time)
        
        txt_clips.append(txt_clip)

    # 4. Composite and Export
    print("Compositing video and subtitle overlays...")
    final_video = CompositeVideoClip([bg_clip] + txt_clips)
    
    print(f"Writing final video to: {output_path}...")
    # Ensure folder exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Write file with high performance preset and standard aac audio codec
    final_video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        logger="bar"
    )
    
    # Close clips
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
