import os
import argparse
import requests
from dotenv import load_dotenv

# Load env variables from .env if present
load_dotenv()

def get_installed_ollama_models(ollama_tags_url: str):
    """
    Queries Ollama to get the list of installed models.
    Returns a list of model names or None if Ollama is unreachable.
    """
    try:
        # standard Ollama tags endpoint is /api/tags
        url = ollama_tags_url.replace("/generate", "/tags")
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            models_data = response.json().get("models", [])
            return [m["name"] for m in models_data]
    except Exception:
        pass
    return None

def generate_script(topic: str, style: str, duration: str, output_path: str, ollama_model: str = "llama3.1", ollama_url: str = "http://localhost:11434/api/generate", only_ollama: bool = False):
    """
    Generates a narrator-only script for short-form videos.
    Optionally enforces Ollama-only or falls back to Gemini.
    Provides detailed error diagnostics for local Ollama runs.
    """
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

    script_text = None
    ollama_error_msg = None

    # 1. Attempt to generate using local Ollama
    # First, verify if Ollama is running and has the requested model
    installed_models = get_installed_ollama_models(ollama_url)
    
    if installed_models is None:
        ollama_error_msg = (
            f"Could not connect to Ollama at '{ollama_url}'.\n"
            f"-> Please ensure the Ollama application is running on your computer.\n"
            f"-> You can launch it by search-opening 'Ollama' from the Windows Start menu."
        )
    else:
        # Check if the requested model is installed
        # Match base name (e.g. 'llama3' should match 'llama3:latest' or 'llama3')
        model_found = False
        for m in installed_models:
            if m == ollama_model or m.split(":")[0] == ollama_model:
                model_found = True
                ollama_model = m  # Use the fully qualified name (like llama3:latest)
                break
                
        if not model_found:
            ollama_error_msg = (
                f"Ollama is running, but model '{ollama_model}' is not installed.\n"
                f"-> Available local models: {installed_models}\n"
                f"-> To install the model, open your terminal (cmd/powershell) and run:\n"
                f"   ollama pull {ollama_model}\n"
                f"-> Alternatively, run this script using one of your installed models."
            )
        else:
            try:
                print(f"Generating script using local Ollama model: '{ollama_model}'...")
                payload = {
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False
                }
                response = requests.post(ollama_url, json=payload, timeout=120)
                if response.status_code == 200:
                    result = response.json()
                    script_text = result.get("response", "").strip()
                    if script_text:
                        print("Script successfully generated using Ollama.")
                else:
                    ollama_error_msg = f"Ollama API returned HTTP {response.status_code}: {response.text}"
            except Exception as e:
                ollama_error_msg = f"Failed to query Ollama API: {e}"

    # 2. Check if we need to fall back or fail
    if not script_text:
        if only_ollama:
            print("\n[Error] Script generation failed using Ollama, and '--only-ollama' is enabled.")
            print(ollama_error_msg)
            raise RuntimeError("Ollama execution failed.")
        else:
            print(f"\n[Info] Ollama check failed:\n{ollama_error_msg}")
            print("\nFalling back to Gemini API...")
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print("\n[Error] GEMINI_API_KEY environment variable is not set.")
                print("Please create a '.env' file in the workspace or export the environment variable.")
                print("Example .env file content:")
                print("GEMINI_API_KEY=your_gemini_api_key_here\n")
                raise ValueError("Ollama failed and missing GEMINI_API_KEY for fallback.")

            try:
                from google import genai
                client = genai.Client(api_key=api_key)
            except ImportError:
                print("[Warning] Could not import google-genai. Fallback to google-generativeai...")
                import google.generativeai as genai_legacy
                genai_legacy.configure(api_key=api_key)
                client = None

            if client:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                script_text = response.text
            else:
                model = genai_legacy.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                script_text = response.text

    # Clean up markdown formatting if the model wrapped it in backticks
    if script_text.startswith("```"):
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
    parser = argparse.ArgumentParser(description="Generate narrator script using Ollama or Gemini.")
    parser.add_argument("--topic", type=str, required=True, help="Topic for the script")
    parser.add_argument("--style", type=str, default="engaging, informative, fast-paced", help="Style of narration")
    parser.add_argument("--duration", type=str, default="60 seconds", help="Target duration (e.g. 30s, 60s)")
    parser.add_argument("--output", type=str, default="assets/script.txt", help="Path to save the output script")
    parser.add_argument("--ollama-model", type=str, default="llama3.1", help="Local Ollama model to try first")
    parser.add_argument("--ollama-url", type=str, default="http://localhost:11434/api/generate", help="Ollama generation API URL")
    parser.add_argument("--only-ollama", action="store_true", help="Force only Ollama usage (no Gemini fallback)")
    args = parser.parse_args()

    try:
        generate_script(
            topic=args.topic,
            style=args.style,
            duration=args.duration,
            output_path=args.output,
            ollama_model=args.ollama_model,
            ollama_url=args.ollama_url,
            only_ollama=args.only_ollama
        )
    except Exception as e:
        print(f"Failed to generate script: {e}")
        exit(1)
