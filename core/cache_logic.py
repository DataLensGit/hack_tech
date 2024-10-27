from sqlalchemy.orm import Session
from core.database import SessionLocal
from core.candidates_models import Candidate, Experience, CandidateIndustryCache, TextVectorCache
from core.job_description_model import JobDescription, Responsibility, PreferredSkill
from typing import List
from core.INDUSTRY_KEYWORDS import INDUSTRY_KEYWORDS
import pickle
from concurrent.futures import ThreadPoolExecutor
import openai
import os
import numpy as np

# Az OpenAI API kulcs inicializálása
openai.api_key = os.getenv("OPENAI_API_KEY")


def initialize_industry_keywords_cache():
    """Pre-cache all industry keywords during system initialization"""
    print("Initializing industry keywords cache...")

    with SessionLocal() as session:
        for industry, keywords in INDUSTRY_KEYWORDS.items():
            for keyword in keywords:
                try:
                    # Check if keyword is already cached
                    existing_cache = session.query(TextVectorCache).filter_by(text=keyword.lower().strip()).first()

                    if not existing_cache:
                        # Calculate and cache vector for uncached keyword
                        vector = get_cached_vector(keyword.lower().strip())
                        print(f"Cached vector for industry keyword: {keyword}")

                except Exception as e:
                    print(f"Error caching industry keyword '{keyword}': {e}")
                    continue

    print("Industry keywords cache initialization completed")
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
        with SessionLocal() as thread_db:
            try:
                cached = thread_db.query(TextVectorCache).filter_by(text=text).first()
                if not cached:
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
        matched_industries = match_industry_keywords(experiences_text, db)

        if not matched_industries:
            print(f"No industries matched for candidate {candidate.first_name} {candidate.last_name}.")
            return

        # Már meglévő iparági adatok egyszerre lekérdezése
        existing_industries = db.query(CandidateIndustryCache.industry_name).filter_by(candidate_id=candidate.id).all()
        existing_industry_names = {entry.industry_name for entry in existing_industries}

        # Új iparági adatok előkészítése
        new_industries = [
            CandidateIndustryCache(candidate_id=candidate.id, industry_name=industry)
            for industry in matched_industries if industry not in existing_industry_names
        ]

        if new_industries:
            # Bulk save egyszerre több objektum mentése
            db.bulk_save_objects(new_industries)
            db.commit()
            print(f"Updated industries for candidate {candidate.first_name} {candidate.last_name}.")

    texts_to_cache = []

    with SessionLocal() as db:
        print("Collecting candidate experiences...")
        candidates = db.query(Candidate).all()

        def process_candidate(candidate):
            experiences_text = " ".join(
                [exp.description.lower() for exp in db.query(Experience).filter_by(candidate_id=candidate.id) if exp.description]
            )
            if experiences_text:
                texts_to_cache.append(experiences_text)
                update_candidate_industry_cache(candidate, experiences_text, db)

        # Párhuzamos feldolgozás jelöltekkel
        with ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(process_candidate, candidates)

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

        print("Collecting industry keywords...")
        for industry, keywords in INDUSTRY_KEYWORDS.items():
            texts_to_cache.extend(keywords)

    total_texts = len(texts_to_cache)
    print(f"Total texts to cache: {total_texts}")

    print("Starting preprocessing and caching...")
    with ThreadPoolExecutor(max_workers=20) as executor:
        for index, text in enumerate(texts_to_cache):
            executor.submit(cache_text_vector, text, index + 1, total_texts)

    print("Preprocessing and caching completed.")


def get_cached_vector(text: str):
    with SessionLocal() as session:
        try:
            cached = session.query(TextVectorCache).filter_by(text=text).first()
            if cached:
                vector = pickle.loads(cached.vector)
                return vector
            else:
                print(f"Calculating and caching vector for text: '{text}'")
                response = openai.Embedding.create(
                    input=text,
                    model="text-embedding-ada-002"
                )
                vector = response['data'][0]['embedding']

                cached_vector = TextVectorCache(
                    text=text,
                    vector=pickle.dumps(vector)
                )
                session.add(cached_vector)
                session.commit()
                return vector
        except Exception as e:
            session.rollback()
            print(f"Error during vector caching for text '{text}': {e}")
            raise e
