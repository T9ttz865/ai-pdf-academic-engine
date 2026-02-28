from flask import Flask, render_template, request, jsonify
import PyPDF2
import requests
import re
import os

app = Flask(__name__)

# =========================
# HuggingFace API
# =========================

HF_TOKEN = os.getenv("HF_TOKEN")

API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"
headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

# =========================
# تنظيف النص
# =========================

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# =========================
# تقسيم ذكي
# =========================

def chunk_text(text, chunk_size=1200):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end

    return chunks

# =========================
# بناء البرومبت حسب الاختيار
# =========================

def build_prompt(text, mode):

    if mode == "summary":
        return f"""
Summarize the following academic text professionally.
Start with a definition, explain importance, mention implications.
Avoid repetition.

Text:
{text}
"""

    elif mode == "points":
        return f"""
Extract clear structured bullet points from the following academic text:

{text}
"""

    elif mode == "questions":
        return f"""
Generate 10 clear academic exam-style questions based on this content:

{text}
"""

    elif mode == "simple":
        return f"""
Explain this academic text in simple language for students:

{text}
"""

    elif mode == "translate":
        return f"""
Translate the following text to English professionally:

{text}
"""

    return text

# =========================
# الصفحة الرئيسية
# =========================

@app.route("/")
def home():
    return render_template("index.html")

# =========================
# التحليل
# =========================

@app.route("/analyze", methods=["POST"])
def analyze():

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    mode = request.form.get("mode", "summary")

    try:
        reader = PyPDF2.PdfReader(file)
        text = ""

        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted

        if not text.strip():
            return jsonify({"error": "No readable text in PDF"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    text = clean_text(text)
    chunks = chunk_text(text)

    all_results = []

    for chunk in chunks:

        prompt = build_prompt(chunk, mode)

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 250,
                "temperature": 0.7
            }
        }

        response = requests.post(API_URL, headers=headers, json=payload)

        if response.status_code != 200:
            return jsonify({"error": response.text}), 500

        result = response.json()

        if isinstance(result, list):
            all_results.append(result[0]["generated_text"])
        else:
            all_results.append(str(result))

    final_result = "\n\n".join(all_results)

    return jsonify({"result": final_result})


if __name__ == "__main__":
    app.run()