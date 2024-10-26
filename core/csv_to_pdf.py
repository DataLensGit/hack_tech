import pandas as pd
from core.database import SessionLocal
from job_description_model import JobDescription, Responsibility, Qualification  # Importáljuk a szükséges modelleket


# CSV betöltése pandas segítségével
def load_csv_to_database(csv_file_path: str):
    # CSV adatainak betöltése pandas DataFrame-be
    df = pd.read_csv(csv_file_path)

    # Adatbázis kapcsolat létrehozása
    db = SessionLocal()

    # Feldolgozzuk a CSV sorait és feltöltjük az adatbázisba
    for index, row in df.iterrows():
        # Új JobDescription objektum létrehozása
        job_description = JobDescription(
            job_title=row.get('Title'),
            company_overview="",  # Ha nincs külön megadva, üres marad
        )

        # Responsibilities hozzáadása
        responsibilities_list = str(row.get('Responsibilities', '')).split(';')
        for responsibility in responsibilities_list:
            if responsibility.strip():
                job_description.responsibilities.append(
                    Responsibility(description=responsibility.strip())
                )

        # Minimum Qualifications hozzáadása
        min_qualifications_list = str(row.get('Minimum Qualifications', '')).split(';')
        for qualification in min_qualifications_list:
            if qualification.strip():
                job_description.qualifications.append(
                    Qualification(description=qualification.strip())
                )

        # Preferred Qualifications hozzáadása
        pref_qualifications_list = str(row.get('Preferred Qualifications', '')).split(';')
        for qualification in pref_qualifications_list:
            if qualification.strip():
                job_description.qualifications.append(
                    Qualification(description=qualification.strip())
                )

        # Az új rekord hozzáadása az adatbázishoz
        db.add(job_description)

    # Módosítások mentése az adatbázisban
    db.commit()
    print("CSV data has been successfully loaded into the database.")

    # Adatbázis kapcsolat lezárása
    db.close()


# Használat példa
if __name__ == "__main__":
    csv_file_path = "../dataset/job_skills.csv"  # A CSV fájl útvonala
    load_csv_to_database(csv_file_path)
