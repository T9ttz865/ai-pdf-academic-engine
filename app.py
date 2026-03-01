from flask import Flask, render_template, request, jsonify
from PyPDF2 import PdfReader

# New SDK (replacement for deprecated google.generativeai)
from google import genai

app = Flask(__name__)

# ===============================
# Gemini / GenAI Client
# ===============================
API_KEY = "AIzaSyAyeY1YEwvjmzhaqBtPpN00cjZeBVYtuFI"
MODEL_NAME = "gemini-2.5-flash"  # stable/current in docs

client = genai.Client(api_key=API_KEY)

# ===============================
# Simple in-memory storage for last uploaded PDF text
# (OK for local/dev single-user. For production use DB/session storage.)
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
        "You are Badr Ai — created by ENG: Badraldeen Mortatha .\n"
        "You are an academic AI assistant specialized in:\n"
        "- PDF summarization\n"
        "- Academic explanations\n"
        "- Generating questions\n"
        "- Extracting key points\n"
        "- Translation\n"
        "If user asks unrelated things, redirect them to academic assistance.\n"
        "Never say you are Gemini or Google AI.\n"
        "Always say you are Badr Ai.\n"
    )


def gen_text(prompt: str) -> str:
    # Centralized generation call
    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )
    # resp.text is the simplest accessor
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
        mode = (data.get("mode") or "text").strip().lower()  # "text" or "pdf"

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        system_prompt = build_system_prompt()

        if mode == "pdf":
            if not LAST_PDF_TEXT.strip():
                return jsonify({"error": "No PDF uploaded yet. Please upload a PDF first."}), 400

            prompt = (
                f"{system_prompt}\n"
                "You have the following PDF content extracted as text. Answer the user's question ONLY using this content.\n"
                "If the answer is not in the content, say you cannot find it in the document.\n\n"
                f"PDF Content:\n{LAST_PDF_TEXT}\n\n"
                f"User Question:\n{user_message}\n"
            )
        else:
            prompt = f"{system_prompt}\nUser:\n{user_message}\n"

        reply = gen_text(prompt)
        if not reply:
            reply = "I couldn't generate a response. Please try again."

        return jsonify({"reply": reply})

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
            return jsonify({"error": "Could not extract text from this PDF (maybe scanned images)."}), 400

        # Store for later Q&A in /chat mode="pdf"
        # Keep it limited to avoid huge prompts (you can increase if needed).
        LAST_PDF_TEXT = full_text[:12000]

        prompt = (
            f"{build_system_prompt()}\n"
            "Analyze the following academic PDF content and return:\n"
            "1) Summary in clear bullet points\n"
            "2) Key concepts\n"
            "3) 5–10 possible exam questions\n"
            "4) Short academic explanation\n\n"
            f"Content:\n{LAST_PDF_TEXT}\n"
        )

        reply = gen_text(prompt)
        if not reply:
            reply = "I extracted the PDF text, but couldn't generate the analysis. Try again."

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===============================
# Run Server
# ===============================
import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))