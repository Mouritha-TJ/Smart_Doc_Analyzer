import os
import sqlite3
import json
import hashlib
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Import NLP utilities
from utils.preprocessing import preprocess_text
from utils.pdf_extractor import extract_document_content
from utils.summarizer import summarize_text
from utils.keyword_extractor import extract_keywords
from utils.theme_extractor import extract_themes
from utils.ner import extract_entities
from utils.statistics import calculate_statistics

# New NLP utilities
from utils.classifier import classify_document
from utils.sentiment import analyze_sentiment
from utils.readability import analyze_readability
from utils.vulnerability_detector import analyze_vulnerability_level
from utils.important_sentences import extract_important_sentences, explain_simply

from utils.document_comparator import compare_documents
from utils.report_generator import generate_pdf_report, generate_docx_report
from utils.translator import translate_to_tamil

app = Flask(__name__)
app.secret_key = "smartdoc_nlp_intelligent_local_system_secret_key"

# Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "smartdoc.db")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB limit

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATABASE_DIR, exist_ok=True)

# Database Connection Helper
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Documents Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Document Pages Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            page_number INTEGER,
            page_text TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """)

    # Analyses Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            summary TEXT NOT NULL,
            summary_level TEXT DEFAULT 'medium',
            classification TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            readability TEXT NOT NULL,
            vulnerability TEXT NOT NULL,
            important_sentences TEXT NOT NULL,
            keywords TEXT NOT NULL,
            themes TEXT NOT NULL,
            entities TEXT NOT NULL,
            stats TEXT NOT NULL,
            compression_percentage REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Migration: Ensure summary_level column exists in existing analyses table
    cursor.execute("PRAGMA table_info(analyses)")
    analyses_columns = [col[1] for col in cursor.fetchall()]
    if "summary_level" not in analyses_columns:
        cursor.execute("ALTER TABLE analyses ADD COLUMN summary_level TEXT DEFAULT 'medium'")

    # Q&A History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qa_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            citations TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Comparison History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comparison_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            doc_a_name TEXT NOT NULL,
            doc_b_name TEXT NOT NULL,
            similarity_percentage REAL NOT NULL,
            comparison_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Translation Cache Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS translations_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_hash TEXT NOT NULL,
            source_text TEXT NOT NULL,
            target_lang TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(text_hash, target_lang)
        )
    """)

    # Create default demo user if no users exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        demo_pass = generate_password_hash("admin123")
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                       ("admin", "admin@smartdoc.local", demo_pass))

    conn.commit()
    conn.close()

# Initialize DB on app startup
init_db()

# Auth Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this feature.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

ALLOWED_EXTENSIONS = {"txt", "pdf", "docx"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Auth Routes ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")

        conn = get_db_connection()
        try:
            pass_hash = generate_password_hash(password)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                           (username, email, pass_hash))
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username or email already exists.", "error")
            return render_template("register.html")
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username.lower())).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username/email or password.", "error")
            return render_template("login.html")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

# --- Main App Routes ---
@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    user_id = session["user_id"]
    input_method = request.form.get("input_method", "text")
    summary_length = request.form.get("summary_length", "medium")
    custom_title = request.form.get("custom_title", "").strip()

    document_name = ""
    full_text = ""
    pages_data = []
    file_type = "txt"

    try:
        if input_method == "file":
            if "file_upload" not in request.files:
                flash("No file included in upload.", "error")
                return redirect(url_for("index"))

            file = request.files["file_upload"]
            if file.filename == "":
                flash("No file selected.", "error")
                return redirect(url_for("index"))

            if not allowed_file(file.filename):
                flash("Invalid file format. Supported formats: PDF, DOCX, TXT.", "error")
                return redirect(url_for("index"))

            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            # Use custom title if provided, otherwise use the filename
            document_name = custom_title if custom_title else filename
            try:
                extracted = extract_document_content(file_path)
                full_text = extracted["full_text"]
                pages_data = extracted["pages"]
                file_type = extracted["file_type"]
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            full_text = request.form.get("pasted_text", "").strip()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Use custom title if provided, otherwise default label
            document_name = custom_title if custom_title else f"Pasted Text - {timestamp}"
            pages_data = [{"page": None, "text": full_text}]
            file_type = "pasted"

        if not full_text or len(full_text.strip()) == 0:
            flash("Error: Uploaded input contains no readable text.", "error")
            return redirect(url_for("index"))

        words = full_text.split()
        if len(words) < 5:
            flash("Error: Input text is too short for analysis (minimum 5 words).", "error")
            return redirect(url_for("index"))

        # Calculate SHA256 file hash for caching check
        file_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check existing cached analysis for user
        cached_doc = cursor.execute(
            "SELECT id FROM documents WHERE user_id = ? AND file_hash = ?", (user_id, file_hash)
        ).fetchone()

        if cached_doc:
            cached_analysis = cursor.execute(
                "SELECT id FROM analyses WHERE document_id = ?", (cached_doc["id"],)
            ).fetchone()
            if cached_analysis:
                conn.close()
                flash("Reused cached document analysis.", "info")
                return redirect(url_for("results", analysis_id=cached_analysis["id"]))

        # Run Core NLP Pipeline
        doc, cleaned_tokens = preprocess_text(full_text)

        # 1. Extractive Summary
        summary_text, selected_sentence_count = summarize_text(doc, length_option=summary_length)

        # 2. Keyphrase & Theme Extraction
        keywords = extract_keywords(doc)
        themes = extract_themes(doc)

        # 3. Named Entity Recognition
        entities = extract_entities(doc)

        # 4. Classification
        classification = classify_document(full_text)

        # 5. Sentiment Analysis
        sentiment = analyze_sentiment(doc, pages_data=pages_data, doc_category=classification["category"])

        # 6. Readability & Quality Analysis
        readability = analyze_readability(full_text, doc)

        # 7. Vulnerability & Risk Level Detection
        vulnerability = analyze_vulnerability_level(doc, pages_data=pages_data)

        # 8. Important Sentences
        imp_sentences = extract_important_sentences(doc, pages_data=pages_data, top_n=5)

        # 9. Statistics
        stats = calculate_statistics(full_text, doc, summary_text, selected_sentence_count)

        # Save Document to DB
        cursor.execute(
            "INSERT INTO documents (user_id, filename, file_type, file_hash) VALUES (?, ?, ?, ?)",
            (user_id, document_name, file_type, file_hash)
        )
        doc_id = cursor.lastrowid

        # Save Pages to DB
        for p in pages_data:
            cursor.execute(
                "INSERT INTO document_pages (document_id, page_number, page_text) VALUES (?, ?, ?)",
                (doc_id, p["page"], p["text"])
            )

        # Save Analysis to DB
        cursor.execute(
            """
            INSERT INTO analyses 
            (document_id, user_id, summary, summary_level, classification, sentiment, readability, vulnerability, important_sentences, keywords, themes, entities, stats, compression_percentage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                user_id,
                summary_text,
                summary_length,
                json.dumps(classification),
                json.dumps(sentiment),
                json.dumps(readability),
                json.dumps(vulnerability),
                json.dumps(imp_sentences),
                json.dumps(keywords),
                json.dumps(themes),
                json.dumps(entities),
                json.dumps(stats),
                stats["compression_percentage"]
            )
        )
        analysis_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return redirect(url_for("results", analysis_id=analysis_id))

    except ValueError as ve:
        flash(f"Error: {str(ve)}", "error")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"An error occurred during NLP processing: {str(e)}", "error")
        return redirect(url_for("index"))

@app.route("/results/<int:analysis_id>")
@login_required
def results(analysis_id):
    user_id = session["user_id"]
    conn = get_db_connection()

    row = conn.execute(
        """
        SELECT a.*, d.filename, d.file_type 
        FROM analyses a 
        JOIN documents d ON a.document_id = d.id 
        WHERE a.id = ? AND a.user_id = ?
        """,
        (analysis_id, user_id)
    ).fetchone()

    if not row:
        conn.close()
        flash("Analysis report not found or unauthorized.", "error")
        return redirect(url_for("index"))

    conn.close()

    analysis = {
        "id": row["id"],
        "document_name": row["filename"],
        "summary": row["summary"],
        "summary_level": row["summary_level"] if "summary_level" in row.keys() else "medium",
        "classification": json.loads(row["classification"]),
        "sentiment": json.loads(row["sentiment"]),
        "readability": json.loads(row["readability"]),
        "vulnerability": json.loads(row["vulnerability"]),
        "important_sentences": json.loads(row["important_sentences"]),
        "keywords": json.loads(row["keywords"]),
        "themes": json.loads(row["themes"]),
        "entities": json.loads(row["entities"]),
        "stats": json.loads(row["stats"]),
        "compression_percentage": row["compression_percentage"],
        "created_at": row["created_at"]
    }

    # Chart data
    keywords = analysis["keywords"]
    if keywords and isinstance(keywords[0], dict):
        chart_words = [item["phrase"] for item in keywords[:8]]
        chart_counts = [item["frequency"] for item in keywords[:8]]
    else:
        chart_words = keywords[:8]
        chart_counts = [1] * len(chart_words)

    return render_template(
        "results.html",
        analysis=analysis,
        chart_words=chart_words,
        chart_counts=chart_counts
    )

# --- Dynamic Summary Level Endpoint ---
@app.route("/api/summary/<int:analysis_id>", methods=["POST"])
@login_required
def update_summary_level(analysis_id):
    import traceback
    user_id = session["user_id"]

    if not request.is_json:
        return jsonify({"success": False, "error": "Request must be JSON"}), 400

    data = request.get_json()
    level = data.get("level", "medium")

    valid_levels = ("very_short", "short", "medium", "detailed")
    if level not in valid_levels:
        level = "medium"

    try:
        conn = get_db_connection()
        row = conn.execute(
            "SELECT a.*, d.filename FROM analyses a JOIN documents d ON a.document_id = d.id WHERE a.id = ? AND a.user_id = ?",
            (analysis_id, user_id)
        ).fetchone()

        if not row:
            conn.close()
            return jsonify({"success": False, "error": "Analysis not found or unauthorized"}), 404

        # Fetch document text from pages
        pages = conn.execute(
            "SELECT page_text FROM document_pages WHERE document_id = ? ORDER BY id ASC",
            (row["document_id"],)
        ).fetchall()

        if not pages:
            conn.close()
            return jsonify({"success": False, "error": "Document pages not found in database"}), 404

        full_text = "\n\n".join([p["page_text"] for p in pages])

        # Re-run NLP preprocessing + extractive summariser
        doc, _ = preprocess_text(full_text)
        summary_text, selected_sentence_count = summarize_text(doc, length_option=level)

        # Persist updated summary to DB
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE analyses SET summary = ?, summary_level = ? WHERE id = ?",
            (summary_text, level, analysis_id)
        )
        conn.commit()
        conn.close()

        # Tamil translation (local, offline)
        summary_ta = translate_to_tamil(summary_text)

        return jsonify({
            "success": True,
            "analysis_id": analysis_id,
            "document_name": row["filename"],
            "level": level,
            "summary": summary_text,
            "summary_ta": summary_ta,
            "sentence_count": selected_sentence_count
        })

    except Exception as e:
        traceback.print_exc()   # Print full stack trace to Flask terminal
        return jsonify({"success": False, "error": str(e)}), 500


# --- Translation API Endpoint (Offline Local) ---
@app.route("/api/translate", methods=["POST"])
@login_required
def translate_api():
    if request.is_json:
        data = request.get_json()
        text = data.get("text", "").strip()
        target_lang = data.get("target_lang", "ta")
    else:
        text = request.form.get("text", "").strip()
        target_lang = request.form.get("target_lang", "ta")

    if not text:
        return jsonify({"success": False, "error": "Empty text provided"}), 400

    if target_lang == "ta":
        translated = translate_to_tamil(text)
    else:
        translated = text

    return jsonify({
        "success": True,
        "original": text,
        "translated": translated,
        "target_lang": target_lang
    })


# --- Simple Explanation Endpoint ---
@app.route("/simple_explain/<int:analysis_id>", methods=["GET"])
@login_required
def simple_explain_route(analysis_id):
    user_id = session["user_id"]
    conn = get_db_connection()
    analysis_row = conn.execute("SELECT * FROM analyses WHERE id = ? AND user_id = ?", (analysis_id, user_id)).fetchone()
    if not analysis_row:
        conn.close()
        return jsonify({"error": "Analysis document not found."}), 404

    pages = conn.execute("SELECT page_number as page, page_text as text FROM document_pages WHERE document_id = ? ORDER BY id ASC", (analysis_row["document_id"],)).fetchall()
    conn.close()

    pages_data = [{"page": p["page"], "text": p["text"]} for p in pages]
    full_text = "\n\n".join([p["text"] for p in pages_data])
    doc, _ = preprocess_text(full_text)

    res = explain_simply(doc, pages_data=pages_data)
    res["explanation_ta"] = translate_to_tamil(res["explanation"])
    return jsonify(res)

# --- Document Comparison Routes ---
@app.route("/compare", methods=["GET", "POST"])
@login_required
def compare():
    user_id = session["user_id"]
    conn = get_db_connection()

    user_analyses = conn.execute(
        """
        SELECT a.id, d.filename, a.created_at 
        FROM analyses a 
        JOIN documents d ON a.document_id = d.id 
        WHERE a.user_id = ? 
        ORDER BY a.created_at DESC
        """,
        (user_id,)
    ).fetchall()

    if request.method == "POST":
        doc_a_id = request.form.get("doc_a_id")
        doc_b_id = request.form.get("doc_b_id")

        if not doc_a_id or not doc_b_id or doc_a_id == doc_b_id:
            conn.close()
            flash("Please select two distinct documents to compare.", "error")
            return render_template("compare.html", user_analyses=user_analyses)

        row_a = conn.execute("SELECT a.*, d.filename FROM analyses a JOIN documents d ON a.document_id = d.id WHERE a.id = ? AND a.user_id = ?", (doc_a_id, user_id)).fetchone()
        row_b = conn.execute("SELECT a.*, d.filename FROM analyses a JOIN documents d ON a.document_id = d.id WHERE a.id = ? AND a.user_id = ?", (doc_b_id, user_id)).fetchone()

        if not row_a or not row_b:
            conn.close()
            flash("Selected documents not found.", "error")
            return render_template("compare.html", user_analyses=user_analyses)

        pages_a = conn.execute("SELECT page_text FROM document_pages WHERE document_id = ?", (row_a["document_id"],)).fetchall()
        pages_b = conn.execute("SELECT page_text FROM document_pages WHERE document_id = ?", (row_b["document_id"],)).fetchall()

        text_a = "\n".join([p["page_text"] for p in pages_a])
        text_b = "\n".join([p["page_text"] for p in pages_b])

        data_a = {
            "document_name": row_a["filename"],
            "original_text": text_a,
            "original_word_count": json.loads(row_a["stats"])["words"],
            "keywords": json.loads(row_a["keywords"]),
            "themes": json.loads(row_a["themes"]),
            "entities": json.loads(row_a["entities"]),
            "classification": json.loads(row_a["classification"]),
            "sentiment": json.loads(row_a["sentiment"]),
            "readability": json.loads(row_a["readability"])
        }

        data_b = {
            "document_name": row_b["filename"],
            "original_text": text_b,
            "original_word_count": json.loads(row_b["stats"])["words"],
            "keywords": json.loads(row_b["keywords"]),
            "themes": json.loads(row_b["themes"]),
            "entities": json.loads(row_b["entities"]),
            "classification": json.loads(row_b["classification"]),
            "sentiment": json.loads(row_b["sentiment"]),
            "readability": json.loads(row_b["readability"])
        }

        comp_result = compare_documents(data_a, data_b)

        # Log comparison to DB
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO comparison_history (user_id, doc_a_name, doc_b_name, similarity_percentage, comparison_data)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, data_a["document_name"], data_b["document_name"], comp_result["similarity_percentage"], json.dumps(comp_result))
        )
        conn.commit()
        conn.close()

        return render_template("compare.html", user_analyses=user_analyses, comp_result=comp_result)

    conn.close()
    return render_template("compare.html", user_analyses=user_analyses)

# --- History Routes ---
@app.route("/history")
@login_required
def history():
    user_id = session["user_id"]
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT a.id, d.filename, a.keywords, a.classification, a.vulnerability, a.compression_percentage, a.created_at
        FROM analyses a
        JOIN documents d ON a.document_id = d.id
        WHERE a.user_id = ?
        ORDER BY a.created_at DESC
        """,
        (user_id,)
    ).fetchall()
    conn.close()

    history_list = []
    for row in rows:
        kw = json.loads(row["keywords"])
        kw_list = [item["phrase"] for item in kw] if kw and isinstance(kw[0], dict) else kw
        cls = json.loads(row["classification"])
        vuln = json.loads(row["vulnerability"])

        history_list.append({
            "id": row["id"],
            "document_name": row["filename"],
            "keywords": kw_list,
            "category": cls.get("category", "General"),
            "vulnerability_level": vuln.get("level", "LOW"),
            "compression_percentage": row["compression_percentage"],
            "created_at": row["created_at"]
        })

    return render_template("history.html", history=history_list)

@app.route("/history/delete/<int:analysis_id>", methods=["POST"])
@login_required
def delete_history(analysis_id):
    user_id = session["user_id"]
    conn = get_db_connection()
    conn.execute("DELETE FROM analyses WHERE id = ? AND user_id = ?", (analysis_id, user_id))
    conn.commit()
    conn.close()
    flash("Document analysis record deleted successfully.", "success")
    return redirect(url_for("history"))

@app.route("/history/clear", methods=["POST"])
@login_required
def clear_history():
    user_id = session["user_id"]
    conn = get_db_connection()
    conn.execute("DELETE FROM analyses WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("Your document analysis history has been cleared.", "success")
    return redirect(url_for("history"))

# --- Report Download Routes ---
@app.route("/report/pdf/<int:analysis_id>")
@login_required
def download_pdf_report(analysis_id):
    user_id = session["user_id"]
    conn = get_db_connection()
    row = conn.execute(
        "SELECT a.*, d.filename FROM analyses a JOIN documents d ON a.document_id = d.id WHERE a.id = ? AND a.user_id = ?",
        (analysis_id, user_id)
    ).fetchone()
    conn.close()

    if not row:
        return "Report not found or unauthorized.", 404

    analysis_data = _prepare_analysis_dict(row)
    pdf_bytes = generate_pdf_report(analysis_data)
    safe_name = secure_filename(row["filename"]).rsplit(".", 1)[0]

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-disposition": f"attachment; filename=smartdoc_report_{safe_name}.pdf"}
    )

@app.route("/report/docx/<int:analysis_id>")
@login_required
def download_docx_report(analysis_id):
    user_id = session["user_id"]
    conn = get_db_connection()
    row = conn.execute(
        "SELECT a.*, d.filename FROM analyses a JOIN documents d ON a.document_id = d.id WHERE a.id = ? AND a.user_id = ?",
        (analysis_id, user_id)
    ).fetchone()
    conn.close()

    if not row:
        return "Report not found or unauthorized.", 404

    analysis_data = _prepare_analysis_dict(row)
    docx_bytes = generate_docx_report(analysis_data)
    safe_name = secure_filename(row["filename"]).rsplit(".", 1)[0]

    return Response(
        docx_bytes,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-disposition": f"attachment; filename=smartdoc_report_{safe_name}.docx"}
    )

@app.route("/report/download/<int:analysis_id>")
@login_required
def download_txt_report(analysis_id):
    return redirect(url_for("download_pdf_report", analysis_id=analysis_id))

def _prepare_analysis_dict(row) -> dict:
    return {
        "id": row["id"],
        "document_name": row["filename"],
        "summary": row["summary"],
        "original_word_count": json.loads(row["stats"])["words"],
        "compression_percentage": row["compression_percentage"],
        "classification": json.loads(row["classification"]),
        "sentiment": json.loads(row["sentiment"]),
        "readability": json.loads(row["readability"]),
        "vulnerability": json.loads(row["vulnerability"]),
        "important_sentences": json.loads(row["important_sentences"]),
        "keywords": json.loads(row["keywords"]),
        "themes": json.loads(row["themes"]),
        "entities": json.loads(row["entities"]),
        "stats": json.loads(row["stats"]),
        "created_at": row["created_at"]
    }

if __name__ == "__main__":
    print("Starting SmartDoc NLP server...")
    print("Point your browser to http://localhost:5000")
    app.run(host="localhost", port=5000, debug=True)
