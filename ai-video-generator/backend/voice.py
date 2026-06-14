import asyncio
import edge_tts
import sys
import os

def generate_voice(text: str, output_path: str, voice: str = "en-US-EmmaNeural") -> bool:
    """
    Converts text to speech using edge-tts.
    Also generates word boundary subtitles and saves them as a .vtt file.
    If it fails, retries once.
    Returns True if successful, False otherwise.
    """
    srt_path = os.path.splitext(output_path)[0] + ".srt"

    async def _tts_communicate():
        communicate = edge_tts.Communicate(text, voice)
        submaker = edge_tts.SubMaker()
        
        with open(output_path, "wb") as fp:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    fp.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.feed(chunk)
                    
        # Write SRT subtitles
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(submaker.get_srt())

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    for attempt in range(1, 3):
        try:
            print(f"Generating voiceover and subtitles with edge-tts (Voice: {voice}), attempt {attempt}...", flush=True)
            
            # edge-tts is async, so we must run it in an event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(_tts_communicate(), loop)
                future.result(timeout=30)
            else:
                loop.run_until_complete(_tts_communicate())
                
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"Successfully generated voiceover at: {output_path}", flush=True)
                if os.path.exists(srt_path):
                    print(f"Successfully generated subtitles at: {srt_path}", flush=True)
                return True
            else:
                raise Exception("Generated audio file is empty or missing.")
                
        except Exception as e:
            print(f"Warning: Text-to-speech failed on attempt {attempt}: {str(e)}", file=sys.stderr)
            if attempt == 1:
                print("Retrying voice generation...", file=sys.stderr)
                # Small delay before retry
                import time
                time.sleep(1)
            else:
                print("Error: All text-to-speech attempts failed.", file=sys.stderr)
                return False

if __name__ == "__main__":
    # Test voice generation
    test_text = "This is a test of the automatic neural text to speech generator. It sounds incredibly realistic!"
    test_output = "output/test_voice.mp3"
    success = generate_voice(test_text, test_output)
    print(f"Voice generation success status: {success}")
    if success and os.path.exists(test_output):
        print(f"File size: {os.path.getsize(test_output)} bytes")
