from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os


# PostgreSQL adatbázis elérési út az .env fájlból
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://testuser:ls47zGNb/3w07KvPC3sYEA==@server.datalensglobal.com/hacktech")

# Adatbázis motor létrehozása
try:
    print(f"Kapcsolódás az adatbázishoz: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL,
                                    pool_size=10,  # Alapértelmezett érték: 5
                                    max_overflow=20,  # Alapértelmezett érték: 10
                                    pool_timeout=60,  # A kapcsolat várakozási ideje másodpercben
                                                        )
    print("Sikeresen létrehoztuk az adatbázis motort.")
except Exception as e:
    print(f"Hiba az adatbázis motor létrehozásakor: {e}")
    raise  # A kivétel további kezelése érdekében

# Session local létrehozása
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Alapmodell létrehozása
Base = declarative_base()

# Adatbázis kapcsolat kezelése függvényként
def get_db():
    db = SessionLocal()
    try:
        print("Új adatbázis kapcsolat létrehozva.")
        yield db
    finally:
        db.close()
        print("Az adatbázis kapcsolat bezárva.")

# Esetleg: Adatbázis inicializálás (például ha szükséges)
def initialize_database():
    """
    A táblák létrehozása az adatbázisban
    """
    Base.metadata.create_all(bind=engine)
    print("Táblák sikeresen létrehozva.")
if __name__ == "__main__":
    # Ha ez a fájl közvetlenül fut, inicializálj mindent
    initialize_database()
