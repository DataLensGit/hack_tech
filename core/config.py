import os
from dotenv import load_dotenv

# Betöltjük a környezeti változókat a .env fájlból
load_dotenv()

class Settings:
    PROJECT_NAME: str = "My Modular Project"
    PROJECT_VERSION: str = "1.0.0"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")  # Alapértelmezett SQLite adatbázis
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == 'true'

    API_VERSION: str = os.getenv("API_VERSION", "/api/v1")

    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    # JWT token élettartama (percekben)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


settings = Settings()
