from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import re

def extract_keywords(doc, top_n=None):
    """
    Extracts keyphrases (unigrams, bigrams, trigrams) and keywords using POS filtering
    (preferring Nouns, Proper Nouns, and Adjectives) and a local sentence-level TF-IDF algorithm.
    Returns list of dicts: [{"phrase": str, "frequency": int, "score": float}]
    """
    total_words = len([token for token in doc if token.is_alpha])
    
    if top_n is None:
        if total_words < 200:
            top_n = 6
        elif total_words <= 1000:
            top_n = 10
        else:
            top_n = 15

    sentences = list(doc.sents)
    
    # Extract noun chunks and clean phrases
    noun_phrases = []
    for chunk in doc.noun_chunks:
        clean_tokens = [
            t.text.strip() for t in chunk
            if not t.is_stop and not t.is_punct and t.is_alpha and len(t.text) > 1
        ]
        if clean_tokens and len(clean_tokens) <= 4:
            phrase = " ".join(clean_tokens).title()
            if len(phrase) > 2:
                noun_phrases.append(phrase)

    phrase_counts = Counter(noun_phrases)

    # Collect sentence texts with POS filtering
    sentence_docs = []
    for sentence in sentences:
        filtered_tokens = []
        for token in sentence:
            if (
                token.pos_ in ("NOUN", "PROPN", "ADJ")
                and not token.is_stop
                and token.is_alpha
                and len(token.text.strip()) > 1
            ):
                filtered_tokens.append(token.text.lower())
        if filtered_tokens:
            sentence_docs.append(" ".join(filtered_tokens))

    if not sentence_docs:
        # Fallback to phrase counts
        results = []
        for phrase, count in phrase_counts.most_common(top_n):
            results.append({"phrase": phrase, "frequency": count, "score": float(count)})
        if not results:
            words = [t.text.title() for t in doc if t.is_alpha and not t.is_stop and len(t.text) > 1]
            for word, count in Counter(words).most_common(top_n):
                results.append({"phrase": word, "frequency": count, "score": float(count)})
        return _format_keyword_output(results, top_n)

    try:
        # TF-IDF with n-grams (1-3)
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            token_pattern=r'(?u)\b\w+\b',
            lowercase=True,
            stop_words='english'
        )
        tfidf_matrix = vectorizer.fit_transform(sentence_docs)
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.sum(axis=0).A1

        scored_candidates = []
        for term, score in zip(feature_names, scores):
            term_title = term.title()
            freq = phrase_counts.get(term_title, 1)
            # Give slight boost to multi-word phrases
            words = term.split()
            boost = 1.2 if len(words) > 1 else 1.0
            scored_candidates.append({
                "phrase": term_title,
                "frequency": freq,
                "score": round(float(score * boost), 3)
            })

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)

        # De-duplicate sub-phrases (e.g. if "Machine Learning" is present, rank it high)
        unique_results = []
        seen_phrases = set()
        for cand in scored_candidates:
            p = cand["phrase"]
            p_lower = p.lower()
            if p_lower not in seen_phrases:
                seen_phrases.add(p_lower)
                unique_results.append(cand)
            if len(unique_results) >= top_n:
                break

        return _format_keyword_output(unique_results, top_n)

    except Exception:
        results = []
        for phrase, count in phrase_counts.most_common(top_n):
            results.append({"phrase": phrase, "frequency": count, "score": float(count)})
        return _format_keyword_output(results, top_n)

def _format_keyword_output(raw_results, top_n):
    # Ensure legacy compatibility: string list or dict list
    # Return formatted dict items
    return raw_results[:top_n]
