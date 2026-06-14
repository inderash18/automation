import os
import argparse
import asyncio
import edge_tts

async def list_english_voices():
    """Prints all available English voices from Microsoft Edge TTS."""
    voices = await edge_tts.list_voices()
    print("\n--- Available English Voices ---")
    for voice in sorted(voices, key=lambda v: v["Name"]):
        if voice["Locale"].startswith("en-"):
            print(f"Name: {voice['Name']}")
            print(f"  Gender: {voice['Gender']}")
            print(f"  Locale: {voice['Locale']}")
            print(f"  Description: {voice['FriendlyName']}")
            print("-" * 30)

async def text_to_speech(text: str, voice: str, output_audio: str, output_srt: str):
    """
    Converts text to speech and generates synchronized subtitles in SRT format.
    """
    print(f"Converting text to speech using voice: '{voice}'...")
    
    # Ensure directories exist
    os.makedirs(os.path.dirname(os.path.abspath(output_audio)), exist_ok=True)
    if output_srt:
        os.makedirs(os.path.dirname(os.path.abspath(output_srt)), exist_ok=True)

    # Communicate with Edge TTS
    communicate = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()

    with open(output_audio, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] in ["WordBoundary", "SentenceBoundary"] and output_srt:
                submaker.feed(chunk)

    print(f"Audio file saved to: {output_audio}")

    if output_srt:
        srt_content = submaker.get_srt()
        with open(output_srt, "w", encoding="utf-8") as srt_file:
            srt_file.write(srt_content)
        print(f"Subtitles file saved to: {output_srt}")

async def main():
    parser = argparse.ArgumentParser(description="Convert text script to speech and SRT subtitles.")
    parser.add_argument("--text", type=str, help="Text to convert to speech (overrides --input)")
    parser.add_argument("--input", type=str, default="assets/script.txt", help="Path to input text file containing the script")
    parser.add_argument("--voice", type=str, default="en-US-AvaNeural", help="Voice to use (e.g. en-US-AvaNeural, en-US-ChristopherNeural)")
    parser.add_argument("--output-audio", type=str, default="assets/voice.mp3", help="Path to save output audio file")
    parser.add_argument("--output-srt", type=str, default="assets/voice.srt", help="Path to save output SRT file")
    parser.add_argument("--list-voices", action="store_true", help="List all available English voices and exit")
    
    args = parser.parse_args()

    if args.list_voices:
        await list_english_voices()
        return

    # Determine input text
    if args.text:
        text_content = args.text
    else:
        if not os.path.exists(args.input):
            print(f"[Error] Input script file '{args.input}' not found.")
            print("Please run the script generator first or provide text directly using --text.")
            exit(1)
        with open(args.input, "r", encoding="utf-8") as f:
            text_content = f.read().strip()

    if not text_content:
        print("[Error] No text content provided to speak.")
        exit(1)

    try:
        await text_to_speech(text_content, args.voice, args.output_audio, args.output_srt)
    except Exception as e:
        print(f"TTS conversion failed: {e}")
        exit(1)

if __name__ == "__main__":
    # Fix event loop policy for Windows if needed
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
