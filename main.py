from fastapi import FastAPI, Request, HTTPException, Form, Depends, File, UploadFile

from core.database import engine, Base  # Importáld az engine-t és a Base-t
from core.authentication import verify_password, get_user_by_username, create_access_token, decode_jwt
from fastapi.staticfiles import StaticFiles
from core.database import get_db
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
import logging

from core.inserting_data import parse_job_description
from core.job_description_model import JobDescription  # Importáld a JobDescription modellt
from core.cache_logic import preprocess_and_cache

import pdfplumber  # PDF feldolgozás

# Logger beállítása
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI()

# Statikus fájlok kezelése
app.mount("/static", StaticFiles(directory="static"), name="static")

# Modul oldalak kezelése

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Token létrehozása
    access_token = create_access_token(data={"sub": user.username})

    # Sikeres bejelentkezés esetén visszaállítjuk a felhasználót a home oldalra, és beállítjuk a token-t a session-be
    response = RedirectResponse(url="/", status_code=303)  # Átirányítás 303 See Other státuszkóddal
    response.set_cookie(key="access_token", value=access_token)
    return response


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


if __name__ == "__main__":
    import uvicorn
    import os
    from core.database import initialize_database
    initialize_database()
    preprocess_and_cache()  # Ne adj át db-t, mivel a függvény nem vár paramétert
    port = int(os.environ.get("PORT", 8000))  # Heroku-n PORT változó lesz elérhető
    uvicorn.run("main:app", host="localhost", port=port, reload=True)
