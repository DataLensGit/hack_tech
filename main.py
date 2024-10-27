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
from core.matching import process_form_data, find_best_candidates_for_last_job
from core.endpoint_logic import generate_candidate_data
from core.extract_job_info import extract_text_from_pdf, extract_job_info, save_job_description_to_db
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

@app.get("/candidates")
async def results_page(request: Request, param1: Optional[str] = None, param2: Optional[str] = None):
    db = SessionLocal()
    try:
        # Iparági kulcsszavak inicializálása (ha szükséges)
        initialize_industry_keywords_cache()

        # Legjobb jelöltek lekérdezése a legutolsó álláshoz
        candidates = find_best_candidates_for_last_job(db)
        data = generate_candidate_data(candidates, param1, param2)

        return templates.TemplateResponse("results.html", {
            "request": request,
            "name": param1,
            "pos": param2,
            "items": data['items'],
            "best_item_id": data['best_item_id'],
            "best_item_explanation": data['best_item_explanation']
        })
    finally:
        db.close()

@app.get("/dummy_candidates")
async def results_page(request: Request, param1: Optional[str] = None, param2: Optional[str] = None):
    dummy_data = {
        "items": [
            {
                "id": 0,
                "image": "/static/img/sample_image_0.jpg",
                "name": "John Doe",
                "description": "Mihai Vlasceanu azért lenne jó választás az adott állásra, mert magas pontszáma alapján kiemelkedő tudású és tapasztalt szakembernek tekinthető. A pontszám alapján valószínűsíthető, hogy rendelkezik a szükséges készségekkel és ismeretekkel ahhoz, hogy hatékonyan és eredményesen ellássa az állásban foglalt feladatokat. Ezen kívül a magas pontszám azt is jelzi, hogy elkötelezett és ambiciózus személyiség, aki nagy valószínűséggel szorgalmasan és precízen végezné el a rábízott feladatokat.",
                "rating": 9.3
            },
            {
                "id": 1,
                "image": "/static/img/sample_image_1.jpg",
                "name": "Jane Smith",
                "description": "Mihai Vlasceanu azért lenne jó választás az adott állásra, mert magas pontszáma alapján kiemelkedő tudású és tapasztalt szakembernek tekinthető. A pontszám alapján valószínűsíthető, hogy rendelkezik a szükséges készségekkel és ismeretekkel ahhoz, hogy hatékonyan és eredményesen ellássa az állásban foglalt feladatokat. Ezen kívül a magas pontszám azt is jelzi, hogy elkötelezett és ambiciózus személyiség, aki nagy valószínűséggel szorgalmasan és precízen végezné el a rábízott feladatokat.",
                "rating": 9.2
            },
            {
                "id": 2,
                "image": "/static/img/sample_image_2.jpg",
                "name": "Alice Johnson",
                "description": "Mihai Vlasceanu azért lenne jó választás az adott állásra, mert magas pontszáma alapján kiemelkedő tudású és tapasztalt szakembernek tekinthető. A pontszám alapján valószínűsíthető, hogy rendelkezik a szükséges készségekkel és ismeretekkel ahhoz, hogy hatékonyan és eredményesen ellássa az állásban foglalt feladatokat. Ezen kívül a magas pontszám azt is jelzi, hogy elkötelezett és ambiciózus személyiség, aki nagy valószínűséggel szorgalmasan és precízen végezné el a rábízott feladatokat.",
                "rating": 7.7
            },
            {
                "id": 3,
                "image": "/static/img/sample_image_1.jpg",
                "name": "Jane Smith",
                "description": "Mihai Vlasceanu azért lenne jó választás az adott állásra, mert magas pontszáma alapján kiemelkedő tudású és tapasztalt szakembernek tekinthető. A pontszám alapján valószínűsíthető, hogy rendelkezik a szükséges készségekkel és ismeretekkel ahhoz, hogy hatékonyan és eredményesen ellássa az állásban foglalt feladatokat. Ezen kívül a magas pontszám azt is jelzi, hogy elkötelezett és ambiciózus személyiség, aki nagy valószínűséggel szorgalmasan és precízen végezné el a rábízott feladatokat.",
                "rating": 9.2
            },
            {
                "id": 4,
                "image": "/static/img/sample_image_2.jpg",
                "name": "Alice Johnson",
                "description": "Mihai Vlasceanu azért lenne jó választás az adott állásra, mert magas pontszáma alapján kiemelkedő tudású és tapasztalt szakembernek tekinthető. A pontszám alapján valószínűsíthető, hogy rendelkezik a szükséges készségekkel és ismeretekkel ahhoz, hogy hatékonyan és eredményesen ellássa az állásban foglalt feladatokat. Ezen kívül a magas pontszám azt is jelzi, hogy elkötelezett és ambiciózus személyiség, aki nagy valószínűséggel szorgalmasan és precízen végezné el a rábízott feladatokat.",
                "rating": 7.7
            }
        ],
        "best_item_id": 0,
        "best_item_explanation": " A magas pontszám alapján Andrei egy megbízható és elkötelezett munkavállaló lenne az adott pozícióban. alapján lett kiválasztva.Raluca Mihai Dumitrescu"
    }

    return templates.TemplateResponse("results.html", {
        "request": request,
        "name": param1,
        "pos": param2,
        "items": dummy_data["items"],
        "best_item_id": dummy_data["best_item_id"],
        "best_item_explanation": dummy_data["best_item_explanation"]
    })


# Végpont a form adatok és fájl fogadására
@app.post("/submit-job")
async def submit_job(
    industry: str = Form(...),
    jobDescription: Optional[str] = Form(None),
    keywords: Optional[str] = Form(None),  # JSON formátumban érkezik
    cv: Optional[UploadFile] = File(None)
):
    db = SessionLocal()
    print(cv)
    try:
        # A JSON-ben érkező kulcsszavak deszerializálása
        keywords_list = json.loads(keywords) if keywords else []

        # Ellenőrzés, hogy szöveges input vagy PDF fájl érkezett
        if cv and cv.filename.endswith(".pdf"):
            # PDF fájl feldolgozása
            pdf_path = f"/tmp/{cv.filename}"  # Ideiglenes helyre mentjük a fájlt
            with open(pdf_path, "wb") as buffer:
                buffer.write(await cv.read())

            # PDF szöveg kinyerése
            job_text = extract_text_from_pdf(pdf_path)
            if not job_text:
                raise HTTPException(status_code=400, detail="Nem sikerült kinyerni a szöveget a PDF fájlból.")
        elif jobDescription:
            # Szöveges leírás esetén közvetlenül használjuk
            job_text = jobDescription
        else:
            raise HTTPException(status_code=400, detail="Nincs érvényes állásleírás vagy PDF fájl.")

        # Job adatok kinyerése a szövegből
        extracted_info = extract_job_info(job_text)
        if not extracted_info:
            raise HTTPException(status_code=500, detail="Nem sikerült kinyerni az adatokat a leírásból.")

        # Adatok mentése az adatbázisba
        new_job = save_job_description_to_db(extracted_info, db)

        # Visszaadunk egy válasz üzenetet
        return {
            "status": "success",
            "job_id": new_job.id,
            "industry": industry,
            "jobDescription": jobDescription if jobDescription else "PDF alapján",
            "keywords": keywords_list,
            "cv_filename": cv.filename if cv else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nem sikerült feldolgozni a kérést: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    import os
    from core.database import initialize_database
    initialize_database()
    #preprocess_and_cache()
    port = int(os.environ.get("PORT", 3000))  # Heroku-n PORT változó lesz elérhető
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
