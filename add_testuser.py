from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base, get_db
from core.authentication import get_password_hash,User

# PostgreSQL adatbázis elérési út az .env fájlból
DATABASE_URL = "postgresql://postgres:1234@localhost/test_database"

# Adatbázis motor létrehozása
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Tesztfelhasználó létrehozása
def create_test_user():
    db = SessionLocal()
    try:
        # Jelszó hash-elése
        hashed_password = get_password_hash("1234")

        # Tesztfelhasználó létrehozása
        test_user = User(username="testuser2", email="testuser2@example.com", hashed_password=hashed_password)

        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        print("Tesztfelhasználó sikeresen létrehozva:", test_user.username)
    except Exception as e:
        print(f"Hiba a tesztfelhasználó létrehozásakor: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_test_user()
