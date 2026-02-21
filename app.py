from flask import Flask, render_template, request, jsonify
import os
import re
import whisper
from transformers import pipeline

# ---------------- APP SETUP ----------------
app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- LOAD MODELS ----------------
speech_model = whisper.load_model("tiny")  # fast transcription

summarizer = pipeline(
    "summarization",
    model="sshleifer/distilbart-cnn-12-6",
    device=-1  # CPU
)

# ---------------- TEXT CLEANING ----------------
def clean_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9., ]", "", text)
    fillers = ["uh", "um", "hmm", "ah", "eh"]
    for f in fillers:
        text = re.sub(rf"\b{f}\b", "", text)
    return text.strip()

def normalize_for_ai(text):
    sentences = text.split(". ")
    cleaned = []
    for s in sentences:
        if len(s.split()) > 5:
            cleaned.append(s.capitalize())
    return ". ".join(cleaned)

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------- AUDIO UPLOAD ----------------
@app.route("/upload", methods=["POST"])
def upload_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file"}), 400

    audio = request.files["audio"]
    if audio.filename == "":
        return jsonify({"error": "Empty file"}), 400

    path = os.path.join(UPLOAD_FOLDER, audio.filename)
    audio.save(path)

    try:
        result = speech_model.transcribe(path)
        raw_text = result.get("text", "")
        cleaned = clean_text(raw_text)
    except Exception as e:
        return jsonify({"error": "Transcription failed"}), 500
    finally:
        if os.path.exists(path):
            os.remove(path)

    return jsonify({"transcript": cleaned})

# ---------------- SUMMARY ----------------
@app.route("/summarize", methods=["POST"])
def summarize():
    text = request.json.get("text", "").strip()
    if len(text.split()) < 40:
        return jsonify({"summary": "Audio content is too short to summarize."})

    prepared = normalize_for_ai(text)[:1000]
    summary = summarizer(prepared, max_length=90, min_length=50, do_sample=False)[0]["summary_text"]
    summary = re.sub(r"\b(i|we|my|our)\b", "the speaker", summary, flags=re.I)
    return jsonify({"summary": summary})

# ---------------- KEY POINTS ----------------
@app.route("/keywords", methods=["POST"])
def keywords():
    text = request.json.get("text", "").strip()
    if len(text.split()) < 40:
        return jsonify({"keywords": []})

    prepared = normalize_for_ai(text)[:1000]
    summary = summarizer(prepared, max_length=120, min_length=70, do_sample=False)[0]["summary_text"]

    points = []
    for s in summary.split(". "):
        if len(s.split()) > 6:
            points.append(s.capitalize())
    return jsonify({"keywords": points[:5]})

# ---------------- FLASHCARDS ----------------
@app.route("/flashcards", methods=["POST"])
def flashcards():
    text = request.json.get("text", "").strip()
    if len(text.split()) < 40:
        return jsonify({"flashcards": []})

    prepared = normalize_for_ai(text)[:1000]
    summary = summarizer(prepared, max_length=130, min_length=80, do_sample=False)[0]["summary_text"]

    cards = []
    for s in summary.split(". "):
        words = s.split()
        if len(words) > 8:
            title = " ".join(words[:3]).capitalize()
            explanation = " ".join(words[3:]).capitalize()
            cards.append({"title": title, "content": explanation})

    return jsonify({"flashcards": cards[:5]})

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
