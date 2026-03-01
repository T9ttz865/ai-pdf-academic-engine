from flask import Flask, render_template, request, jsonify
from PyPDF2 import PdfReader
import os

# New SDK (replacement for deprecated google.generativeai)
from google import genai

app = Flask(__name__)

# ===============================
# Gemini / GenAI Client
# ===============================

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("Error: GEMINI_API_KEY is not set. Please add it in environment variables.")

MODEL_NAME = "gemini-2.5-flash"

client = genai.Client(api_key=API_KEY)

# ===============================
# Simple in-memory storage for last uploaded PDF text
# ===============================
LAST_PDF_TEXT = ""

# ===============================
# Pages
# ===============================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/pdf")
def pdf_page():
    return render_template("pdf.html")

@app.route("/text")
def text_page():
    return render_template("text.html")

@app.route("/about")
def about_page():
    return render_template("about.html")

# ===============================
# Helpers
# ===============================
def build_system_prompt() -> str:
    return (
        "You are Badr Ai — created by ENG: Badraldeen Mortatha.\n"
        "You are an academic AI assistant specialized in:\n"
        "- PDF summarization\n"
        "- Academic explanations\n"
        "- Generating questions\n"
        "- Extracting key points\n"
        "- Translation\n"
        "If the user asks unrelated things, redirect them to academic assistance.\n"
        "Never say you are Gemini or Google AI.\n"
        "Always say you are Badr Ai.\n"
    )

def gen_text(prompt: str) -> str:
    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )
    return (resp.text or "").strip()

# ===============================
# Chat API (Text + PDF Q&A)
# ===============================
@app.route("/chat", methods=["POST"])
def chat():
    global LAST_PDF_TEXT

    try:
        data = request.get_json(silent=True) or {}
        user_message = (data.get("message") or "").strip()
        mode = (data.get("mode") or "text").strip().lower()

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        system_prompt = build_system_prompt()

        if mode == "pdf":
            if not LAST_PDF_TEXT:
                return jsonify({"error": "No PDF uploaded yet."}), 400

            prompt = (
                f"{system_prompt}\n"
                "PDF Content:\n" + LAST_PDF_TEXT + "\n\n"
                "Answer the user's question using ONLY this content:\n"
                f"{user_message}"
            )
        else:
            prompt = f"{system_prompt}\nUser:\n{user_message}\n"

        reply = gen_text(prompt)
        return jsonify({"reply": reply or "No reply generated."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===============================
# PDF Upload + Analyze
# ===============================
@app.route("/analyze_pdf", methods=["POST"])
def analyze_pdf():
    global LAST_PDF_TEXT

    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        reader = PdfReader(file)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text)

        full_text = "\n\n".join(text_parts).strip()
        if not full_text:
            return jsonify({"error": "Could not extract text from PDF."}), 400

        LAST_PDF_TEXT = full_text[:12000]

        prompt = (
            f"{build_system_prompt()}\n"
            "Summarize this PDF text and extract key points, questions, and explanation.\n"
            f"{LAST_PDF_TEXT}"
        )

        reply = gen_text(prompt)
        return jsonify({"reply": reply or "No analysis generated."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===============================
# Run Server
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))