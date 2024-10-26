from sqlalchemy.orm import Session
from core.database import SessionLocal, engine
from candidates_models import Candidate, Experience,CandidateIndustryCache
from core.job_description_model import JobDescription, Responsibility, PreferredSkill
from candidates_models import TextVectorCache  # Az új adatbázis táblák importálása
from typing import List, Dict, Optional

from INDUSTRY_KEYWORDS import INDUSTRY_KEYWORDS
import pickle  # A vektorok bináris tárolásához
from concurrent.futures import ThreadPoolExecutor
import openai
import os
import numpy as np
# Az OpenAI API kulcs inicializálása
openai.api_key = os.getenv("OPENAI_API_KEY")
def match_industry_keywords(text: str, db: Session) -> List[str]:
    matched_industries = []
    cleaned_text = text.lower().strip()

    if not cleaned_text:
        return matched_industries

    # Szöveg vektor lekérése cache-ből vagy vektorizáció
    text_vector = get_cached_vector(cleaned_text)

    if np.linalg.norm(text_vector) == 0:
        print("The provided text does not have valid vectors.")
        return matched_industries

    for industry, keywords in INDUSTRY_KEYWORDS.items():
        similarity_scores = []

        for keyword in keywords:
            keyword_clean = keyword.lower().strip()
            # Kulcsszó vektor lekérése
            keyword_vector = get_cached_vector(keyword_clean)

            if np.linalg.norm(keyword_vector) > 0:
                # Koszinusz hasonlóság számítása
                similarity = np.dot(text_vector, keyword_vector) / (np.linalg.norm(text_vector) * np.linalg.norm(keyword_vector))
                similarity_scores.append(similarity)

        if similarity_scores:
            # Átlagos hasonlóság egy iparág számára
            average_similarity = sum(similarity_scores) / len(similarity_scores)

            # Szigorúbb küszöbérték
            if average_similarity > 0.45:
                matched_industries.append(industry)

    return matched_industries

def preprocess_and_cache():
    initialize_industry_keywords_cache()
    def cache_text_vector(text: str, index: int, total: int):
        # Minden szál külön adatbázis kapcsolatot használ
        with SessionLocal() as thread_db:
            try:
                cached = thread_db.query(TextVectorCache).filter_by(text=text).first()
                if not cached:
                    # OpenAI API segítségével vektorizálás
                    response = openai.Embedding.create(
                        input=text,
                        model="text-embedding-ada-002"
                    )
                    vector = response['data'][0]['embedding']

                    # Mentés a cache-be
                    cached_vector = TextVectorCache(
                        text=text,
                        vector=pickle.dumps(vector)
                    )
                    thread_db.add(cached_vector)
                    thread_db.commit()
                    print(f"Vector cached for text [{index}/{total}]: '{text[:30]}...'")
            except Exception as e:
                thread_db.rollback()
                print(f"Error during vector caching for text '{text}': {e}")

    def update_candidate_industry_cache(candidate: Candidate, experiences_text: str, db: Session):
        # Iparági kulcsszavak alapján illeszkedő iparágak keresése
        matched_industries = match_industry_keywords(experiences_text, db)

        if not matched_industries:
            print(f"No industries matched for candidate {candidate.first_name} {candidate.last_name}.")
            return

        for industry in matched_industries:
            # Ellenőrizzük, hogy már nincs-e mentve az iparági adat
            existing_cache = db.query(CandidateIndustryCache).filter_by(candidate_id=candidate.id,
                                                                        industry_name=industry).first()

            if not existing_cache:
                # Új iparági adat mentése
                candidate_industry = CandidateIndustryCache(
                    candidate_id=candidate.id,
                    industry_name=industry
                )
                db.add(candidate_industry)

        # Tranzakció véglegesítése
        db.commit()

    # Összes szöveg gyűjtése, amit vektorizálni kell
    texts_to_cache = []

    # Jelöltek tapasztalatainak gyűjtése
    with SessionLocal() as db:
        print("Collecting candidate experiences...")
        candidates = db.query(Candidate).all()
        for candidate in candidates:
            experiences_text = " ".join(
                [exp.description.lower() for exp in db.query(Experience).filter_by(candidate_id=candidate.id) if
                 exp.description])
            if experiences_text:
                texts_to_cache.append(experiences_text)

                # Iparági egyezések frissítése a jelölt tapasztalatai alapján
                update_candidate_industry_cache(candidate, experiences_text, db)

        # Állásleírások és a kapcsolódó szövegek gyűjtése
        print("Collecting job descriptions...")
        job_descriptions = db.query(JobDescription).all()
        for job in job_descriptions:
            if job.job_title:
                texts_to_cache.append(job.job_title)

            responsibilities = db.query(Responsibility).filter_by(job_description_id=job.id).all()
            for resp in responsibilities:
                if resp.description:
                    texts_to_cache.append(resp.description)

            skills = db.query(PreferredSkill).filter_by(job_description_id=job.id).all()
            for skill in skills:
                if skill.skill_name:
                    texts_to_cache.append(skill.skill_name)

        # Iparági kulcsszavak hozzáadása
        print("Collecting industry keywords...")
        for industry, keywords in INDUSTRY_KEYWORDS.items():
            texts_to_cache.extend(keywords)

    total_texts = len(texts_to_cache)
    print(f"Total texts to cache: {total_texts}")

    # Párhuzamos cache-elés a szövegekhez
    print("Starting preprocessing and caching...")
    with ThreadPoolExecutor(max_workers=20) as executor:
        for index, text in enumerate(texts_to_cache):
            executor.submit(cache_text_vector, text, index + 1, total_texts)

    print("Preprocessing and caching completed.")


def get_cached_vector(text: str):
    # Mindig új adatbázis kapcsolatot hozunk létre a kontextuskezelő használatával
    with SessionLocal() as session:
        try:
            # Ellenőrizzük, hogy a vektor már a cache-ben van-e
            cached = session.query(TextVectorCache).filter_by(text=text).first()
            if cached:
                # Vektor betöltése az adatbázisból
                vector = pickle.loads(cached.vector)
                #print(f"Vector found in cache for text: '{text}'")
                return vector
            else:
                # OpenAI API segítségével vektorizálás
                print(f"Calculating and caching vector for text: '{text}'")
                response = openai.Embedding.create(
                    input=text,
                    model="text-embedding-ada-002"
                )
                vector = response['data'][0]['embedding']

                # Vektor mentése az adatbázisba
                cached_vector = TextVectorCache(
                    text=text,
                    vector=pickle.dumps(vector)
                )
                session.add(cached_vector)
                session.commit()  # Biztosítsuk, hogy a tranzakció befejeződik

                return vector
        except Exception as e:
            session.rollback()  # Ha bármilyen hiba történik, visszagörgetjük a tranzakciót
            print(f"Error during vector caching for text '{text}': {e}")
            raise e
