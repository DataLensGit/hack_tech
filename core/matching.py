import numpy as np
from typing import List, Dict
from sqlalchemy.orm import Session
from core.database import SessionLocal
from candidates_models import Candidate, Experience, Skill  # Import your candidate models here
from job_description_model import JobDescription, Responsibility, Qualification, PreferredSkill, IndustryField

# Constants for weightage
INDUSTRY_KNOWLEDGE_WEIGHT = 0.10
TECHNICAL_SKILLS_WEIGHT = 0.30
JOB_MATCHING_WEIGHT = 0.60

# Function to calculate Industry Knowledge Score
def calculate_industry_score(candidate: Candidate, job_description: JobDescription) -> float:
    # Csak azok az iparágak kerüljenek be, ahol az exp.company nem None
    candidate_industries = {exp.company.lower() for exp in candidate.experiences if exp.company}
    job_industries = {industry.industry_name.lower() for industry in job_description.industries}

    print(f"\n--- Calculating Industry Score ---")
    print(f"Candidate Industries: {candidate_industries}")
    print(f"Job Industries: {job_industries}")

    if not job_industries:
        print("No industry specified in the job description.")
        return 0.0

    # Check if the candidate has experience in the relevant industries
    if candidate_industries.intersection(job_industries):
        print("Direct industry match found. Full score awarded.")
        return 100.0
    elif any(industry in candidate_industries for industry in job_industries):
        print("Partial industry match found. Partial score awarded.")
        return 50.0
    else:
        print("No relevant industry experience.")
        return 0.0

# Function to calculate Technical Skills Score
def calculate_technical_skills_score(candidate: Candidate, job_description: JobDescription) -> float:
    required_skills = {skill.skill_name.lower() for skill in job_description.skills}
    candidate_skills = {skill.skill_name.lower() for skill in candidate.skills}

    print(f"\n--- Calculating Technical Skills Score ---")
    print(f"Required Skills: {required_skills}")
    print(f"Candidate Skills: {candidate_skills}")

    if not required_skills:
        print("No skills required in the job description.")
        return 0.0

    matched_skills = required_skills.intersection(candidate_skills)
    unmatched_skills = required_skills.difference(candidate_skills)

    print(f"Matched Skills: {matched_skills}")
    print(f"Unmatched Skills: {unmatched_skills}")

    # Score based on the number of matched skills and their weightage
    total_weight = 100
    matched_weight = (len(matched_skills) / len(required_skills)) * total_weight
    print(f"Technical Skills Score: {matched_weight}")
    return matched_weight

# Function to calculate Job Description Matching Score
def calculate_job_matching_score(candidate: Candidate, job_description: JobDescription) -> float:
    candidate_experience_text = " ".join([exp.description.lower() for exp in candidate.experiences])
    job_requirements_text = " ".join([resp.description.lower() for resp in job_description.responsibilities])

    print(f"\n--- Calculating Job Matching Score ---")
    print(f"Candidate Experience Text: {candidate_experience_text}")
    print(f"Job Requirements Text: {job_requirements_text}")

    # Basic keyword matching for relevance score (e.g., overlap ratio)
    common_keywords = set(candidate_experience_text.split()).intersection(set(job_requirements_text.split()))
    total_keywords = set(job_requirements_text.split())

    print(f"Common Keywords: {common_keywords}")
    print(f"Total Keywords in Job Description: {total_keywords}")

    if not total_keywords:
        print("No specific requirements in job description.")
        return 0.0

    match_ratio = len(common_keywords) / len(total_keywords)
    print(f"Job Matching Score: {match_ratio * 100.0}")
    return match_ratio * 100.0

# Function to calculate Final Score for a Candidate
def calculate_final_score(candidate: Candidate, job_description: JobDescription) -> float:
    print(f"\n=== Calculating Final Score for Candidate: {candidate.first_name} {candidate.last_name} ===")
    industry_score = calculate_industry_score(candidate, job_description)
    technical_score = calculate_technical_skills_score(candidate, job_description)
    job_matching_score = calculate_job_matching_score(candidate, job_description)

    print(f"Industry Score: {industry_score}")
    print(f"Technical Skills Score: {technical_score}")
    print(f"Job Matching Score: {job_matching_score}")

    final_score = (
        (industry_score * INDUSTRY_KNOWLEDGE_WEIGHT) +
        (technical_score * TECHNICAL_SKILLS_WEIGHT) +
        (job_matching_score * JOB_MATCHING_WEIGHT)
    )

    print(f"Final Score: {final_score}")
    return final_score

# Function to rank candidates for a specific job
def rank_candidates_for_job(job_description: JobDescription, db: Session, top_n: int = 5) -> List[Dict]:
    candidates = db.query(Candidate).all()
    scores = []

    print(f"\n=== Ranking Candidates for Job: {job_description.job_title} ===")

    for candidate in candidates:
        score = calculate_final_score(candidate, job_description)
        scores.append({"candidate": candidate, "score": score})

    # Sort candidates by score in descending order and return top N
    ranked_candidates = sorted(scores, key=lambda x: x["score"], reverse=True)[:top_n]

    # Return the candidates with the final score
    return [
        {
            "candidate_id": candidate["candidate"].id,
            "first_name": candidate["candidate"].first_name,
            "last_name": candidate["candidate"].last_name,
            "score": candidate["score"]
        }
        for candidate in ranked_candidates
    ]

# Function to find best matching job for a specific candidate
def find_best_matching_job(candidate: Candidate, db: Session) -> Dict:
    job_descriptions = db.query(JobDescription).all()
    best_match = None
    best_score = 0.0

    print(f"\n=== Finding Best Matching Job for Candidate: {candidate.first_name} {candidate.last_name} ===")

    for job_description in job_descriptions:
        score = calculate_final_score(candidate, job_description)

        if score > best_score:
            best_score = score
            best_match = job_description

    if best_match:
        print(f"Best Match Found: {best_match.job_title} with Score: {best_score}")
        return {
            "job_title": best_match.job_title,
            "company_overview": best_match.company_overview,
            "score": best_score
        }
    else:
        print("No suitable job found for the candidate.")
        return {
            "message": "No suitable job found for the candidate."
        }

# Example usage
if __name__ == "__main__":
    db = SessionLocal()

    # Example to rank candidates for a specific job
    job_id = 1  # Assume you have a job with ID 1
    job_description = db.query(JobDescription).filter_by(id=job_id).first()

    if job_description:
        ranked_candidates = rank_candidates_for_job(job_description, db)
        print(f"\nTop candidates for job '{job_description.job_title}':")
        for rank in ranked_candidates:
            print(rank)

    # Example to find best matching job for a candidate
    candidate_id = 1  # Assume you have a candidate with ID 1
    candidate = db.query(Candidate).filter_by(id=candidate_id).first()

    if candidate:
        best_job = find_best_matching_job(candidate, db)
        print(f"\nBest matching job for candidate '{candidate.first_name} {candidate.last_name}':")
        print(best_job)

    db.close()
