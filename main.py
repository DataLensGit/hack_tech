from fastapi import FastAPI, Request, HTTPException, Form, Depends
from core.endpoint_logic import load_all_avaliable_modules, load_module, templates
from addons.sample_module.controllers import router as sample_module_router
from core.database import engine, Base  # Importáld az engine-t és a Base-t
from core.authentication import verify_password, get_user_by_username, create_access_token, decode_jwt
from fastapi.staticfiles import StaticFiles
from core.database import get_db
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
import logging


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

if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 8000))  # Heroku-n PORT változó lesz elérhető
    uvicorn.run("main:app", host="localhost", port=port, reload=True)
