import spacy
import spacy.cli
import re

_nlp = None

def get_nlp():
    """
    Gets or downloads/loads the spaCy en_core_web_sm model.
    """
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy model 'en_core_web_sm' not found. Downloading...")
            try:
                spacy.cli.download("en_core_web_sm")
                _nlp = spacy.load("en_core_web_sm")
            except Exception as e:
                # Fallback if download fails or is offline
                raise RuntimeError(f"Failed to load or download spaCy model 'en_core_web_sm': {str(e)}")
    return _nlp

def preprocess_text(text: str):
    """
    Cleans and processes the text using spaCy.
    Returns:
        doc: The spaCy Doc object (for sentence tokenization, POS tagging, NER).
        cleaned_tokens: A list of lemmatized, lowercase tokens with stopwords/punctuation removed.
    """
    nlp = get_nlp()
    
    # Simple clean: replace multiple whitespaces with single space
    cleaned_spacing = re.sub(r'\s+', ' ', text).strip()
    
    # Process with spaCy
    doc = nlp(cleaned_spacing)
    
    cleaned_tokens = []
    for token in doc:
        # Keep alphabetic tokens, skip stopwords, punctuation, space, and numbers
        if (
            token.is_alpha 
            and not token.is_stop 
            and not token.is_punct 
            and not token.is_space
            and len(token.text.strip()) > 1
        ):
            cleaned_tokens.append(token.lemma_.lower())
            
    return doc, cleaned_tokens
