from typing import List, Dict
from sqlalchemy.orm import Session
from core.database import SessionLocal
from core.candidates_models import Candidate
from core.job_description_model import JobDescription
import openai
from core.cache_logic import get_cached_vector, preprocess_and_cache
from concurrent.futures import ThreadPoolExecutor
from core.matching import (
    calculate_industry_score_cached,
    calculate_job_matching_score,
    calculate_technical_skills_score_cached
)
import heapq
import os
openai.api_key = os.getenv("OPENAI_API_KEY")
# Súlyok a pontszámításhoz
INDUSTRY_KNOWLEDGE_WEIGHT = 0.10
TECHNICAL_SKILLS_WEIGHT = 0.30
JOB_MATCHING_WEIGHT = 0.60

# Pontszámok kiszámítása és mentése
def calculate_and_save_final_score(candidate: Candidate, job_description: JobDescription, db: Session) -> float:
    try:
        # Industry, technical skills és job matching score kiszámítása
        industry_score = calculate_industry_score_cached(candidate, job_description, db)
        technical_score = calculate_technical_skills_score_cached(candidate, job_description, db=db)
        job_matching_score = calculate_job_matching_score(candidate, job_description, db)

        # Final score számítása
        final_score = (
            (industry_score * INDUSTRY_KNOWLEDGE_WEIGHT) +
            (technical_score * TECHNICAL_SKILLS_WEIGHT) +
            (job_matching_score * JOB_MATCHING_WEIGHT)
        )

        return final_score
    except Exception as e:
        print(f"Error during score calculation for job {job_description.job_title}: {e}")
        return 0.0

# A jelölt számára legjobb állások kiválasztása
def get_best_jobs_for_candidate(candidate: Candidate, db: Session, top_n: int = 5) -> List[Dict]:
    # Minden állást lekérdezünk az adatbázisból
    jobs = db.query(JobDescription).all()
    scores = []

    print(f"\n=== Ranking Jobs for Candidate: {candidate.first_name} {candidate.last_name} ===")

    def get_score_and_suggestion_for_job(job):
        try:
            # Minden szálnak új adatbázis kapcsolatot hozunk létre
            with SessionLocal() as thread_db:
                score = calculate_and_save_final_score(candidate, job, thread_db)

                # Jelölt életrajz szövegének összegyűjtése
                cv_text = " ".join([exp.description for exp in candidate.experiences if exp.description])

                # Generálunk egy javaslatot a ChatGPT API segítségével
                job_description_text = job.get_full_job_description()  # Javítás itt
                suggestion = generate_suggestion(cv_text=cv_text, job_description=job_description_text)

                return {
                    "job": job,
                    "score": score,
                    "suggestion": suggestion
                }
        except Exception as e:
            print(f"Hiba történt az állás {job.job_title} pontszámításakor: {e}")
            return {
                "job": job,
                "score": 0.0,
                "suggestion": "Nincs javaslat elérhető."
            }

    # Többszálas feldolgozás az állásokhoz
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(get_score_and_suggestion_for_job, jobs))

    # Rendezés pontszám alapján, és a top_n legjobb állás kiválasztása
    top_jobs = heapq.nlargest(top_n, results, key=lambda x: x["score"])

    return [
        {
            "job_id": job["job"].id,
            "job_title": job["job"].job_title,
            "score": job["score"],
            "suggestion": job["suggestion"]  # A generált javaslat
        }
        for job in top_jobs
    ]

def generate_suggestion(cv_text: str, job_description: str) -> str:
    """
    Meghívja a ChatGPT API-t, hogy egy rövid, 2-3 mondatos javaslatot adjon arra, miért lenne jó az adott állás a jelölt számára.

    Args:
        cv_text (str): A jelölt életrajza.
        job_description (str): Az állás leírása.

    Returns:
        str: A ChatGPT által generált rövid összefoglaló.
    """
    prompt = f"""
    Az alábbiakban található egy állás leírás és egy jelölt életrajza. Írj 2-3 mondatot, amelyben összefoglalod, hogy a jelölt miért lenne jó választás erre az állásra.

    Állás Leírás:
    {job_description}

    Jelölt Életrajz:
    {cv_text}

    Rövid javaslat (2-3 mondatban):
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        # Az API válaszának feldolgozása
        if response and 'choices' in response and len(response['choices']) > 0:
            suggestion = response['choices'][0]['message']['content'].strip()
            return suggestion
        else:
            return "Nem sikerült megfelelő választ generálni."

    except Exception as e:
        print(f"Error during API call: {e}")
        return "Hiba történt a javaslat generálása során."
def find_best_jobs_for_last_candidate(db: Session, top_n: int = 5) -> List[Dict]:
    # Lekérdezzük az utolsó hozzáadott jelöltet az adatbázisból
    last_candidate = db.query(Candidate).order_by(Candidate.id.desc()).first()

    if not last_candidate:
        print("Nincs jelölt az adatbázisban.")
        return []

    print(f"\n=== Finding Best Jobs for Last Candidate: {last_candidate.first_name} {last_candidate.last_name} ===")

    # Legjobb állások keresése a jelölt számára
    best_jobs = get_best_jobs_for_candidate(last_candidate, db, top_n=top_n)

    print("\n--- Legjobb Állások ---\n")
    for job in best_jobs:
        print(job)

    return best_jobs

# Fő folyamat indítása
if __name__ == "__main__":
    preprocess_and_cache()
    while True:
        db = SessionLocal()

        try:
            # Felhasználótól kérünk egy jelöltazonosítót
            candidate_id = input("Add meg a jelölt azonosítóját (vagy 'exit' a kilépéshez): ")

            # Kilépési feltétel
            if candidate_id.lower() == 'exit':
                break

            try:
                candidate_id = int(candidate_id)
            except ValueError:
                print("Érvénytelen jelöltazonosító. Próbáld újra.")
                continue

            # Keresünk egy jelöltet a megadott azonosítóval
            candidate = db.query(Candidate).filter_by(id=candidate_id).first()

            if candidate:
                # Legjobb állások keresése a jelölt számára
                best_jobs = get_best_jobs_for_candidate(candidate, db)

                print("\n--- Legjobb Állások ---\n")
                for job in best_jobs:
                    print(job)
            else:
                print(f"Nincs találat a {candidate_id} azonosítójú jelölthöz.")

        finally:
            db.close()

if __name__ == "__Main__":
    pass
