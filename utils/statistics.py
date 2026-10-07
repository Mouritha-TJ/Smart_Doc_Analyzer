import math

def calculate_statistics(original_text: str, doc, summary_text: str, selected_sentence_count: int):
    """
    Computes linguistic stats for the original text and compares it to the summary.
    
    Args:
        original_text: Original raw text string.
        doc: The processed spaCy Doc object.
        summary_text: Extracted summary text string.
        selected_sentence_count: Number of sentences in summary.
    Returns:
        Dict containing raw stats and comparison details.
    """
    # 1. Characters count
    char_count = len(original_text)
    
    # 2. Total words (count alphabetic tokens)
    words = [token.text for token in doc if token.is_alpha]
    word_count = len(words)
    
    # 3. Sentences count
    sentences = list(doc.sents)
    sentence_count = len(sentences)
    
    # 4. Unique words (vocabulary set)
    unique_words = {token.lemma_.lower() for token in doc if token.is_alpha}
    unique_word_count = len(unique_words)
    
    # 5. Average sentence length (words per sentence)
    avg_sentence_length = round(word_count / sentence_count, 1) if sentence_count > 0 else 0.0
    
    # 6. Vocabulary richness (Ratio of unique words to total words)
    vocab_richness = round(unique_word_count / word_count, 3) if word_count > 0 else 0.0
    
    # 7. Estimated reading time (based on average 200 words per minute)
    reading_time_mins = max(1, math.ceil(word_count / 200.0)) if word_count > 0 else 0
    
    # Summary stats
    summary_words_list = summary_text.split()
    summary_word_count = len(summary_words_list)
    
    # Compression ratio: how much text was shaved off (e.g. 80% means only 20% remains)
    if word_count > 0:
        compression_percentage = round((1 - (summary_word_count / word_count)) * 100, 1)
        # Handle cases where summary word count might be slightly larger due to formatting (rare)
        compression_percentage = max(0.0, min(100.0, compression_percentage))
    else:
        compression_percentage = 0.0
        
    return {
        "characters": char_count,
        "words": word_count,
        "sentences": sentence_count,
        "unique_words": unique_word_count,
        "avg_sentence_length": avg_sentence_length,
        "vocabulary_richness": vocab_richness,
        "reading_time": reading_time_mins,
        "summary_words": summary_word_count,
        "summary_sentences": selected_sentence_count,
        "compression_percentage": compression_percentage
    }
