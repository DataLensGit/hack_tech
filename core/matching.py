import numpy as np
from typing import List, Dict
from sqlalchemy.orm import Session
from core.database import SessionLocal, engine
from candidates_models import Candidate, Experience, Skill
from job_description_model import JobDescription, Responsibility, Qualification, PreferredSkill, IndustryField
from cache_model import TextVectorCache, CandidateJobScore, CandidateIndustryCache  # Az új adatbázis táblák importálása
from INDUSTRY_KEYWORDS import INDUSTRY_KEYWORDS
import spacy
import pickle  # A vektorok bináris tárolásához
from concurrent.futures import ThreadPoolExecutor

# Constants for weightage
INDUSTRY_KNOWLEDGE_WEIGHT = 0.10
TECHNICAL_SKILLS_WEIGHT = 0.30
JOB_MATCHING_WEIGHT = 0.60

# SpaCy betöltése
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    import subprocess
    import sys
    print("The 'en_core_web_md' model is not installed. Installing...")
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_md"])
    nlp = spacy.load("en_core_web_md")

# Vektorizáció cache-elése
def get_cached_vector(text: str, db: Session):
    try:
        # Ellenőrizzük, hogy a vektor már a cache-ben van-e
        cached = db.query(TextVectorCache).filter_by(text=text).first()
        if cached:
            # Vektor betöltése az adatbázisból
            vector = pickle.loads(cached.vector)
            print(f"Vector found in cache for text: '{text}'")
            return vector
        else:
            # Vektor kiszámítása és mentése a cache-be
            print(f"Calculating and caching vector for text: '{text}'")
            doc = nlp(text)
            vector = doc.vector
            # Vektor mentése az adatbázisba
            cached_vector = TextVectorCache(
                text=text,
                vector=pickle.dumps(vector)
            )
            db.add(cached_vector)
            db.flush()  # Flush a változások írása előtt
            db.commit()  # Elmentjük az adatbázisba
            return vector
    except Exception as e:
        db.rollback()
        print(f"Error during vector caching for text '{text}': {e}")
        raise e

# Kulcsszavak alapján iparági kategorizálás
def match_industry_keywords(text: str, db: Session) -> List[str]:
    matched_industries = []
    cleaned_text = text.lower().strip()

    if not cleaned_text:
        return matched_industries

    # Szöveg vektor lekérése cache-ből vagy vektorizáció
    text_vector = get_cached_vector(cleaned_text, db)

    if np.linalg.norm(text_vector) == 0:
        print("The provided text does not have valid vectors.")
        return matched_industries

    for industry, keywords in INDUSTRY_KEYWORDS.items():
        similarity_scores = []

        for keyword in keywords:
            keyword_clean = keyword.lower().strip()
            # Kulcsszó vektor lekérése
            keyword_vector = get_cached_vector(keyword_clean, db)

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

# Iparági Pontszám Számítása Cache Használatával
def calculate_industry_score_cached(candidate: Candidate, job_description: JobDescription, db: Session) -> float:
    candidate_industries = db.query(CandidateIndustryCache).filter_by(candidate_id=candidate.id).all()
    job_industries = [industry.industry_name for industry in job_description.industries if industry.industry_name]

    if not candidate_industries or not job_industries:
        print(f"No industry data available for comparison.")
        return 0.0

    matching_fields = set([ci.industry_name for ci in candidate_industries]).intersection(set(job_industries))
    total_fields = len(job_industries)

    match_percentage = (len(matching_fields) / total_fields) * 100
    print(f"Matching Fields (Cached): {matching_fields}")
    print(f"Match Percentage (Cached): {match_percentage}%")

    return match_percentage

# Technikai Skillek Pontszám Számítása Cache Használatával
def calculate_technical_skills_score_cached(candidate: Candidate, job_description: JobDescription,
                                            threshold: float = 0.6, db: Session = None) -> float:

    required_skills = [skill.skill_name.lower() for skill in job_description.skills if skill.skill_name]
    candidate_skills = [skill.skill_name.lower() for skill in candidate.skills if skill.skill_name]

    if not required_skills:
        print("No skills required in the job description.")
        return 0.0

    if not candidate_skills:
        print(f"No skills found for Candidate: {candidate.first_name} {candidate.last_name}")
        return 0.0

    total_score = 0

    for req_skill in required_skills:
        req_vector = get_cached_vector(req_skill, db)
        if np.linalg.norm(req_vector) == 0:
            continue
        max_similarity = 0
        for cand_skill in candidate_skills:
            cand_vector = get_cached_vector(cand_skill, db)
            if np.linalg.norm(cand_vector) == 0:
                continue
            similarity = np.dot(req_vector, cand_vector) / (np.linalg.norm(req_vector) * np.linalg.norm(cand_vector))
            if similarity > max_similarity:
                max_similarity = similarity

        if max_similarity >= threshold:
            total_score += max_similarity

    technical_score = (total_score / len(required_skills)) * 100 if required_skills else 0.0
    print(f"Technical Skills Score (Cached): {technical_score}")

    return technical_score
# Job Description Matching Score számítása
def calculate_job_matching_score(candidate: Candidate, job_description: JobDescription, db: Session) -> float:
    candidate_experience_text = " ".join([exp.description.lower() for exp in candidate.experiences if exp.description]).strip()
    job_requirements_text = " ".join([resp.description.lower() for resp in job_description.responsibilities if resp.description]).strip()

    if not candidate_experience_text:
        print("No candidate experience data available.")
        return 0.0

    if not job_requirements_text:
        print("No job requirements data available.")
        return 0.0

    # Szöveg vektorok lekérése
    candidate_vector = get_cached_vector(candidate_experience_text, db)
    job_vector = get_cached_vector(job_requirements_text, db)

    if np.linalg.norm(candidate_vector) == 0 or np.linalg.norm(job_vector) == 0:
        print("No valid vectors for similarity calculation.")
        return 0.0

    # Koszinusz hasonlóság számítása
    similarity = np.dot(candidate_vector, job_vector) / (np.linalg.norm(candidate_vector) * np.linalg.norm(job_vector))
    job_matching_score = similarity * 100
    print(f"Job Matching Score: {job_matching_score}")
    return job_matching_score

# Pontszámok kiszámítása és mentése
def calculate_and_save_final_score(candidate: Candidate, job_description: JobDescription, db: Session):
    print(f"\n=== Calculating Final Score for Candidate: {candidate.first_name} {candidate.last_name} ===")

    existing_score = db.query(CandidateJobScore).filter_by(candidate_id=candidate.id, job_id=job_description.id).first()
    if existing_score:
        print("Score already calculated and saved.")
        return existing_score.final_score

    industry_score = calculate_industry_score_cached(candidate, job_description, db)
    technical_score = calculate_technical_skills_score_cached(candidate, job_description, db=db)
    job_matching_score = calculate_job_matching_score(candidate, job_description, db)

    print(f"Industry Score: {industry_score}")
    print(f"Technical Skills Score: {technical_score}")
    print(f"Job Matching Score: {job_matching_score}")

    final_score = (
        (industry_score * INDUSTRY_KNOWLEDGE_WEIGHT) +
        (technical_score * TECHNICAL_SKILLS_WEIGHT) +
        (job_matching_score * JOB_MATCHING_WEIGHT)
    )

    print(f"Final Score: {final_score}")

    candidate_job_score = CandidateJobScore(
        candidate_id=candidate.id,
        job_id=job_description.id,
        industry_score=industry_score,
        technical_score=technical_score,
        job_matching_score=job_matching_score,
        final_score=final_score
    )
    db.add(candidate_job_score)
    db.commit()

    return final_score

# Jelöltek rangsorolása egy adott állásra
def rank_candidates_for_job(job_description: JobDescription, db: Session, top_n: int = 5) -> List[Dict]:
    candidates = db.query(Candidate).all()
    scores = []

    print(f"\n=== Ranking Candidates for Job: {job_description.job_title} ===")

    def get_score_for_candidate(candidate):
        existing_score = db.query(CandidateJobScore).filter_by(candidate_id=candidate.id, job_id=job_description.id).first()
        if existing_score:
            score = existing_score.final_score
        else:
            score = calculate_and_save_final_score(candidate, job_description, db)
        return {
            "candidate": candidate,
            "score": score
        }

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(get_score_for_candidate, candidates))

    ranked_candidates = sorted(results, key=lambda x: x["score"], reverse=True)[:top_n]

    return [
        {
            "candidate_id": candidate["candidate"].id,
            "first_name": candidate["candidate"].first_name,
            "last_name": candidate["candidate"].last_name,
            "score": candidate["score"]
        }
        for candidate in ranked_candidates
    ]

# Pontszámok előzetes kiszámítása és eltárolása az adatbázisba
def precompute_all_scores(db: Session):
    candidates = db.query(Candidate).all()
    job_descriptions = db.query(JobDescription).all()

    def compute_for_pair(args):
        candidate, job_description = args
        calculate_and_save_final_score(candidate, job_description, db)

    from itertools import product
    candidate_job_pairs = list(product(candidates, job_descriptions))

    print(f"\n=== Precomputing Scores for {len(candidate_job_pairs)} Candidate-Job Pairs ===")

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(compute_for_pair, candidate_job_pairs)

# Fő folyamat indítása
if __name__ == "__main__":
    db = SessionLocal()

    # Előre kiszámítjuk és eltároljuk az összes lehetséges pontszámot
    precompute_all_scores(db)

    # Példa a jelöltek rangsorolására egy adott állásra
    job_id = 2  # Tegyük fel, hogy van egy állás azonosítóval 2

    job_description = db.query(JobDescription).filter_by(id=job_id).first()

    if job_description:
        ranked_candidates = rank_candidates_for_job(job_description, db)
        print("\n--- Ranked Candidates ---\n")
        for candidate in ranked_candidates:
            print(candidate)

    db.close()
