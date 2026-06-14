import subprocess
import shutil
import random
import sys

def get_fallback_script(topic: str, style_index: int = None) -> str:
    """Generates a viral YouTube Shorts script template matching the topic and style index."""
    topic = topic.strip()
    # Curated templates for various styles
    templates = [
        # Template 1: Curiosity / Mind-blowing
        (
            f"Stop scrolling, because {topic} is about to change everything you know. "
            f"Here is the mind-blowing truth that almost nobody is talking about. "
            f"We are witnessing a massive shift right now, and it's happening faster than anyone predicted. "
            f"In a few years, looking back, this will seem like the turning point. "
            f"The real question is: are you going to adapt, or get left behind? "
            f"Let me know your thoughts in the comments, and follow for more."
        ),
        # Template 2: List / Secrets
        (
            f"This is the dark secret behind {topic} that they don't want you to know. "
            f"First, it's not as simple as it looks, and most people are getting it completely wrong. "
            f"Second, the fast-moving changes are happening in secret right under our noses. "
            f"And third, the future of this is going to affect your daily life sooner than you think. "
            f"Would you try this, or is it too risky? "
            f"Subscribe if you want to stay ahead of the curve."
        ),
        # Template 3: Inspirational / Motivational
        (
            f"What if I told you that {topic} is your ultimate golden opportunity? "
            f"Think about it. The world is evolving, and those who start today are the ones who will lead tomorrow. "
            f"It takes courage to step up, but the rewards are absolutely life-changing. "
            f"Don't wait for the perfect moment—take the moment and make it perfect. "
            f"Are you ready to take the leap, or will you watch from the sidelines? "
            f"Double tap if you agree!"
        )
    ]
    if style_index is not None and 0 <= style_index < len(templates):
        return templates[style_index]
    return random.choice(templates)

def generate_script(topic: str, style_index: int = 0) -> str:
    """
    Generates a viral YouTube Shorts script using local Ollama llama3 model.
    Falls back to a style-specific template if Ollama fails or is not installed.
    """
    styles_instructions = [
        "Focus: Curiosity and mind-blowing twists. Create a massive curiosity gap. Make the hook feel like a mystery that must be solved.",
        "Focus: Secrets and lists. Frame the topic as a secret hack, dark truth, or list of things 'they' don't want the viewer to know.",
        "Focus: Motivational and inspiring. Use an urgent, high-emotion tone. Emphasize life-changing opportunity and immediate action."
    ]
    
    style_prompt = styles_instructions[style_index] if 0 <= style_index < len(styles_instructions) else styles_instructions[0]

    prompt = (
        f"You are a viral YouTube Shorts creator. Write a highly engaging, viral YouTube Shorts script about: '{topic}'.\n\n"
        f"Style directive: {style_prompt}\n\n"
        "Requirements:\n"
        "1. Duration: Must be about 30 to 40 seconds when spoken (approx. 70-90 words).\n"
        "2. Structure: Start with a powerful 2-second hook that immediately grabs attention. End with an emotional or curiosity-inducing statement/question.\n"
        "3. Formatting: Output ONLY the script text itself. Do not include any stage directions, slide notes, speaker tags (e.g. do not include '[Host]', 'Voiceover:', or brackets). Just the clean spoken words.\n"
        "4. Style: Conversational, energetic, and punchy. Make every sentence count."
    )

    # Check if ollama command is available
    if not shutil.which("ollama"):
        print("Warning: Ollama is not installed or not in PATH. Using fallback script.", file=sys.stderr)
        return get_fallback_script(topic, style_index)

    try:
        # Run Ollama via subprocess
        print(f"Calling Ollama to generate script variation {style_index} for topic: '{topic}'...", flush=True)
        result = subprocess.run(
            ["ollama", "run", "llama3", prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=45  # Set a reasonable timeout
        )

        if result.returncode != 0:
            print(f"Warning: Ollama returned non-zero code {result.returncode}. Using fallback script.", file=sys.stderr)
            print(f"Ollama Error: {result.stderr}", file=sys.stderr)
            return get_fallback_script(topic, style_index)

        script = result.stdout.strip()
        if not script:
            print("Warning: Ollama returned empty script. Using fallback script.", file=sys.stderr)
            return get_fallback_script(topic, style_index)

        # Clean script of any brackets/notes that Ollama might have included
        cleaned_lines = []
        for line in script.split('\n'):
            line = line.strip()
            # Skip empty lines, lines starting with brackets (directions), or speaker labels
            if not line:
                continue
            if line.startswith('[') and line.endswith(']'):
                continue
            if line.startswith('(') and line.endswith(')'):
                continue
            if line.lower().startswith('voiceover:') or line.lower().startswith('narrator:') or line.lower().startswith('host:'):
                line = line.split(':', 1)[1].strip()
            # Remove asterisks that are often used for emphasis in markdown but sound weird in raw TTS
            line = line.replace('*', '')
            cleaned_lines.append(line)

        final_script = " ".join(cleaned_lines)
        print(f"Successfully generated script variation {style_index}: '{final_script[:60]}...'", flush=True)
        return final_script

    except subprocess.TimeoutExpired:
        print("Warning: Ollama script generation timed out. Using fallback script.", file=sys.stderr)
        return get_fallback_script(topic, style_index)
    except Exception as e:
        print(f"Warning: Ollama script generation failed with error: {str(e)}. Using fallback script.", file=sys.stderr)
        return get_fallback_script(topic, style_index)

if __name__ == "__main__":
    # Test script generation
    test_topic = "the future of artificial intelligence"
    script = generate_script(test_topic)
    print("\n--- Generated Script ---")
    print(script)
