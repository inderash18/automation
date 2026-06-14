import os
import argparse
from dotenv import load_dotenv

# Load env variables from .env if present
load_dotenv()

def generate_script(topic: str, style: str, duration: str, output_path: str):
    """
    Generates a narrator-only script for short-form videos using Gemini API.
    """
    print(f"Generating script for topic: '{topic}' in style: '{style}'...")

    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n[Error] GEMINI_API_KEY environment variable is not set.")
        print("Please create a '.env' file in the workspace or export the environment variable.")
        print("Example .env file content:")
        print("GEMINI_API_KEY=your_gemini_api_key_here\n")
        raise ValueError("Missing GEMINI_API_KEY environment variable.")

    try:
        from google import genai
        # Initialize client with explicitly loaded api_key if needed,
        # otherwise the SDK pulls it from the environment variable GEMINI_API_KEY.
        client = genai.Client(api_key=api_key)
    except ImportError:
        # Fallback if there is an issue with google-genai import
        print("[Warning] Could not import google-genai. Attempting fallback to google-generativeai...")
        import google.generativeai as genai_legacy
        genai_legacy.configure(api_key=api_key)
        
        # We will use the legacy method below in the try/except
        client = None

    prompt = (
        f"Write a spoken narrator-only script for a short video (e.g., YouTube Shorts/Instagram Reels) on the topic: '{topic}'.\n"
        f"The style of the video should be: '{style}'.\n"
        f"The video length should target approximately: {duration}.\n"
        f"Guidelines:\n"
        f"1. Start with a powerful hook in the first 3 seconds to capture attention.\n"
        f"2. Keep the script concise, engaging, and fast-paced.\n"
        f"3. Do NOT include any stage directions, director notes, visual cues, scene descriptions, sound effect cues, or formatting in brackets (e.g., no [Visual of Earth], [Music fades], [Host smiles], or 'Narrator:').\n"
        f"4. Output ONLY the words that the narrator will speak out loud. The output must be raw, continuous speech that can be fed directly into a text-to-speech engine.\n"
        f"5. End with a brief call to action."
    )

    if client:
        # Using new google-genai library
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        script_text = response.text
    else:
        # Legacy fallback
        model = genai_legacy.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        script_text = response.text

    # Clean up markdown formatting if the model wrapped it in backticks
    if script_text.startswith("```"):
        # Remove starting ```text or ```
        lines = script_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        script_text = "\n".join(lines)
    
    script_text = script_text.strip()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(script_text)

    print(f"Script successfully written to: {output_path}")
    print("\n--- Script Output ---")
    print(script_text)
    print("----------------------\n")
    return script_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate narrator script using Gemini API.")
    parser.add_argument("--topic", type=str, required=True, help="Topic for the script")
    parser.add_argument("--style", type=str, default="engaging, informative, fast-paced", help="Style of narration")
    parser.add_argument("--duration", type=str, default="60 seconds", help="Target duration (e.g. 30s, 60s)")
    parser.add_argument("--output", type=str, default="assets/script.txt", help="Path to save the output script")
    args = parser.parse_args()

    try:
        generate_script(args.topic, args.style, args.duration, args.output)
    except Exception as e:
        print(f"Failed to generate script: {e}")
        exit(1)
