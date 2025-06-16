from flask import Flask, request, render_template
import pytesseract
from PIL import Image
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import which
import os
import tempfile

# ✅ Path to your ffmpeg.exe
AudioSegment.converter = r"C:\ffmeg\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        text = request.form.get("input_text", "")

        # Handle text file
        if 'text_file' in request.files:
            f = request.files['text_file']
            if f.filename:
                text += "\n" + f.read().decode("utf-8")

        # Handle image file (OCR)
        if 'image_file' in request.files:
            img_file = request.files['image_file']
            if img_file.filename:
                img = Image.open(img_file)
                text += "\n" + pytesseract.image_to_string(img)

        # Handle audio file (convert to wav and transcribe)
        if 'audio_file' in request.files:
            audio_file = request.files['audio_file']
            if audio_file.filename:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
                        sound = AudioSegment.from_file(audio_file)
                        sound.export(temp_wav.name, format="wav")

                        recognizer = sr.Recognizer()
                        with sr.AudioFile(temp_wav.name) as source:
                            audio_data = recognizer.record(source)
                            text += "\n" + recognizer.recognize_google(audio_data)

                    os.remove(temp_wav.name)
                except Exception as e:
                    text += f"\n[Audio Error: {str(e)}]"

        # Clean and combine all input
        items = []
        for line in text.splitlines():
            items.extend([i.strip() for i in line.split(",") if i.strip()])

        sort_order = request.form.get("sort_order", "asc")
        reverse = sort_order == "desc"

        # Detect if all items are numeric
        def is_number(s):
            try:
                float(s)
                return True
            except ValueError:
                return False

        if all(is_number(item) for item in items):
            sorted_items = sorted(items, key=lambda x: float(x), reverse=reverse)
        else:
            sorted_items = sorted(items, key=str.lower, reverse=reverse)

        result = ", ".join(sorted_items)

    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
