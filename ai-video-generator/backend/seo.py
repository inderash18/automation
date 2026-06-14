def generate_hashtags(topic: str) -> list:
    """
    Generates up to 8 high-relevance hashtags for a given topic.
    Cleans punctuation and generates context-based tags dynamically.
    """
    base = ["#shorts", "#viral", "#trending", "#fyp"]
    
    # Clean topic: remove non-alphanumeric chars (keep spaces)
    cleaned_topic = "".join(c for c in topic if c.isalnum() or c.isspace()).strip().lower()
    if not cleaned_topic:
        return base
        
    dynamic = []
    
    # 1. Entire topic concatenated
    topic_collapsed = cleaned_topic.replace(" ", "")
    if topic_collapsed:
        dynamic.append(f"#{topic_collapsed}")
        
    # 2. Individual words of topic (up to 3 words, filtering out short stop words)
    words = cleaned_topic.split()
    for w in words[:3]:
        if len(w) > 2:
            dynamic.append(f"#{w}")
            
    # 3. Niche keyword injections
    # Tech/AI niche
    if any(k in cleaned_topic for k in ["ai", "chatgpt", "llama", "tech", "future", "gpt", "bot", "intelligence"]):
        dynamic.extend(["#ai", "#technology", "#automation", "#chatgpt"])
    # Development niche
    if any(k in cleaned_topic for k in ["code", "developer", "program", "python", "javascript", "engineer"]):
        dynamic.extend(["#coding", "#programming", "#developer", "#software"])
    # Wealth/Business niche
    if any(k in cleaned_topic for k in ["money", "earn", "hustle", "finance", "rich", "job", "career"]):
        dynamic.extend(["#sidehustle", "#makemoney", "#finance", "#success"])
    # Motivation/Self-improvement niche
    if any(k in cleaned_topic for k in ["life", "mindset", "success", "motivate", "habit", "focus", "discipline"]):
        dynamic.extend(["#motivation", "#mindset", "#discipline", "#inspiration"])

    # Combine lists while maintaining order and filtering duplicates
    combined = base + dynamic
    seen = set()
    final_tags = []
    for tag in combined:
        if tag not in seen:
            seen.add(tag)
            final_tags.append(tag)
            
    return final_tags[:8] # Return top 8 most relevant hashtags

if __name__ == "__main__":
    # Test SEO tagging
    test_topics = ["make money with ai tools", "best coding habits for beginners"]
    print("\n--- Generated Sample Hashtags ---")
    for t in test_topics:
        print(f"Topic: '{t}' -> Tags: {' '.join(generate_hashtags(t))}")
