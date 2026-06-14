import random

# Curated list of high-retention viral topics for YouTube Shorts niches
TRENDS = [
    # AI & Future Tech Niche
    "AI tools that feel illegal to know",
    "how AI is changing software development",
    "Elon Musk shocking warning about superintelligence",
    "hidden ChatGPT hacks you aren't using",
    "the future of human programmers in an AI world",
    "insane web automation tools you need to try",
    
    # Personal Finance & Side Hustles Niche
    "side hustles you can start with zero dollars",
    "how to build passive income with AI bots",
    "the lazy way to make money online",
    "why saving money is keeping you poor",
    "secrets of self-made digital entrepreneurs",
    
    # Self-Improvement & Habit Niche
    "micro habits that will double your focus",
    "the dark truth about daily productivity hacks",
    "how to build bulletproof discipline in 30 days",
    "why you are constantly tired and how to fix it",
    "essential sleep rules of high performers"
]

def get_trending_topic() -> str:
    """Returns a random trending YouTube Shorts topic."""
    return random.choice(TRENDS)

if __name__ == "__main__":
    print("\n--- Trending Topics ---")
    for i in range(3):
        print(f"[{i+1}] {get_trending_topic()}")
