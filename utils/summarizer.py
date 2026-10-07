"""
Extractive Summarizer using local NLP techniques:
 - Sentence tokenization (spaCy)
 - Stop-word removal
 - Lemmatization
 - Normalized word-frequency scoring
 - Sentence position weighting
 - Named-entity density bonus
 - Cosine-similarity-based redundancy removal (no repeating ideas)

No external API. 100% local.
"""

from collections import Counter
import math


def _cosine_sim(vec_a: dict, vec_b: dict) -> float:
    """Compute cosine similarity between two term-frequency dicts."""
    if not vec_a or not vec_b:
        return 0.0
    keys = set(vec_a) | set(vec_b)
    dot = sum(vec_a.get(k, 0) * vec_b.get(k, 0) for k in keys)
    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _sent_vector(sentence, word_weights: dict) -> dict:
    """Build a weighted term vector for a sentence."""
    vec = {}
    for token in sentence:
        if token.is_alpha and not token.is_stop and not token.is_punct:
            lemma = token.lemma_.lower()
            vec[lemma] = vec.get(lemma, 0) + word_weights.get(lemma, 0.01)
    return vec


def summarize_text(doc, length_option="medium"):
    """
    Extractive summarizer.

    Summary levels:
        very_short  → 1-2 sentences
        short       → ~10-12% of sentences (min 3)
        medium      → ~20-22% of sentences (min 5)
        detailed    → ~32-35% of sentences (min 8, max 25)

    Returns:
        summary_text (str): The extractive summary.
        selected_count (int): Number of sentences selected.
    """
    sentences = list(doc.sents)
    total = len(sentences)

    if total == 0:
        return "", 0
    if total <= 2:
        return doc.text.strip(), total

    # ── Determine target sentence count ──────────────────────────────────────
    opt = length_option.lower().strip().replace("-", "_").replace(" ", "_") \
        if isinstance(length_option, str) else "medium"

    if opt in ("very_short", "veryshort", "brief"):
        target = max(1, min(2, total))
    elif opt == "short":
        target = max(3, min(math.ceil(total * 0.12), 6))
    elif opt in ("detailed", "long", "comprehensive"):
        # Caps at 25 sentences regardless of document length
        target = max(8, min(math.ceil(total * 0.33), 25))
    else:  # medium
        target = max(5, min(math.ceil(total * 0.22), 12))

    target = min(target, total)

    # ── Step 1: Word frequency (lemmatised, no stop-words) ───────────────────
    freq = Counter()
    for token in doc:
        if token.is_alpha and not token.is_stop and not token.is_punct and not token.is_space:
            freq[token.lemma_.lower()] += 1

    if not freq:
        # No content words — fall back to first `target` sentences
        sents = [s.text.strip() for s in sentences[:target]]
        return " ".join(sents), len(sents)

    max_freq = max(freq.values())
    weights = {w: c / max_freq for w, c in freq.items()}

    # ── Step 2: Score each sentence ─────────────────────────────────────────
    scored = []
    for idx, sent in enumerate(sentences):
        content = [t for t in sent
                   if t.is_alpha and not t.is_stop and not t.is_punct]
        if not content:
            scored.append((idx, sent, 0.0))
            continue

        # Average word weight
        base = sum(weights.get(t.lemma_.lower(), 0) for t in content) / len(content)

        # Position bonus: first 15% of sentences get +0.15 (usually topic sentences)
        pos_ratio = idx / total
        pos_bonus = 0.15 if pos_ratio <= 0.15 else (0.05 if pos_ratio <= 0.30 else 0.0)

        # Named-entity density bonus
        ent_bonus = min(0.1 * len(sent.ents), 0.2)

        # Length normalisation penalty (very short / very long sentences are less useful)
        word_count = len(content)
        if word_count < 4:
            len_penalty = -0.1
        elif word_count > 60:
            len_penalty = -0.05
        else:
            len_penalty = 0.0

        scored.append((idx, sent, base + pos_bonus + ent_bonus + len_penalty))

    # ── Step 3: Select top sentences with redundancy removal ─────────────────
    ranked = sorted(scored, key=lambda x: x[2], reverse=True)

    selected = []       # (original_idx, sentence_span)
    selected_vecs = []  # term vectors for redundancy check
    SIM_THRESHOLD = 0.72   # sentences more similar than this are skipped

    for idx, sent, score in ranked:
        if len(selected) >= target:
            break

        sent_text = " ".join(sent.text.strip().split())
        if not sent_text:
            continue

        # Build term vector
        vec = _sent_vector(sent, weights)

        # Check redundancy against already-selected sentences
        is_redundant = any(_cosine_sim(vec, sv) >= SIM_THRESHOLD for sv in selected_vecs)
        if is_redundant:
            continue

        selected.append((idx, sent_text))
        selected_vecs.append(vec)

    # ── Step 4: Re-order by original document position ───────────────────────
    selected.sort(key=lambda x: x[0])

    summary_sentences = [text for _, text in selected]
    summary_text = " ".join(summary_sentences)
    return summary_text, len(summary_sentences)
