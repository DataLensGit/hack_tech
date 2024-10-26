import openai
import os
import io
from fastapi import HTTPException

# OpenAI API kulcs betöltése
openai.api_key = os.getenv("OPENAI_API_KEY")

# Audio fájl feldolgozása az OpenAI Whisper segítségével
async def transcribe_audio(audio_bytes):
    try:
        # Fájl létrehozása BytesIO segítségével
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "recording.wav"  # Adjunk neki egy nevet

        # Whisper API hívása a szövegfeldolgozáshoz
        response = openai.Audio.transcribe("whisper-1", audio_file)
        return response.get("text", "Nincs eredmény")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nem sikerült feldolgozni a hangfájlt: {str(e)}")
