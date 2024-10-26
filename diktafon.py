import openai
from flask import Flask, render_template, jsonify
import threading
import speech_recognition as sr
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
from flask import Flask, render_template, jsonify
import threading
from live_transcribe import Transcriber

app = Flask(__name__)
recognized_text = ""

def transcribe_audio():
    global recognized_text

    def callback(text):
        global recognized_text
        recognized_text = text
        print(f"Felismert szöveg: {text}")

    # Folyamatos beszédfelismerés a callback függvénnyel
    transcriber = Transcriber(callback=callback, language="hu-HU")
    transcriber.start()  # Elindítjuk a folyamatos felismerést

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_text')
def get_text():
    return jsonify({"text": recognized_text})

if __name__ == "__main__":
    # Beszédfelismerés egy külön szálon
    threading.Thread(target=transcribe_audio, daemon=True).start()
    app.run(debug=True)
