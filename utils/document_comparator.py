from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def compare_documents(doc_a_data: dict, doc_b_data: dict) -> dict:
    """
    Compares Document A and Document B using local TF-IDF cosine similarity
    and set operations for keywords, themes, and entities.
    """
    text_a = doc_a_data.get("original_text", "")
    text_b = doc_b_data.get("original_text", "")

    # Calculate overall similarity score using TF-IDF
    if text_a and text_b:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
        cos_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        similarity_pct = round(float(cos_sim) * 100.0, 1)
    else:
        similarity_pct = 0.0

    # Keywords Comparison
    kw_a = _extract_phrase_set(doc_a_data.get("keywords", []))
    kw_b = _extract_phrase_set(doc_b_data.get("keywords", []))

    common_kw = list(kw_a.intersection(kw_b))
    unique_a_kw = list(kw_a - kw_b)
    unique_b_kw = list(kw_b - kw_a)

    # Themes Comparison
    themes_a = set(doc_a_data.get("themes", []))
    themes_b = set(doc_b_data.get("themes", []))

    common_themes = list(themes_a.intersection(themes_b))
    unique_a_themes = list(themes_a - themes_b)
    unique_b_themes = list(themes_b - themes_a)

    # Entities Comparison
    ents_a = _extract_entity_set(doc_a_data.get("entities", {}))
    ents_b = _extract_entity_set(doc_b_data.get("entities", {}))

    common_ents = list(ents_a.intersection(ents_b))
    unique_a_ents = list(ents_a - ents_b)
    unique_b_ents = list(ents_b - ents_a)

    return {
        "similarity_percentage": similarity_pct,
        "doc_a_name": doc_a_data.get("document_name", "Document A"),
        "doc_b_name": doc_b_data.get("document_name", "Document B"),
        "doc_a_word_count": doc_a_data.get("original_word_count", 0),
        "doc_b_word_count": doc_b_data.get("original_word_count", 0),
        "doc_a_category": doc_a_data.get("classification", {}).get("category", "General"),
        "doc_b_category": doc_b_data.get("classification", {}).get("category", "General"),
        "keywords": {
            "common": common_kw[:10],
            "unique_a": unique_a_kw[:10],
            "unique_b": unique_b_kw[:10]
        },
        "themes": {
            "common": common_themes,
            "unique_a": unique_a_themes,
            "unique_b": unique_b_themes
        },
        "entities": {
            "common": common_ents[:10],
            "unique_a": unique_a_ents[:10],
            "unique_b": unique_b_ents[:10]
        },
        "sentiment": {
            "doc_a": doc_a_data.get("sentiment", {}).get("overall", "Neutral"),
            "doc_b": doc_b_data.get("sentiment", {}).get("overall", "Neutral")
        },
        "readability": {
            "doc_a_ease": doc_a_data.get("readability", {}).get("flesch_reading_ease", 0),
            "doc_b_ease": doc_b_data.get("readability", {}).get("flesch_reading_ease", 0)
        }
    }

def _extract_phrase_set(keywords_input) -> set:
    if isinstance(keywords_input, list):
        if keywords_input and isinstance(keywords_input[0], dict):
            return {item["phrase"].title() for item in keywords_input if "phrase" in item}
        elif keywords_input and isinstance(keywords_input[0], str):
            return {item.title() for item in keywords_input}
    return set()

def _extract_entity_set(entities_input) -> set:
    if isinstance(entities_input, dict) and "flat" in entities_input:
        return {item["name"] for item in entities_input["flat"] if "name" in item}
    return set()
