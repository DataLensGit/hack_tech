import os
import json
import importlib
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException, UploadFile, File
from core.extract_job_info import process_single_job_description as job_pdf
from core.extract_cv_info import process_single_cv as cv_pdf
from core.database import engine
from core.getjob import find_best_jobs_for_last_candidate
import sys
import random
from typing import List, Dict, Optional

# Templating rendszer (Jinja2)
templates = Jinja2Templates(directory="templates")

import openai

# Funkció az ajánlás generálásához a jelölt adatai alapján
def generate_suggestion_for_candidate(candidate: Dict) -> str:
    """
    Meghívja a ChatGPT API-t, hogy egy rövid ajánlást adjon a jelöltről.

    Args:
        candidate (Dict): A jelölt adatai.

    Returns:
        str: A ChatGPT által generált rövid ajánlás.
    """
    prompt = f"""
    Here is a candidate's name and score below. Write 2-3 sentences summarizing why the candidate would be a good fit for the given position.

    Name:
    {candidate['first_name']} {candidate['last_name']}

    Score:
    {candidate['score']}

    Short recommenditation:
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        # Az API válaszának feldolgozása
        if response and 'choices' in response and len(response['choices']) > 0:
            suggestion = response['choices'][0]['message']['content'].strip()
            return suggestion
        else:
            return "Nem sikerült megfelelő választ generálni."

    except Exception as e:
        print(f"Error during API call: {e}")
        return "Hiba történt a javaslat generálása során."

# Jelölt adatok generálása a visszaküldéshez
def generate_candidate_data(candidates: List[Dict], param1: Optional[str] = None, param2: Optional[str] = None) -> Dict:
    items = []
    best_item_id = None
    best_score = 0

    for i, candidate in enumerate(candidates):
        # Rövid ajánlás generálása
        suggestion = generate_suggestion_for_candidate(candidate)

        item = {
            "id": i,
            "image": f"/static/img/sample_image_{i}.jpg",  # Ha van kép azonosítója, cseréld ki erre
            "name": f"{candidate['first_name']} {candidate['last_name']}",
            "description": f"Score: {candidate['score']:.1f}\nRecommendation: {suggestion}",
            "rating": round(candidate['score'], 1)  # Pontszám egy tizedesjegyre kerekítve
        }
        items.append(item)

        # A legjobb jelölt kiválasztása
        if candidate['score'] > best_score:
            best_score = candidate['score']
            best_item_id = i

    # Magyarázat a legjobb jelölt kiválasztására
    best_item_explanation = f"The best canditate is {items[best_item_id]['name']} {items[best_item_id]['description']} " if best_item_id is not None else "No best candidate"

    return {
        "items": items,
        "best_item_id": best_item_id,
        "best_item_explanation": best_item_explanation
    }
def generate_data(jobs, param1=None, param2=None):
    # 5 objektum létrehozása, mindegyik tartalmaz képet, nevet, leírást és értékelést
    items = []
    for i in range(len(jobs)):
        job = jobs[i]  # Hivatkozunk az aktuális állás objektumra
        item = {
            "id": i,
            "image": f"/static/img/sample_image_{i}.jpg",
            "name": job["job_title"],  # Az állás nevére hivatkozunk
            "description": job["suggestion"],
            "rating": round(float(job["score"]), 1)  # Az állás pontszámára hivatkozunk, float típusra konvertálva
        }
        items.append(item)

    # A legjobb értékelésű elem kiválasztása
    best_item = max(items, key=lambda x: x["rating"])
    best_item_id = best_item["id"]
    best_item_explanation = f"The best position is {best_item['name']} with a rating of {best_item['rating']}."

    return {
        "items": items,
        "best_item_id": best_item_id,
        "best_item_explanation": best_item_explanation
    }

    # Egy elem kiválasztása a legjobbnak
    best_item = max(items, key=lambda x: x['rating'])
    best_item["explanation"] = f"This is why this position {best_item['id']} is considered the best."

    return {
        "items": items,
        "best_item_id": best_item['id'],
        "best_item_explanation": best_item['explanation']
    }

def handle_file_upload_job_description(file: UploadFile):
    # Ellenőrizzük, hogy a fájl PDF típusú-e
    print("Belépett")
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Csak PDF fájlokat lehet feltölteni")

    # PDF fájl mentése a "documents" mappába
    save_path = os.path.join("documents", file.filename)
    with open(save_path, "wb") as buffer:
        buffer.write(file.file.read())
    job_pdf(save_path)
    return {"message": "Fájl sikeresen feltöltve", "filename": file.filename}


def handle_file_upload_cv(file: UploadFile):
    # Ellenőrizzük, hogy a fájl PDF típusú-e
    print("Belépett")
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Csak PDF fájlokat lehet feltölteni")

    # Létrehozzuk a "documents" mappát, ha nem létezik
    documents_dir = "documents"
    os.makedirs(documents_dir, exist_ok=True)  # Ez létrehozza a könyvtárat, ha még nem létezik

    # PDF fájl mentése a "documents" mappába
    save_path = os.path.join(documents_dir, file.filename)
    with open(save_path, "wb") as buffer:
        buffer.write(file.file.read())

    # A fájl feldolgozása a megfelelő függvény meghívásával
    cv_pdf(file.filename, documents_dir)

    return {"message": "Fájl sikeresen feltöltve", "filename": file.filename}

if __name__ == "__main__":
    pass