from sqlalchemy import MetaData
from core.database import engine
from add_testuser import create_test_user

def drop_all_tables():
    # MetaData objektum az összes tábla lekérdezéséhez
    metadata = MetaData()
    metadata.reflect(bind=engine)  # Összes tábla betöltése

    # Táblák törlése
    metadata.drop_all(bind=engine)
    print("Minden tábla sikeresen törölve.")

if __name__ == "__main__":
    drop_all_tables()
