from flask import Flask, render_template, request, jsonify
import PyPDF2
from transformers import pipeline
import re

# app = Flask(__name__)
app = Flask(__name__, static_folder="static", template_folder="templates")
# ==========================================
# تحميل موديل التلخيص
# ==========================================

summarizer = pipeline(
    "summarization",
    model="t5-small",
    tokenizer="t5-small"
)

# ==========================================
# تنظيف النص
# ==========================================

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\n', ' ')
    return text.strip()

# ==========================================
# تقسيم النص الذكي
# ==========================================

def chunk_text(text, chunk_size=900):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            while end < len(text) and text[end] != " ":
                end += 1
        chunks.append(text[start:end])
        start = end
    return chunks

# ==========================================
# بناء البرومبت حسب الوضع المختار
# ==========================================

def build_prompt(text, mode):

    if mode == "summary":
        return f"""
Summarize the following academic text professionally.
Start with a clear definition, explain its importance,
and mention practical or ethical implications.

Text:
{text}
"""

    elif mode == "points":
        return f"""
Extract the key points from the following academic text.
Present them clearly in bullet-style format.

Text:
{text}
"""

    elif mode == "questions":
        return f"""
Generate 10 exam-style questions based on the following text.
Include a mix of short-answer and conceptual questions.

Text:
{text}
"""

    elif mode == "simple":
        return f"""
Explain the following content in simple language suitable for beginners.
Make it easy to understand and avoid technical complexity.

Text:
{text}
"""

    elif mode == "translate":
        return f"""
Translate the following text into English clearly and professionally.

Text:
{text}
"""

    elif mode == "analysis":  # إضافة احترافية
        return f"""
Analyze the following academic text.
Identify its main idea, structure, strengths, weaknesses,
and practical implications.

Text:
{text}
"""

    else:
        return f"Summarize the following text:\n{text}"

# ==========================================
# الصفحة الرئيسية
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")

# ==========================================
# Route التحليل
# ==========================================

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
            return jsonify({"error": "PDF has no readable text"}), 400

    except Exception as e:
        return jsonify({"error": f"PDF read error: {str(e)}"}), 500

    text = clean_text(text)

    chunks = chunk_text(text)

    summaries = []

    # معالجة كل جزء
    for chunk in chunks:
        prompt = build_prompt(chunk, mode)

        summary = summarizer(
            prompt,
            max_length=160,
            min_length=50,
            do_sample=True,
            temperature=0.5,
            top_k=40
        )

        summaries.append(summary[0]["summary_text"])

    merged = " ".join(summaries)

    # تلخيص نهائي إذا كان وضع summary فقط
    if mode == "summary" and len(merged) > 800:
        final_prompt = build_prompt(merged, mode)
        final = summarizer(
            final_prompt,
            max_length=200,
            min_length=80,
            do_sample=True,
            temperature=0.5
        )
        output = final[0]["summary_text"]
    else:
        output = merged

    return jsonify({"result": output})


# if __name__ == "__main__":
#     app.run(debug=True) 

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)