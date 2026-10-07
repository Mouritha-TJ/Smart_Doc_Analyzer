from collections import Counter

def extract_themes(doc, num_themes=5):
    """
    Extracts 3–5 major key themes from a spaCy Doc.
    Uses noun chunk extraction, cleans the noun phrases, counts their frequencies,
    and returns the top unique non-overlapping concepts, capitalized.
    """
    noun_chunks = list(doc.noun_chunks)
    cleaned_chunks = []
    
    for chunk in noun_chunks:
        # Extract individual tokens, filtering stopwords, punctuation, numbers
        clean_tokens = [
            token.text.strip().lower() 
            for token in chunk 
            if not token.is_stop and not token.is_punct and token.is_alpha
        ]
        
        # We prefer multi-word noun phrases (e.g. 2-3 words) to represent concepts,
        # but single words can also be candidate concepts.
        if clean_tokens and len(clean_tokens) <= 4:
            phrase = " ".join(clean_tokens)
            # Filter out very short phrases
            if len(phrase) > 3:
                cleaned_chunks.append(phrase)

    # Count frequencies of the cleaned phrases
    phrase_counts = Counter(cleaned_chunks)
    
    # Take the top 30 candidates to filter and de-duplicate
    candidates = [phrase for phrase, count in phrase_counts.most_common(30)]
    
    themes = []
    for candidate in candidates:
        # Avoid redundancy (e.g. if "data science" is selected, skip "science")
        # Ensure the candidate is not a substring of, or does not contain, an already selected theme
        is_redundant = False
        for theme in themes:
            theme_lower = theme.lower()
            if candidate in theme_lower or theme_lower in candidate:
                is_redundant = True
                break
        
        if not is_redundant:
            themes.append(candidate.title())
            if len(themes) >= num_themes:
                break

    # If we didn't extract enough themes, fill with most common nouns/proper nouns
    if len(themes) < 3:
        nouns = []
        for token in doc:
            if (
                token.pos_ in ("NOUN", "PROPN") 
                and not token.is_stop 
                and token.is_alpha 
                and len(token.text.strip()) > 2
            ):
                nouns.append(token.lemma_.title())
                
        noun_counts = Counter(nouns)
        for noun, count in noun_counts.most_common(10):
            if noun not in themes:
                themes.append(noun)
            if len(themes) >= num_themes:
                break

    # If the list is still completely empty, fallback
    if not themes:
        themes = ["General Overview"]

    # Slice to return 3 to 5 themes
    return themes[:max(3, min(num_themes, len(themes)))]
