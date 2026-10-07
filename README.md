# SmartDoc NLP — Intelligent Local Document Analysis System

> **Pure Local NLP System:** This project operates 100% locally and **does NOT require any external AI API key** (no OpenAI, Gemini, Claude, Groq, or cloud inference). All processing runs using local Python libraries, spaCy, NLTK, scikit-learn, PyPDF2, python-docx, ReportLab, and SQLite.

---

## 1. Project Overview
**SmartDoc NLP** is a comprehensive, local NLP document analysis platform designed to process PDF, DOCX, TXT documents, or pasted text. It automatically generates:
- Executive Extractive Summaries
- Document Classification with reasoning & confidence metrics
- Local Extractive Document Q&A with exact `[Page X]` source citations
- Context-aware Security & Vulnerability Level Detection (LOW, MEDIUM, HIGH, CRITICAL)
- Sentiment Analysis & Readability/Quality Scores
- Multi-word Keyphrase & Theme Extraction
- Named Entity Recognition (NER)
- Side-by-side Dual Document Comparison Matrix
- Downloadable PDF (`ReportLab`) and DOCX (`python-docx`) Reports
- User Authentication & Multi-Tenant Document History

---

## 2. Features

### Core NLP Capabilities
- **Flexible Inputs:** Support for PDF, DOCX, TXT uploads, and text paste.
- **Page-Level Mapping:** Preserves page boundaries (`page_number`, `page_text`) across PDF and DOCX files.
- **Extractive Document Q&A:** Answers user questions using local TF-IDF/cosine similarity sentence matching with strict zero-hallucination thresholding. If no match is found, returns: *"No sufficiently relevant information was found in this document."*
- **Vulnerability & Risk Level Indicator:** Scans security language and evaluates threat levels. Uses **negation detection** (e.g., *"no known vulnerabilities"* or *"free of security flaws"* is correctly identified as LOW risk rather than falsely flagged).
- **Document Classification:** Profiles documents into categories (*Research Paper, Technical Document, Business Report, Legal Document, Financial Document, Resume/CV, News Article, Academic Document, Security/Vulnerability Report, General Document*).
- **Sentiment Analysis:** Sentence-level VADER polarity scoring with breakdown percentages and top positive/negative sentences.
- **Document Readability:** Flesch Reading Ease, Flesch-Kincaid Grade Level, sentence complexity, and vocabulary richness calculations.
- **Important Sentences & Simple Explanation:** Sentence importance ranking and term simplification via a local domain glossary.
- **Document Comparison:** Upload or select two documents to compare similarity percentages, shared vs. unique keywords, themes, and entities.
- **PDF & DOCX Reports:** Export complete analysis reports as formatted PDF or Word files.
- **Local User Auth:** User registration, login, session management, and Werkzeug password hashing.

---

## 3. NLP & Machine Learning Methods

### Document Classification Method
Uses local TF-IDF vector profiles combined with regex structural signal markers (e.g., `Abstract`, `References` for Research Papers; `CVE-`, `Exploit` for Security Reports). Computes cosine similarity scores to output category predictions with confidence metrics and reasoning.

### Document Q&A Method
Sentences are extracted and vectorized alongside the user's question using a local `TfidfVectorizer`. Sentences with the highest cosine similarity are ranked and returned with exact page citations `[Page X]`. Questions below the similarity score threshold (0.15) yield a transparent fallback message without hallucinating answers.

### Vulnerability / Risk Detection Method
Applies weighted security term matching coupled with regex negation patterns (e.g. `no known vulnerabilities`, `zero vulnerabilities`, `not vulnerable`). Sentences containing negations or procedural policy phrasing are discounted to avoid false positive alarms.

### Sentiment & Readability Methods
Sentence polarity is scored using NLTK's VADER lexicon. Readability uses the Flesch Reading Ease equation ($206.835 - 1.015 \times \text{ASL} - 84.6 \times \text{ASW}$) combined with syllable counting heuristics.

---

## 4. System Architecture & Folder Structure
```
smartdoc_nlp/
│
├── app.py                  # Main Flask server, routes, and SQLite schema
├── requirements.txt        # Backend Python dependencies
├── README.md               # Documentation
├── test_app.py             # 12-suite automated test file
│
├── utils/
│   ├── preprocessing.py    # spaCy cleaning and tokenization
│   ├── pdf_extractor.py    # Page-mapped PDF/DOCX/TXT text extraction
│   ├── summarizer.py       # Extractive sentence scoring summarizer
│   ├── keyword_extractor.py# Multi-word n-gram keyphrase extraction
│   ├── theme_extractor.py  # Noun phrase theme detection
│   ├── ner.py              # Named entity recognition
│   ├── classifier.py       # Document classifier
│   ├── sentiment.py        # VADER sentiment analyzer
│   ├── readability.py      # Flesch readability calculator
│   ├── vulnerability_detector.py # Vulnerability & risk scanner
│   ├── important_sentences.py # Sentence ranking & simple explanation
│   ├── qa_engine.py        # Local extractive Q&A engine
│   ├── document_comparator.py # Dual document comparison matrix
│   ├── report_generator.py # PDF (ReportLab) & DOCX (python-docx) generators
│   └── statistics.py       # Linguistic document statistics
│
├── templates/
│   ├── login.html          # User login
│   ├── register.html       # User registration
│   ├── index.html          # File upload & text input page
│   ├── results.html        # Complete analysis dashboard
│   ├── compare.html        # Document comparison dashboard
│   └── history.html        # Multi-user history log
│
├── static/
│   ├── css/
│   │   └── style.css       # Dark dashboard theme & badges
│   └── js/
│       └── script.js       # Drag-and-drop, word counters, Q&A AJAX
│
├── database/
│   └── smartdoc.db         # SQLite database
└── uploads/                # Temporary file upload directory
```

---

## 5. Database Structure
SQLite is initialized in `database/smartdoc.db` with relational foreign keys:

- `users`: User authentication (`username`, `email`, `password_hash`).
- `documents`: Uploaded files (`user_id`, `filename`, `file_type`, `file_hash`).
- `document_pages`: Page-mapped text (`document_id`, `page_number`, `page_text`).
- `analyses`: Saved NLP results (`summary`, `classification`, `sentiment`, `readability`, `vulnerability`, `keywords`, `themes`, `entities`, `stats`).
- `qa_history`: Logged document questions & extractive answers (`question`, `answer`, `citations`, `confidence_score`).
- `comparison_history`: Dual document comparison matrix logs (`similarity_percentage`, `comparison_data`).

---

## 6. Installation & How to Run

### Prerequisites
- Python 3.8 to 3.11 installed.

### Setup Instructions
1. Navigate to the project directory:
   ```bash
   cd smartdoc_nlp
   ```

2. Install local dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: spaCy's `en_core_web_sm` model and NLTK lexicons download automatically on first run).*

3. Run the Flask application:
   ```bash
   python app.py
   ```

4. Open your browser:
   ```text
   http://localhost:5000
   ```

5. Run Automated Tests:
   ```bash
   python test_app.py
   ```

---

## 7. Limitations & Future Improvements
- **Scanned PDF Documents:** PDFs containing scanned image pages require OCR (e.g. Tesseract) for text extraction.
- **Multilingual Support:** Current local models target English documents; support for multi-language spaCy models can be added.
- **CSV Export:** Support exporting entity matrices to CSV/Excel files.

---

## 8. Confirmation
**This application operates 100% locally and does NOT require any cloud API key or external LLM service.**
