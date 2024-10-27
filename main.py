import json
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Form, Depends, File, UploadFile
from core.authentication import verify_password, get_user_by_username, create_access_token, decode_jwt
from fastapi.staticfiles import StaticFiles
from core.database import get_db, SessionLocal
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
import logging
from core.inserting_data import parse_job_description
from core.job_description_model import JobDescription  # Importáld a JobDescription modellt
from core.getjob import find_best_jobs_for_last_candidate
from core.microphone import transcribe_audio
from core.cache_logic import preprocess_and_cache
import pdfplumber  # PDF feldolgozás
from core.endpoint_logic import templates, handle_file_upload_job_description,handle_file_upload_cv, generate_data
from core.cache_logic import initialize_industry_keywords_cache
# Logger beállítása
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI()

# Statikus fájlok kezelése
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})
# Modul oldalak kezelése
# PDF feldolgozás a dataset mappából
@app.post("/process-dataset")
async def process_dataset(db: Session = Depends(get_db)):
    dataset_path = "dataset/job_descriptions"  # A PDF-eket tartalmazó mappa
    if not os.path.exists(dataset_path):
        raise HTTPException(status_code=404, detail="Dataset mappa nem található")

    # PDF fájlok feldolgozása
    for filename in os.listdir(dataset_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(dataset_path, filename)
            try:
                # PDF fájl olvasása
                with pdfplumber.open(file_path) as pdf:
                    text = "\n".join(page.extract_text() for page in pdf.pages)

                # PDF szöveg elemzése
                sections = parse_job_description(text)

                # Adatok adatbázisba mentése
                job_description = JobDescription(
                    job_title=sections.get("job_title"),
                    company_overview=sections.get("company_overview"),
                    key_responsibilities=sections.get("key_responsibilities"),
                    required_qualifications=sections.get("required_qualifications"),
                    preferred_skills=sections.get("preferred_skills"),
                    benefits=sections.get("benefits")
                )
                db.add(job_description)
                db.commit()
                logger.info(f"Sikeresen feldolgozva: {filename}")
            except Exception as e:
                logger.error(f"Hiba a '{filename}' feldolgozása során: {e}")
                db.rollback()

    return {"message": "Dataset feldolgozása befejeződött"}
@app.post("/upload-pdf-job")
async def upload_pdf_job_pdf(file: UploadFile = File(...)):
    # Meghívjuk a handle_file_upload függvényt az endpoint_logic modulból
    return handle_file_upload_job_description(file)
@app.post("/upload-pdf-cv")
async def upload_pdf_job_cv(file: UploadFile = File(...)):
    # Meghívjuk a handle_file_upload függvényt az endpoint_logic modulból
    return handle_file_upload_cv(file)
@app.get("/get-items")
async def get_items():
    # Meghívjuk a generate_data függvényt, és visszaküldjük az eredményt
    return generate_data()

@app.get("/test")
async def login_get(request: Request):
    return templates.TemplateResponse("test.html", {"request": request})

@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Csak audio fájlokat lehet feltölteni")

    # Audio fájl tartalmának beolvasása
    audio_bytes = await file.read()

    try:
        # OpenAI Whisper feldolgozás
        transcription = await transcribe_audio(audio_bytes)
        return {"transcription": transcription}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nem sikerült feldolgozni a hangfájlt: {str(e)}")

@app.get("/results")
async def results_page(request: Request, param1: Optional[str] = None, param2: Optional[str] = None):
    db = SessionLocal()
    initialize_industry_keywords_cache()
    jobs = find_best_jobs_for_last_candidate(db)
    data = generate_data(jobs, param1, param2)
    return templates.TemplateResponse("results.html", {
        "request": request,
        "name":param1,
        "pos":param2,
        "items": data['items'],
        "best_item_id": data['best_item_id'],
        "best_item_explanation": data['best_item_explanation']
    })
    db.close()
# Végpont a form adatok és fájl fogadására
@app.post("/submit-job")
async def submit_job(
    industry: str = Form(...),
    jobDescription: Optional[str] = Form(None),
    keywords: Optional[str] = Form(None),  # JSON formátumban érkezik
    cv: Optional[UploadFile] = File(None)
):
    try:
        # A JSON-ben érkező kulcsszavak deszerializálása
        keywords_list = json.loads(keywords) if keywords else []

        # Fájl név ellenőrzése (nem olvassuk be a tartalmát)
        if cv:
            cv_filename = cv.filename
            print(f"Fájl neve: {cv_filename}")

        # Logikailag feldolgozhatod az adatokat
        print("Industry:", industry)
        print("Job Description:", jobDescription)
        print("Keywords:", keywords_list)

        # Visszaadunk egy válasz üzenetet
        return {
            "status": "success",
            "industry": industry,
            "jobDescription": jobDescription,
            "keywords": keywords_list,
            "cv_filename": cv_filename if cv else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nem sikerült feldolgozni a kérést: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import os
    from core.database import initialize_database
    initialize_database()
    preprocess_and_cache()
    port = int(os.environ.get("PORT", 8000))  # Heroku-n PORT változó lesz elérhető
    uvicorn.run("main:app", host="localhost", port=port, reload=False)
