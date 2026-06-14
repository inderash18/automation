import random

def generate_title(topic: str) -> str:
    """
    Generates a high-converting, attention-grabbing title for a YouTube Short.
    Ensures title casing of the topic for polished aesthetics.
    """
    # Clean and Title Case the topic
    topic_words = [word.capitalize() if word.lower() not in ['a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by', 'of', 'in', 'with', 'about'] else word.lower() for word in topic.strip().split()]
    if topic_words:
        # Capitalize the first word regardless of part of speech
        topic_words[0] = topic_words[0].capitalize()
    clean_topic = " ".join(topic_words)
    
    # Selection of high-performing hook title structures
    templates = [
        f"This Changes Everything About {clean_topic}...",
        f"The Hidden Secret Behind {clean_topic} 🤫",
        f"Nobody Talks About This {clean_topic} Trick!",
        f"Why You're Getting {clean_topic} Completely WRONG",
        f"I Tried {clean_topic} Using AI... Here's What Happened",
        f"This Insane {clean_topic} Hack Will Save You Hours!",
        f"You Are Missing This in {clean_topic} 🚨",
        f"The Truth About {clean_topic} (Shocking)",
        f"5 Secrets of {clean_topic} They Don't Want You To Know",
        f"Before You Try {clean_topic}, WATCH THIS!"
    ]
    
    return random.choice(templates)

if __name__ == "__main__":
    import sys
    # Reconfigure stdout to support unicode printing on Windows terminals
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
        
    # Test title generation
    test_topic = "coding with chatgpt"
    print("\n--- Generated Sample Titles ---")
    for _ in range(5):
        print(f"Title: {generate_title(test_topic)}")
