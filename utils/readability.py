import re

def count_syllables_in_word(word: str) -> int:
    """
    Local heuristic syllable counter.
    """
    word = word.lower().strip()
    if len(word) <= 3:
        return 1
    word = re.sub(r'(?:[^laeiouy]|ed|es|e)$', '', word)
    word = re.sub(r'^y', '', word)
    syllables = len(re.findall(r'[aeiouy]{1,2}', word))
    return max(1, syllables)

def analyze_readability(original_text: str, doc) -> dict:
    """
    Calculates Flesch Reading Ease, Flesch-Kincaid Grade Level,
    vocabulary richness, and lexical complexity metrics.
    """
    words = [token.text for token in doc if token.is_alpha]
    word_count = len(words)
    sentences = list(doc.sents)
    sentence_count = len(sentences) or 1

    if word_count == 0:
        return {
            "flesch_reading_ease": 0,
            "grade_level": "N/A",
            "vocabulary_richness": 0.0,
            "lexical_diversity": 0.0,
            "sentence_complexity": "Low",
            "quality_rating": "N/A",
            "explanation": "Insufficient text for readability calculation."
        }

    total_syllables = sum(count_syllables_in_word(w) for w in words)
    
    asl = word_count / sentence_count  # Average Sentence Length
    asw = total_syllables / word_count # Average Syllables per Word

    # Flesch Reading Ease score (out of 100 integer, no decimals)
    flesch_score = 206.835 - (1.015 * asl) - (84.6 * asw)
    flesch_score = int(round(max(0.0, min(100.0, flesch_score))))

    # Flesch-Kincaid Grade Level
    fk_grade = (0.39 * asl) + (11.8 * asw) - 15.59
    fk_grade = round(max(0.0, fk_grade), 1)

    # Grade Level Description
    if flesch_score >= 80:
        grade_desc = "Easy (Middle School)"
        quality_rating = "Very Accessible"
    elif flesch_score >= 60:
        grade_desc = "Standard (High School)"
        quality_rating = "Good / Clear"
    elif flesch_score >= 40:
        grade_desc = "Fairly Difficult (College)"
        quality_rating = "Technical / Complex"
    else:
        grade_desc = "Very Difficult (Academic/Graduate)"
        quality_rating = "Dense / Advanced"

    # Lexical Diversity & Stopword ratio
    unique_words = {w.lower() for w in words}
    unique_count = len(unique_words)
    lexical_diversity = round(unique_count / word_count, 3)

    stopwords = [t for t in doc if t.is_stop and t.is_alpha]
    stopword_ratio = round(len(stopwords) / word_count, 3)

    sentence_complexity = "High" if asl > 22 else ("Moderate" if asl > 14 else "Low")

    explanation = (
        f"Calculated using Flesch Reading Ease formula ({flesch_score}/100) based on "
        f"an average of {round(asl, 1)} words per sentence and {round(asw, 2)} syllables per word."
    )

    return {
        "flesch_reading_ease": flesch_score,
        "grade_level": grade_desc,
        "fk_grade_num": fk_grade,
        "vocabulary_richness": lexical_diversity,
        "stopword_ratio": stopword_ratio,
        "sentence_complexity": sentence_complexity,
        "quality_rating": quality_rating,
        "explanation": explanation
    }
