import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

_sia = None

def _get_sia():
    global _sia
    if _sia is None:
        try:
            nltk.download('vader_lexicon', quiet=True)
            _sia = SentimentIntensityAnalyzer()
        except Exception:
            _sia = None
    return _sia

def analyze_sentiment(doc, pages_data=None, doc_category=None) -> dict:
    """
    Performs local sentence-level sentiment analysis using VADER lexicon.
    Returns percentages and key positive/negative sentences.
    """
    sia = _get_sia()
    sentences = list(doc.sents)

    if not sentences or sia is None:
        return {
            "overall": "Neutral",
            "positive_pct": 0.0,
            "neutral_pct": 100.0,
            "negative_pct": 0.0,
            "positive_sentences": [],
            "negative_sentences": [],
            "note": "Sentiment analysis unavailable or neutral."
        }

    pos_count = 0
    neu_count = 0
    neg_count = 0

    scored_sentences = []

    for sent in sentences:
        text = sent.text.strip()
        if len(text.split()) < 3:
            continue

        scores = sia.polarity_scores(text)
        compound = scores["compound"]

        # Map sentence to page number if pages_data is provided
        page_num = _find_page_number(text, pages_data)

        if compound >= 0.05:
            pos_count += 1
            sentiment_label = "positive"
        elif compound <= -0.05:
            neg_count += 1
            sentiment_label = "negative"
        else:
            neu_count += 1
            sentiment_label = "neutral"

        scored_sentences.append({
            "text": text,
            "score": compound,
            "label": sentiment_label,
            "page": page_num
        })

    total = pos_count + neu_count + neg_count or 1
    pos_pct = round((pos_count / total) * 100.0, 1)
    neu_pct = round((neu_count / total) * 100.0, 1)
    neg_pct = round((neg_count / total) * 100.0, 1)

    if pos_pct > neg_pct + 10:
        overall = "Positive"
    elif neg_pct > pos_pct + 10:
        overall = "Negative"
    else:
        overall = "Neutral"

    # Extract top positive & negative sentences
    pos_sents = sorted([s for s in scored_sentences if s["label"] == "positive"], key=lambda x: x["score"], reverse=True)[:3]
    neg_sents = sorted([s for s in scored_sentences if s["label"] == "negative"], key=lambda x: x["score"])[:3]

    note = ""
    if doc_category in ["Technical Document", "Research Paper", "Legal Document", "Security / Vulnerability Report", "Financial Document"]:
        note = f"Sentiment analysis may have limited relevance for objective {doc_category.lower()} content."

    return {
        "overall": overall,
        "positive_pct": pos_pct,
        "neutral_pct": neu_pct,
        "negative_pct": neg_pct,
        "positive_sentences": [{"sentence": s["text"], "page": s["page"]} for s in pos_sents],
        "negative_sentences": [{"sentence": s["text"], "page": s["page"]} for s in neg_sents],
        "note": note
    }

def _find_page_number(sentence_text: str, pages_data) -> int:
    if not pages_data:
        return None
    for p in pages_data:
        if p.get("text") and sentence_text[:30] in p["text"]:
            return p.get("page")
    return None
