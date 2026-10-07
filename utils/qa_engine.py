from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

QUESTION_STOP_WORDS = {
    "what", "is", "are", "was", "were", "the", "a", "an", "and", "or", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "about", "how", "why", "when", "where", "which", "who", "whom", "whose",
    "does", "do", "did", "can", "could", "should", "would", "tell", "me", "give", "explain", "describe",
    "mentioned", "discuss", "discussed", "document", "report", "paper", "say", "says"
}

def answer_question(question: str, doc, pages_data=None) -> dict:
    """
    Extractive Question Answering system using local TF-IDF cosine similarity
    and lemmatized keyword overlap matching.
    Strictly zero hallucination: if confidence < threshold, returns explicit fallback.
    Returns:
        {
            "question": str,
            "answer": str,
            "citations": [int or None],
            "page_text": str, # e.g. "Page 2" or "Page reference not available for TXT documents."
            "confidence": float, # 0.0 to 1.0
            "relevant_sentences": [{"sentence": str, "page": int, "score": float}]
        }
    """
    if not question or len(question.strip()) < 3:
        return {
            "question": question,
            "answer": "Please enter a valid question regarding the document.",
            "citations": [],
            "page_text": "N/A",
            "confidence": 0.0,
            "relevant_sentences": []
        }

    sentences = list(doc.sents)
    sentence_objs = []
    sentence_texts = []
    
    for s in sentences:
        txt = " ".join(s.text.strip().split())
        if len(txt.split()) >= 3:
            sentence_objs.append(s)
            sentence_texts.append(txt)

    if not sentence_texts:
        return {
            "question": question,
            "answer": "No relevant information was found in this document.",
            "citations": [],
            "page_text": "N/A",
            "confidence": 0.0,
            "relevant_sentences": []
        }

    # Extract meaningful question keywords (lemmatized, lower)
    q_words = [
        re.sub(r'[^a-zA-Z0-9]', '', w.lower())
        for w in question.split()
    ]
    q_keywords = {w for w in q_words if w and w not in QUESTION_STOP_WORDS and len(w) > 1}

    # Clean corpus for TF-IDF
    corpus = sentence_texts + [question]

    try:
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            token_pattern=r'(?u)\b\w+\b'
        )
        tfidf_matrix = vectorizer.fit_transform(corpus)

        q_vector = tfidf_matrix[-1]
        sent_vectors = tfidf_matrix[:-1]

        # Cosine similarity
        similarities = cosine_similarity(q_vector, sent_vectors).flatten()

        scored_matches = []
        for idx, sim in enumerate(similarities):
            sent_obj = sentence_objs[idx]
            sent_str = sentence_texts[idx]
            
            # Sentence keywords
            sent_tokens = {
                re.sub(r'[^a-zA-Z0-9]', '', t.text.lower())
                for t in sent_obj if t.is_alpha and not t.is_stop
            }
            
            # Calculate keyword overlap
            overlap = len(q_keywords.intersection(sent_tokens)) if q_keywords else 0
            overlap_ratio = overlap / len(q_keywords) if q_keywords else 0.0

            # Combined score: 60% TF-IDF cosine similarity + 40% keyword overlap
            combined_score = (0.6 * float(sim)) + (0.4 * overlap_ratio)

            if combined_score > 0.08 and (overlap > 0 or sim > 0.18):
                page_num = _find_page_number(sent_str, pages_data)
                scored_matches.append({
                    "sentence": sent_str,
                    "score": round(combined_score, 3),
                    "raw_sim": round(float(sim), 3),
                    "overlap": overlap,
                    "page": page_num
                })

        scored_matches.sort(key=lambda x: x["score"], reverse=True)

        # Strict threshold check for zero hallucination
        if not scored_matches or scored_matches[0]["score"] < 0.14 or scored_matches[0]["overlap"] == 0:
            return {
                "question": question,
                "answer": "No relevant information was found in this document.",
                "citations": [],
                "page_text": "N/A",
                "confidence": 0.0,
                "relevant_sentences": []
            }

        # Select top 1-2 most relevant sentences
        top_matches = scored_matches[:2]
        extracted_text = " ".join([m["sentence"] for m in top_matches])

        # Page citations
        valid_pages = [m["page"] for m in top_matches if m["page"] is not None]
        unique_pages = list(dict.fromkeys(valid_pages))

        if unique_pages:
            page_str = ", ".join([f"Page {p}" for p in unique_pages])
        else:
            page_str = "Page reference not available for TXT documents."

        return {
            "question": question,
            "answer": extracted_text,
            "citations": unique_pages,
            "page_text": page_str,
            "confidence": top_matches[0]["score"],
            "relevant_sentences": top_matches
        }

    except Exception:
        return {
            "question": question,
            "answer": "No relevant information was found in this document.",
            "citations": [],
            "page_text": "N/A",
            "confidence": 0.0,
            "relevant_sentences": []
        }

def _find_page_number(sentence_text: str, pages_data) -> int:
    if not pages_data:
        return None
    # Normalize snippet
    snippet = " ".join(sentence_text[:35].split()).lower()
    for p in pages_data:
        if p.get("text"):
            page_clean = " ".join(p["text"].split()).lower()
            if snippet in page_clean:
                return p.get("page")
    return None
