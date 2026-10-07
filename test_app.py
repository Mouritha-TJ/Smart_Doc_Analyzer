import unittest
import os
import json
import uuid
import sqlite3
from werkzeug.security import check_password_hash

from app import app, init_db, get_db_connection
from utils.preprocessing import preprocess_text
from utils.pdf_extractor import extract_document_content
from utils.summarizer import summarize_text
from utils.keyword_extractor import extract_keywords
from utils.theme_extractor import extract_themes
from utils.ner import extract_entities
from utils.statistics import calculate_statistics

# NLP modules
from utils.classifier import classify_document
from utils.sentiment import analyze_sentiment
from utils.readability import analyze_readability
from utils.vulnerability_detector import analyze_vulnerability_level
from utils.important_sentences import extract_important_sentences, explain_simply
from utils.qa_engine import answer_question
from utils.document_comparator import compare_documents
from utils.report_generator import generate_pdf_report, generate_docx_report
from utils.translator import translate_to_tamil

class TestSmartDocNLPComplete(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        init_db()

    def setUp(self):
        self.client = app.test_client()
        
        # Sample Document 1: Student Mental Health Report
        self.student_report_text = (
            "Student Mental Health Report Analysis. "
            "Academic pressure, sleep and daily routine, social relationships, financial concerns, "
            "career uncertainty, and digital media use are identified as major factors affecting student mental health. "
            "The university recommends strengthening campus counseling services, expanding wellness programs, "
            "and establishing student peer support groups across all departments."
        )

        # Sample Document 2: Security Assessment
        self.sample_vulnerable_text = (
            "Security Assessment Report for Enterprise Core Application. "
            "Our security audit identified a critical SQL injection vulnerability in the login portal. "
            "Additionally, an authentication bypass issue allows unauthorized access to administrative features. "
            "We recommend immediate deployment of patch version 2.4 and enforcing strong access control."
        )

        self.sample_safe_text = (
            "Quarterly Technology Infrastructure Review. "
            "The infrastructure architecture team has completed the quarterly audit. "
            "This application has no known vulnerabilities and zero security risks reported. "
            "All server configurations meet compliance standards and employee training is up to date."
        )

    def test_preprocessing_and_tokens(self):
        doc, tokens = preprocess_text(self.student_report_text)
        self.assertIsNotNone(doc)
        self.assertGreater(len(tokens), 0)
        self.assertIn("health", tokens)

    def test_keyphrase_extraction(self):
        doc, _ = preprocess_text(self.student_report_text)
        keywords = extract_keywords(doc, top_n=5)
        self.assertGreaterEqual(len(keywords), 1)

    def test_document_classification(self):
        res = classify_document(self.sample_vulnerable_text)
        self.assertIn("category", res)
        self.assertEqual(res["category"], "Security / Vulnerability Report")
        self.assertGreaterEqual(res["confidence"], 60)

    def test_sentiment_analysis(self):
        doc, _ = preprocess_text(self.student_report_text)
        res = analyze_sentiment(doc, doc_category="Academic Document")
        self.assertIn("overall", res)
        self.assertIn("positive_pct", res)

    def test_readability_analysis(self):
        doc, _ = preprocess_text(self.student_report_text)
        res = analyze_readability(self.student_report_text, doc)
        self.assertIn("flesch_reading_ease", res)
        self.assertIn("grade_level", res)

    def test_vulnerability_detection_high_risk(self):
        doc, _ = preprocess_text(self.sample_vulnerable_text)
        res = analyze_vulnerability_level(doc)
        self.assertIn(res["level"], ["HIGH", "CRITICAL"])
        self.assertGreaterEqual(res["score"], 25)

    def test_vulnerability_detection_negation_safe(self):
        doc, _ = preprocess_text(self.sample_safe_text)
        res = analyze_vulnerability_level(doc)
        self.assertEqual(res["level"], "LOW")
        self.assertTrue(res["has_negation"])

    def test_summary_level_adjustments(self):
        doc, _ = preprocess_text(self.student_report_text)
        
        # Test all summary levels
        s_very_short, c_vshort = summarize_text(doc, length_option="very_short")
        s_short, c_short = summarize_text(doc, length_option="short")
        s_medium, c_med = summarize_text(doc, length_option="medium")
        s_detailed, c_det = summarize_text(doc, length_option="detailed")

        self.assertGreater(len(s_very_short), 0)
        self.assertGreaterEqual(c_short, 1)
        self.assertGreaterEqual(c_det, c_vshort)

    def test_local_extractive_qa_matching(self):
        doc, _ = preprocess_text(self.student_report_text)
        pages_data = [{"page": 2, "text": self.student_report_text}]
        
        # Question with direct keyword overlap
        res = answer_question("What are the main factors affecting student mental health?", doc, pages_data=pages_data)
        self.assertIn("Academic pressure", res["answer"])
        self.assertIn("Page 2", res["page_text"])
        self.assertGreater(res["confidence"], 0)

    def test_local_extractive_qa_zero_hallucination_france(self):
        doc, _ = preprocess_text(self.student_report_text)
        pages_data = [{"page": 1, "text": self.student_report_text}]
        
        # Unrelated query -> MUST return zero-hallucination fallback
        res = answer_question("What is the capital of France?", doc, pages_data=pages_data)
        self.assertEqual(res["answer"], "No relevant information was found in this document.")
        self.assertEqual(res["confidence"], 0.0)

    def test_local_offline_tamil_translation(self):
        sample_en = "Student mental health is influenced by academic pressure and sleep."
        tamil_trans = translate_to_tamil(sample_en)
        self.assertIsNotNone(tamil_trans)
        self.assertGreater(len(tamil_trans), 0)
        # Should contain Tamil characters or translated terms
        self.assertTrue(any(ord(c) >= 0x0B80 and ord(c) <= 0x0BFF for c in tamil_trans))

    def test_document_comparison(self):
        doc_a = {"document_name": "Doc A", "original_text": self.sample_vulnerable_text, "keywords": ["Security", "Audit"]}
        doc_b = {"document_name": "Doc B", "original_text": self.sample_safe_text, "keywords": ["Review", "Audit"]}
        res = compare_documents(doc_a, doc_b)
        self.assertIn("similarity_percentage", res)
        self.assertIn("Audit", res["keywords"]["common"])

    def test_pdf_and_docx_report_generation(self):
        mock_data = {
            "document_name": "Student_Mental_Health_Report.docx",
            "summary": "This is a student mental health summary.",
            "original_word_count": 100,
            "compression_percentage": 60.0,
            "classification": {"category": "Academic Document", "confidence": 85, "reasoning": "Test"},
            "sentiment": {"overall": "Neutral", "positive_pct": 10, "neutral_pct": 80, "negative_pct": 10},
            "readability": {"flesch_reading_ease": 65.0, "grade_level": "Standard", "vocabulary_richness": 0.5},
            "vulnerability": {"level": "LOW", "score": 5, "indicators": []},
            "important_sentences": [],
            "keywords": [{"phrase": "Mental Health", "frequency": 3}],
            "themes": ["Mental Health", "Education"],
            "entities": {"flat": []},
            "stats": {"words": 100, "sentences": 5}
        }

        pdf_bytes = generate_pdf_report(mock_data)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

        docx_bytes = generate_docx_report(mock_data)
        self.assertTrue(len(docx_bytes) > 0)

    def test_user_authentication_flow(self):
        unique_id = uuid.uuid4().hex[:8]
        u_name = f"user_{unique_id}"
        u_email = f"{u_name}@smartdoc.local"

        # 1. Register User
        res_reg = self.client.post('/register', data={
            'username': u_name,
            'email': u_email,
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b"Registration successful", res_reg.data)

        # 2. Login User
        res_login = self.client.post('/login', data={
            'username': u_name,
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b"Welcome back", res_login.data)

        # 3. Access Protected Route
        res_index = self.client.get('/')
        self.assertEqual(res_index.status_code, 200)

        # 4. Logout
        res_logout = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b"logged out", res_logout.data)

if __name__ == "__main__":
    unittest.main()
