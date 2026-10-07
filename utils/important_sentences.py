from collections import Counter

LOCAL_GLOSSARY = {
    "utilizes": "uses",
    "utilize": "use",
    "architecture": "system design",
    "methodology": "method / approach",
    "vulnerability": "security weakness",
    "vulnerabilities": "security weaknesses",
    "implementation": "practical setup",
    "algorithm": "step-by-step rules",
    "mitigation": "fix / solution",
    "stakeholders": "key people involved",
    "facilitate": "help / enable",
    "subsequent": "following",
    "prior": "before",
    "commence": "begin",
    "terminate": "stop",
    "demonstrates": "shows",
    "expedite": "speed up"
}

def extract_important_sentences(doc, pages_data=None, top_n=5) -> list:
    """
    Ranks sentences by word frequency weight, entity density, and position bonus.
    Returns list of dicts: [{"sentence": str, "score": float, "page": int}]
    """
    sentences = list(doc.sents)
    if not sentences:
        return []

    # Calculate word frequencies of meaningful words
    word_freqs = Counter()
    for token in doc:
        if token.is_alpha and not token.is_stop and not token.is_punct:
            word_freqs[token.lemma_.lower()] += 1

    max_freq = max(word_freqs.values()) if word_freqs else 1
    word_weights = {w: count / max_freq for w, count in word_freqs.items()}

    scored_sentences = []
    total_sents = len(sentences)

    for idx, sent in enumerate(sentences):
        text = sent.text.strip()
        words = [t.lemma_.lower() for t in sent if t.is_alpha and not t.is_stop]
        if not words or len(text.split()) < 4:
            continue

        # Word frequency score
        base_score = sum(word_weights.get(w, 0.0) for w in words) / len(words)

        # Entity density bonus
        ent_bonus = 0.2 if len(sent.ents) > 0 else 0.0

        # Position bonus (first 20% of document sentences get a boost)
        pos_bonus = 0.15 if (idx / total_sents) <= 0.2 else 0.0

        total_score = round(base_score + ent_bonus + pos_bonus, 2)
        page_num = _find_page_number(text, pages_data)

        scored_sentences.append({
            "sentence": text,
            "score": min(1.0, total_score),
            "page": page_num,
            "index": idx
        })

    # Sort by score descending
    scored_sentences.sort(key=lambda x: x["score"], reverse=True)

    # Return top N, formatted
    return [
        {
            "sentence": s["sentence"],
            "score": round(s["score"], 2),
            "page": s["page"]
        }
        for s in scored_sentences[:top_n]
    ]

def explain_simply(doc, pages_data=None) -> dict:
    """
    Produces a simple, jargon-reduced explanation based on top important document sentences.
    """
    important = extract_important_sentences(doc, pages_data=pages_data, top_n=3)
    if not important:
        return {
            "explanation": "No sufficient text content to generate a simplified overview.",
            "glossary_used": [],
            "source": "N/A"
        }

    raw_sentences = [item["sentence"] for item in important]

    # Replace complex jargon using local glossary
    simplified_sents = []
    used_glossary = []

    for sent_text in raw_sentences:
        modified_text = sent_text
        for complex_term, simple_term in LOCAL_GLOSSARY.items():
            if complex_term in modified_text.lower():
                modified_text = modified_text.replace(complex_term, simple_term)
                modified_text = modified_text.replace(complex_term.capitalize(), simple_term.capitalize())
                if f"{complex_term} → {simple_term}" not in used_glossary:
                    used_glossary.append(f"{complex_term} → {simple_term}")
        simplified_sents.append(modified_text)

    simple_paragraph = " ".join(simplified_sents)

    return {
        "explanation": simple_paragraph,
        "glossary_used": used_glossary,
        "source": "Simple explanation constructed locally from key document sentences."
    }

def _find_page_number(sentence_text: str, pages_data) -> int:
    if not pages_data:
        return None
    for p in pages_data:
        if p.get("text") and sentence_text[:30] in p["text"]:
            return p.get("page")
    return None
