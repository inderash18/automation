import re

def score_script(script: str) -> int:
    """
    Evaluates a script based on standard YouTube Shorts viral metrics.
    Returns a normalized score between 0 and 100.
    """
    if not script or not script.strip():
        return 0

    score = 0
    script_lower = script.lower()
    words = script.split()
    word_count = len(words)

    # 1. Hook Strength (Highly critical: check first 15 words)
    hook_keywords = [
        "stop", "you", "secret", "never", "nobody", "trick", "illegal", 
        "expose", "hack", "future", "mind-blowing", "insane", "shocking",
        "why", "how", "don't"
    ]
    first_words = " ".join(words[:15]).lower() if word_count >= 15 else script_lower
    for hook in hook_keywords:
        if hook in first_words:
            score += 3  # Add points for starting with high-retention hooks

    # 2. Emotional Triggers & Pique Words (found anywhere in text)
    emotional_triggers = [
        "mistake", "regret", "guarantee", "proven", "hidden", "warning",
        "danger", "fail", "success", "magic", "scared", "lie", "truth"
    ]
    for word in emotional_triggers:
        if word in script_lower:
            score += 2

    # 3. Direct Reader Address (Engagement)
    personal_pronouns = ["you", "your", "yours", "yourself"]
    pronoun_count = sum(script_lower.count(p) for p in personal_pronouns)
    if pronoun_count > 0:
        score += min(6, pronoun_count * 2)  # Up to 6 points for active pronouns

    # 4. Curiosity gaps & punctuation
    if "?" in script:
        score += 4
    if "!" in script:
        score += 2

    # 5. Brevity / Retention Pace (Ideal density for a 30s Short is 70 to 90 words)
    if 65 <= word_count <= 95:
        score += 6
    elif 50 <= word_count < 65 or 95 < word_count <= 110:
        score += 3
    else:
        score += 0  # Too short or too wordy (hard to fit in 30 seconds)

    # Normalize score to be out of 100 (assuming max raw score is around 25-30)
    # A raw score of 20 or higher is considered a solid viral script
    normalized_score = min(100, int((score / 22) * 100))
    # Make sure we don't return 0 for a valid script
    return max(15, normalized_score)

def choose_best(scripts: list) -> tuple:
    """
    Ranks a list of script candidates.
    Returns a tuple of (best_script, best_score, scored_candidates_list).
    """
    scored = []
    for s in scripts:
        score = score_script(s)
        scored.append((s, score))
        
    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)
    best_script, best_score = scored[0]
    return best_script, best_score, scored

if __name__ == "__main__":
    # Test script grading
    candidates = [
        "Just some normal facts about programming. You write code, test it, and then fix the bugs. It takes a lot of time.",
        "STOP scrolling! If you are writing code without AI, you are making a massive mistake. The secret is that developers using AI tools are already 10 times faster than you. Are you going to adapt, or get left behind? Let me know in the comments!",
        "What if I told you that AI is going to replace your job tomorrow? It sounds scary, but it is actually the truth. You must adapt and learn the tools before it is too late. Subscribe right now to stay ahead!"
    ]
    
    best, score, all_scored = choose_best(candidates)
    print("\n--- Scored Candidate Scripts ---")
    for i, (scr, sc) in enumerate(all_scored):
        print(f"[{i+1}] Score: {sc}% | text: '{scr[:60]}...'")
    print(f"\nBest Script Chosen (Score: {score}%):")
    print(best)
