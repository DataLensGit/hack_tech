import json
import pdfplumber
from sqlalchemy.orm import Session
from core.database import SessionLocal
from core.job_description_model import JobDescription

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        # Összes oldal szövegének összegyűjtése
        text = "\n".join(page.extract_text() for page in pdf.pages)
    return text


def parse_job_description(text):
    # Egyszerű szövegfeldolgozás a PDF szövegének felosztására
    # Eredményt JSON formátumban adja vissza, amely később jól használható az OpenAI API-hoz
    sections = {
        "job_title": None,
        "company_overview": None,
        "key_responsibilities": None,
        "required_qualifications": None,
        "preferred_skills": None,
        "benefits": None
    }

    # A szöveg szétválasztása a különböző szekciókra
    lines = text.split('\n')
    current_section = None
    for line in lines:
        line = line.strip()
        if "Job Title" in line:
            current_section = "job_title"
        elif "Company Overview" in line:
            current_section = "company_overview"
        elif "Key Responsibilities" in line:
            current_section = "key_responsibilities"
        elif "Required Qualifications" in line:
            current_section = "required_qualifications"
        elif "Preferred Skills" in line:
            current_section = "preferred_skills"
        elif "Benefits" in line:
            current_section = "benefits"
        elif current_section and line:
            if sections[current_section]:
                sections[current_section] += " " + line
            else:
                sections[current_section] = line
    # Debug kimenet a visszatérési érték ellenőrzéséhez
    print("Parsed Sections:")
    for section, content in sections.items():
        print(f"{section}: {content}")

    return sections
    # Eredmény JSON formátumra alakítása
    #json_result = json.dumps(sections, indent=4)
    #return json_result


def save_to_database(sections):
    db: Session = SessionLocal()
    try:
        # Debug kimenet az adatbázisba mentés előtt
        print("Saving to database:", sections)

        job_description = JobDescription(
            job_title=sections.get("job_title"),
            company_overview=sections.get("company_overview"),
            key_responsibilities=sections.get("key_responsibilities"),
            required_qualifications=sections.get("required_qualifications"),
            preferred_skills=sections.get("preferred_skills"),
            benefits=sections.get("benefits")
        )
        db.add(job_description)
        db.commit()

        # Debug kimenet a sikeres mentés után
        print("Record saved successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error saving to database: {e}")
    finally:
        db.close()


def process_pdf(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    sections_json = parse_job_description(text)
    save_to_database(sections_json)