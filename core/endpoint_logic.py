import os
import json
import importlib
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException, UploadFile, File
from core.extract_job_info import extract_text_from_pdf as job_pdf
from core.extract_cv_info import extract_text_from_pdf as cv_pdf
from core.database import engine
import sys
import random
from typing import List
# Templating rendszer (Jinja2)
templates = Jinja2Templates(directory="templates")



def generate_data(param1=None, param2=None):
    # 5 objektum létrehozása, mindegyik tartalmaz képet, nevet, leírást és értékelést
    items = []
    for i in range(1, 6):
        item = {
            "id": i,
            "image": f"/static/img/sample_image_{i}.jpg",
            "name": f"Item {i}",
            "description": f"This is a description for item {i}.",
            "rating": int(random.uniform(1, 100))
        }
        items.append(item)

    # Egy elem kiválasztása a legjobbnak
    best_item = max(items, key=lambda x: x['rating'])
    best_item["explanation"] = f"This is why item {best_item['id']} is considered the best."

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

    # PDF fájl mentése a "documents" mappába
    save_path = os.path.join("documents", file.filename)
    with open(save_path, "wb") as buffer:
        buffer.write(file.file.read())
    cv_pdf(save_path)
    return {"message": "Fájl sikeresen feltöltve", "filename": file.filename}


if __name__ == "__main__":
    pass