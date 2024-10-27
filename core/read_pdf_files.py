import os
import json
import pdfplumber
from datetime import datetime
from core.database import SessionLocal
from core.candidates_models import Candidate, Education, Experience, Skill, Language, Certificate, Project, Attachment
from core.inserting_data import parse_job_description  # A PDF szöveg elemzéséhez szükséges függvény

# Biztonságos év átalakítás a datetime objektumokhoz
def safe_year_conversion(year):
    try:
        return int(year)
    except (ValueError, TypeError):
        return None

# Jelölt létrehozása és mentése az adatbázisba
def create_candidate(db, first_name, last_name, email, phone_number, location, linkedin_url, summary):
    candidate = Candidate(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=phone_number,
        location=location,
        linkedin_url=linkedin_url,
        summary=summary
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate

# Oktatás hozzáadása
def add_education(db, candidate_id, degree, institution, start_date, end_date, field_of_study):
    education = Education(
        candidate_id=candidate_id,
        degree=degree,
        institution=institution,
        start_date=start_date,
        end_date=end_date,
        field_of_study=field_of_study
    )
    db.add(education)
    db.commit()

# Munkatapasztalat hozzáadása
def add_experience(db, candidate_id, job_title, company, location, start_date, end_date, description):
    experience = Experience(
        candidate_id=candidate_id,
        job_title=job_title,
        company=company,
        location=location,
        start_date=start_date,
        end_date=end_date,
        description=description
    )
    db.add(experience)
    db.commit()

# Technikai készségek hozzáadása
def add_skill(db, candidate_id, skill_name, skill_level):
    skill = Skill(
        candidate_id=candidate_id,
        skill_name=skill_name,
        skill_level=skill_level
    )
    db.add(skill)
    db.commit()

# Nyelvismeret hozzáadása
def add_language(db, candidate_id, language, proficiency):
    language_record = Language(
        candidate_id=candidate_id,
        language=language,
        proficiency=proficiency
    )
    db.add(language_record)
    db.commit()

# Tanúsítványok hozzáadása
def add_certificate(db, candidate_id, certificate_name, issuing_organization, issue_date, expiration_date, certificate_url):
    certification = Certificate(
        candidate_id=candidate_id,
        certificate_name=certificate_name,
        issuing_organization=issuing_organization,
        issue_date=issue_date,
        expiration_date=expiration_date,
        certificate_url=certificate_url
    )
    db.add(certification)
    db.commit()

# Projektek hozzáadása
def add_project(db, candidate_id, project_name, description, start_date, end_date, url):
    project = Project(
        candidate_id=candidate_id,
        project_name=project_name,
        description=description,
        start_date=start_date,
        end_date=end_date,
        url=url
    )
    db.add(project)
    db.commit()

# Mellékletek hozzáadása
def add_attachment(db, candidate_id, file_name, file_path, upload_date):
    attachment = Attachment(
        candidate_id=candidate_id,
        file_name=file_name,
        file_path=file_path,
        upload_date=upload_date
    )
    db.add(attachment)
    db.commit()

# Funkció az adatok kinyerésére és mentésére
def save_extracted_data_to_db(extracted_info, file_name, db_session):
    if not extracted_info:
        return

    print(f"\n=== Extracted Data ({file_name}) ===\n")
    print(json.dumps(extracted_info, indent=2, ensure_ascii=False))

    # Jelölt információ mentése
    first_name = extracted_info.get("FirstName", "N/A")
    last_name = extracted_info.get("LastName", "N/A")
    email = extracted_info.get("Email", "N/A")
    phone_number = extracted_info.get("PhoneNumber")
    location = extracted_info.get("Location")
    linkedin_url = extracted_info.get("LinkedInURL")
    summary = extracted_info.get("Summary")

    candidate = create_candidate(
        db=db_session,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=phone_number,
        location=location,
        linkedin_url=linkedin_url,
        summary=summary
    )

    # Oktatás részletek mentése
    if "Education" in extracted_info:
        for edu in extracted_info["Education"]:
            start_year = safe_year_conversion(edu.get("StartYear"))
            end_year = safe_year_conversion(edu.get("EndYear"))
            add_education(
                db=db_session,
                candidate_id=candidate.id,
                degree=edu.get("Degree"),
                institution=edu.get("Institution"),
                start_date=datetime(year=start_year, month=1, day=1) if start_year else None,
                end_date=datetime(year=end_year, month=1, day=1) if end_year else None,
                field_of_study=edu.get("FieldOfStudy")
            )

    # Munkatapasztalatok mentése
    if "Experience" in extracted_info:
        for exp in extracted_info["Experience"]:
            start_year = safe_year_conversion(exp.get("StartYear"))
            end_year = safe_year_conversion(exp.get("EndYear"))
            add_experience(
                db=db_session,
                candidate_id=candidate.id,
                job_title=exp.get("JobTitle"),
                company=exp.get("Company"),
                location=exp.get("Location"),
                start_date=datetime(year=start_year, month=1, day=1) if start_year else None,
                end_date=datetime(year=end_year, month=1, day=1) if end_year else None,
                description=exp.get("Description")
            )

    # Technikai készségek mentése
    if "TechnicalSkills" in extracted_info:
        for skill in extracted_info["TechnicalSkills"]:
            add_skill(
                db=db_session,
                candidate_id=candidate.id,
                skill_name=skill.get("SkillName"),
                skill_level=skill.get("Level")
            )

    # Nyelvek mentése
    if "Languages" in extracted_info:
        for language in extracted_info["Languages"]:
            add_language(
                db=db_session,
                candidate_id=candidate.id,
                language=language.get("Language"),
                proficiency=language.get("Proficiency")
            )

    # Tanúsítványok mentése
    if "RelevantCertifications" in extracted_info:
        for cert in extracted_info["RelevantCertifications"]:
            add_certificate(
                db=db_session,
                candidate_id=candidate.id,
                certificate_name=cert.get("CertificationName"),
                issuing_organization=cert.get("IssuingOrganization"),
                issue_date=datetime(year=safe_year_conversion(cert.get("IssueYear")), month=1, day=1),
                expiration_date=datetime(year=safe_year_conversion(cert.get("ExpirationYear")), month=1, day=1) if cert.get("ExpirationYear") else None,
                certificate_url=cert.get("CertificateURL")
            )

    # Projektek mentése
    if "Projects" in extracted_info:
        for proj in extracted_info["Projects"]:
            start_year = safe_year_conversion(proj.get("StartYear"))
            end_year = safe_year_conversion(proj.get("EndYear"))
            add_project(
                db=db_session,
                candidate_id=candidate.id,
                project_name=proj.get("ProjectName"),
                description=proj.get("Description"),
                start_date=datetime(year=start_year, month=1, day=1) if start_year else None,
                end_date=datetime(year=end_year, month=1, day=1) if end_year else None,
                url=proj.get("ProjectURL")
            )

    # Mellékletek mentése
    if "Attachments" in extracted_info:
        for attach in extracted_info["Attachments"]:
            add_attachment(
                db=db_session,
                candidate_id=candidate.id,
                file_name=attach.get("FileName"),
                file_path=attach.get("FilePath"),
                upload_date=datetime.now()
            )

# Rekurzív PDF feldolgozás, majd az adatbázisba mentés
def process_pdf_files(db):
    dataset_paths = [
        "../dataset/job_descriptions",  # Az eredeti mappa, ahol a korábbi PDF-ek vannak
        "../dataset/pdfs"               # A mappa, ahol több almappa is lehet PDF-ekkel
    ]

    for dataset_path in dataset_paths:
        if not os.path.exists(dataset_path):
            print(f"Dataset mappa nem található: {dataset_path}")
            continue

        for root, _, files in os.walk(dataset_path):
            for filename in files:
                if filename.endswith(".pdf"):
                    file_path = os.path.join(root, filename)
                    try:
                        # PDF fájl olvasása
                        with pdfplumber.open(file_path) as pdf:
                            text = "\n".join(page.extract_text() for page in pdf.pages)

                        # PDF szöveg elemzése
                        extracted_info = parse_job_description(text)

                        # Kinyert adatok mentése az adatbázisba
                        save_extracted_data_to_db(extracted_info, filename, db)
                        print(f"Sikeresen feldolgozva: {file_path}")
                    except Exception as e:
                        print(f"Hiba a '{file_path}' feldolgozása során: {e}")
                        db.rollback()

# Adatbázis kapcsolat létrehozása és PDF fájlok feldolgozása
if __name__ == "__main__":
    db = SessionLocal()
    process_pdf_files(db)
    db.close()
