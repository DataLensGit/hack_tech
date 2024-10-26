from fastapi import FastAPI, Request, HTTPException, Form, Depends, UploadFile, File, WebSocket
import os
from core.endpoint_logic import load_all_avaliable_modules, load_module, templates, handle_file_upload, generate_data
from core.microphone import transcribe_audio
from addons.sample_module.controllers import router as sample_module_router
from core.database import engine, Base  # Importáld az engine-t és a Base-t
from core.authentication import verify_password, get_user_by_username, create_access_token, decode_jwt
from fastapi.staticfiles import StaticFiles
from core.database import get_db
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
import logging
from typing import Optional
from typing import List
from pydantic import BaseModel
import json


# Logger beállítása
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adatbázis táblák létrehozása (ha még nem léteznek)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("A táblák létrehozása sikeresen megtörtént.")
except Exception as e:
    logger.error(f"Hiba a táblák létrehozásakor: {e}")

app = FastAPI()

# Statikus fájlok kezelése
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/static/js", StaticFiles(directory="static/js"), name="js")

app.include_router(sample_module_router, prefix="/sample_module")

# Jinja2 szűrő hozzáadása a FastAPI alkalmazáshoz
templates.env.filters['decode_jwt'] = decode_jwt

# Kezdőoldal: modulok listázása
@app.get("/")
def home(request: Request):
    return load_all_avaliable_modules(request)

# Modul oldalak kezelése
@app.get("/modules/{module_name}")
def get_module(module_name: str, request: Request):
    return load_module(module_name, request)

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

@app.get("/login")
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

#Saját végpontok kezelése
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    # Meghívjuk a handle_file_upload függvényt az endpoint_logic modulból
    return handle_file_upload(file)

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
    data = generate_data(param1, param2)
    return templates.TemplateResponse("results.html", {
        "request": request,
        "name":param1,
        "pos":param2,
        "items": data['items'],
        "best_item_id": data['best_item_id'],
        "best_item_explanation": data['best_item_explanation']
    })


class Keyword(BaseModel):
    skill: str
    weight: int

class JobSubmission(BaseModel):
    industry: str
    jobDescription: Optional[str] = None
    keywords: List[Keyword] = []

# Végpont a form adatok és fájl fogadására

class Keyword(BaseModel):
    skill: str
    weight: int

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

    port = int(os.environ.get("PORT", 8000))  # Heroku-n PORT változó lesz elérhető
    uvicorn.run("main:app", host="localhost", port=port, reload=True)
