import os
import openai
import json
import PyPDF2
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from core.database import SessionLocal
from datetime import datetime
from job_description_model import JobDescription, Benefit, Responsibility, Qualification, PreferredSkill, IndustryField
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
    except Exception as e:
        print(f"Hiba történt a PDF szöveg kinyerése közben: {e}")
        return None

# Function to extract information from a job description using ChatGPT
def extract_job_info(job_text):
    prompt = f"""
    Extract the following data from the job description. Provide the information in JSON format with the keys:
    "JobTitle", "CompanyOverview", "IndustryFields", "KeyResponsibilities", "RequiredQualifications", "PreferredSkills", "Benefits".

    For "PreferredSkills" and "Benefits", list each item individually without grouping. Do not combine different skills or benefits into a single entry. Use short, precise phrases for each item, for example HTML CSS javascript should be 3 different item, try to use only 1-2 word/skills.
    Don't leave anything blank, specific softwares should be listed in preferredskills. Determining the industry field is MANDATORY!
    Example format:
    {{
        "JobTitle": "Senior Software Engineer",
        "CompanyOverview": "Tech-driven company focused on AI and Machine Learning...",
        "IndustryFields": ["Retail", "Banking"],
        "KeyResponsibilities": [
            "Develop software applications",
            "Lead development team",
            "Ensure quality standards"
        ],
        "RequiredQualifications": [
            "Bachelor's degree in Computer Science",
            "5+ years experience in software development"
        ],
        "PreferredSkills": [
            "HTML",
            "CSS",
            "JavaScript",
            "Agile methodologies",
            "Accessibility standards",
            "Web design",
            "Mobile design",
            "AR/VR design"
        ],
        "Benefits": [
            "Competitive salary",
            "Health insurance",
            "Remote work options",
            "Flexible working hours",
            "Performance-based bonuses",
            "Professional development opportunities"
        ]
    }}

    Job Description Content:
    {job_text}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        if response and 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content'].strip()

            # Try parsing the content to JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError as json_err:
                print(f"Hiba: A ChatGPT API válasza nem volt érvényes JSON formátumban. Hiba: {json_err}")
                print(f"Kapott tartalom: {content}")
                return None
        else:
            print("Hiba: A ChatGPT API nem adott vissza megfelelő választ.")
            return None

    except Exception as e:
        print(f"Hiba történt a ChatGPT API hívása közben: {e}")
        return None

# Function to save extracted job data to the database
def save_job_description_to_db(extracted_info, db_session):
    if not extracted_info:
        return

    try:
        # Save basic job description information
        job_description = JobDescription(
            job_title=extracted_info.get("JobTitle", "N/A"),
            company_overview=extracted_info.get("CompanyOverview", "N/A")
        )
        db_session.add(job_description)
        db_session.commit()
        db_session.refresh(job_description)

        # Save industry fields
        for industry in extracted_info.get("IndustryFields", []):
            new_industry = IndustryField(
                industry_name=industry,
                job_description_id=job_description.id
            )
            db_session.add(new_industry)

        # Save responsibilities
        for responsibility in extracted_info.get("KeyResponsibilities", []):
            new_responsibility = Responsibility(
                description=responsibility,
                job_description_id=job_description.id
            )
            db_session.add(new_responsibility)

        # Save qualifications
        for qualification in extracted_info.get("RequiredQualifications", []):
            new_qualification = Qualification(
                description=qualification,
                job_description_id=job_description.id
            )
            db_session.add(new_qualification)

        # Save preferred skills
        for skill in extracted_info.get("PreferredSkills", []):
            new_skill = PreferredSkill(
                skill_name=skill,
                job_description_id=job_description.id
            )
            db_session.add(new_skill)

        # Save benefits
        for benefit in extracted_info.get("Benefits", []):
            new_benefit = Benefit(
                description=benefit,
                job_description_id=job_description.id
            )
            db_session.add(new_benefit)

        db_session.commit()
        print(f"Sikeresen mentettük az adatokat: {job_description.job_title}")

    except Exception as db_err:
        print(f"Hiba történt az adatbázisba mentés közben: {db_err}")
        db_session.rollback()

# Function to process a single job description file
def process_single_job_description(file_name, directory_path):
    db_session = SessionLocal()
    file_path = os.path.join(directory_path, file_name)

    if file_name.endswith(".txt") or file_name.endswith(".pdf"):
        print(f"\n=== Feldolgozás alatt: {file_name} ===\n")

        if file_name.endswith(".txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    job_text = file.read()
            except Exception as file_err:
                print(f"Hiba történt a fájl beolvasása közben: {file_err}")
                return

        elif file_name.endswith(".pdf"):
            job_text = extract_text_from_pdf(file_path)

        if job_text:
            extracted_info = extract_job_info(job_text)
            if extracted_info:
                print("\n=== Kinyert adatok ===\n")
                print(json.dumps(extracted_info, indent=2, ensure_ascii=False))
                save_job_description_to_db(extracted_info, db_session)

    db_session.close()

# Function to process job description files in a directory using threading
def process_job_descriptions_in_directory(directory_path, max_workers=10):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        file_names = [file_name for file_name in os.listdir(directory_path) if file_name.endswith(".txt") or file_name.endswith(".pdf")]
        for file_name in file_names:
            executor.submit(process_single_job_description, file_name, directory_path)

# Example usage
if __name__ == "__main__":
    job_directory = "../dataset/job_descriptions"  # Directory where your job description files are located
    process_job_descriptions_in_directory(job_directory)
