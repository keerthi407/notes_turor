from flask import Flask, render_template, request, redirect, url_for
import PyPDF2
import textstat
import os
import random

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

global_quiz = []

def generate_quiz(sentences):
    quiz = []
    words_pool = []

    for s in sentences:
        words_pool.extend(s.split())

    for s in sentences[:5]:
        words = s.split()
        if len(words) > 5:
            answer = random.choice(words)
            question = s.replace(answer, "_____")

            options = random.sample(words_pool, min(3, len(words_pool)))
            if answer not in options:
                options.append(answer)

            random.shuffle(options)

            quiz.append({
                "question": question,
                "answer": answer,
                "options": options
            })

    return quiz


@app.route("/", methods=["GET", "POST"])
def index():
    global global_quiz

    if request.method == "POST":
        file = request.files.get("pdf")
        if not file:
            return "No file selected"

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        reader = PyPDF2.PdfReader(filepath)
        text = ""

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

        if not text.strip():
            return "PDF has no readable text"

        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 30]

        analyzed = []
        for s in sentences:
            score = textstat.flesch_reading_ease(s)

            if score > 60:
                level = "easy"
            elif score > 30:
                level = "medium"
            else:
                level = "hard"

            analyzed.append((s, level))

        global_quiz = generate_quiz(sentences)

        return render_template("result.html", data=analyzed)

    return render_template("index.html")


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    global global_quiz

    if request.method == "POST":
        score = 0

        for i, q in enumerate(global_quiz):
            selected = request.form.get(f"q{i}")
            if selected == q["answer"]:
                score += 1

        return render_template("score.html", score=score, total=len(global_quiz))

    return render_template("quiz.html", quiz=global_quiz)


# 🔥 IMPORTANT FIX FOR RENDER + PHONE ACCESS
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
