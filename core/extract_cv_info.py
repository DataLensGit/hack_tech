import os
import openai
import json
import PyPDF2
from datetime import datetime
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Import your database session and models
from core.database import SessionLocal
from candidates_models import (
    create_candidate,
    add_education,
    add_experience,
    add_skill,
    add_language,
    add_certificate,
    add_project,
    add_attachment
)

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


# Function to extract information from CV using ChatGPT
def extract_cv_info(cv_text, file_name):
    prompt = f"""
    The file name of the CV is: {file_name}.
    Extract the following data from the candidate's CV. Provide the information in JSON format with the keys:
    "IndustryExperience", "TechnicalSkills", "RelevantCertifications", "JobTitles", "Responsibilities", "ToolsTechnologies", "FirstName", "LastName", "Email", "Languages", "Education".

    Each section should be structured as follows:

    - Languages: A list of dictionaries with "Language" and "Proficiency" (e.g., Fluent, Intermediate).
    - Education: A list of dictionaries with "Degree", "FieldOfStudy", "Institution", "StartYear", and "EndYear".

    Example format:
    {{
        "FirstName": "John",
        "LastName": "Doe",
        "Email": "johndoe@example.com",
        "IndustryExperience": ["Banking", "Healthcare"],
        "TechnicalSkills": [
            {{"SkillName": "Python", "Level": "Expert"}},
            {{"SkillName": "JavaScript", "Level": "Intermediate"}}
        ],
        "RelevantCertifications": ["AWS Certified Solutions Architect", "Certified Scrum Master"],
        "JobTitles": ["Software Engineer", "Backend Developer"],
        "Responsibilities": ["Led a team of 5 developers", "Implemented CI/CD pipelines"],
        "ToolsTechnologies": ["Docker", "Kubernetes", "AWS", "React"],
        "Languages": [
            {{"Language": "English", "Proficiency": "Fluent"}},
            {{"Language": "French", "Proficiency": "Intermediate"}}
        ],
        "Education": [
            {{"Degree": "Bachelor of Science", "FieldOfStudy": "Computer Science", "Institution": "XYZ University", "StartYear": 2015, "EndYear": 2019}},
            {{"Degree": "Master of Science", "FieldOfStudy": "Data Science", "Institution": "ABC University", "StartYear": 2020, "EndYear": 2022}}
        ]
    }}

    CV Content:
    {cv_text}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )

        if response and 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content'].strip()
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                print("Hiba: A ChatGPT API válasza nem volt érvényes JSON formátumban.")
                print(f"Kapott tartalom: {content}")
                return None
        else:
            print("Hiba: A ChatGPT API nem adott vissza megfelelő választ.")
            return None

    except Exception as e:
        print(f"Hiba történt a ChatGPT API hívása közben: {e}")
        return None


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


def safe_year_conversion(year_str):
    try:
        return int(year_str)
    except (ValueError, TypeError):
        return None


# Function to save extracted data to the database
def save_extracted_data_to_db(extracted_info, file_name, db_session):
    if not extracted_info:
        return

    print(f"\n=== Kinyert adatok ({file_name}) ===\n")
    print(json.dumps(extracted_info, indent=2, ensure_ascii=False))

    first_name = extracted_info.get("FirstName", "N/A")
    last_name = extracted_info.get("LastName", "N/A")
    email = extracted_info.get("Email", "N/A")

    candidate = create_candidate(
        db=db_session,
        first_name=first_name,
        last_name=last_name,
        email=email,
    )

    if "IndustryExperience" in extracted_info:
        for industry in extracted_info["IndustryExperience"]:
            add_project(
                db=db_session,
                candidate_id=candidate.id,
                project_name=industry,
                description=f"Experience in {industry}",
                start_date=None,
                end_date=None
            )

    if "TechnicalSkills" in extracted_info:
        for skill in extracted_info["TechnicalSkills"]:
            skill_name = skill.get("SkillName")
            skill_level = skill.get("Level")
            add_skill(
                db=db_session,
                candidate_id=candidate.id,
                skill_name=skill_name,
                skill_level=skill_level
            )

    if "RelevantCertifications" in extracted_info:
        for cert in extracted_info["RelevantCertifications"]:
            add_certificate(
                db=db_session,
                candidate_id=candidate.id,
                certificate_name=cert
            )

    if "JobTitles" in extracted_info and "Responsibilities" in extracted_info:
        for job_title, responsibility in zip(extracted_info["JobTitles"], extracted_info["Responsibilities"]):
            add_experience(
                db=db_session,
                candidate_id=candidate.id,
                job_title=job_title,
                company=None,
                description=responsibility
            )

    if "ToolsTechnologies" in extracted_info:
        for tool in extracted_info["ToolsTechnologies"]:
            add_skill(
                db=db_session,
                candidate_id=candidate.id,
                skill_name=tool,
                skill_level="Intermediate"
            )

    if "Languages" in extracted_info:
        for language in extracted_info["Languages"]:
            add_language(
                db=db_session,
                candidate_id=candidate.id,
                language=language.get("Language"),
                proficiency=language.get("Proficiency")
            )

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

    add_attachment(
        db=db_session,
        candidate_id=candidate.id,
        file_name=file_name,
        file_path=os.path.abspath(file_name),
        upload_date=datetime.now()
    )


# Function to process a single CV file
def process_single_cv(file_name, directory_path):
    db_session = SessionLocal()
    pdf_path = os.path.join(directory_path, file_name)

    if file_name.endswith(".pdf"):
        print(f"\n=== Feldolgozás alatt: {file_name} ===\n")

        cv_text = extract_text_from_pdf(pdf_path)
        if cv_text:
            extracted_info = extract_cv_info(cv_text, file_name)
            if extracted_info:
                save_extracted_data_to_db(extracted_info, file_name, db_session)

    db_session.close()


# Function to process CV files in a directory using threading
def process_cvs_in_directory(directory_path, max_workers=10):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        file_names = [file_name for file_name in os.listdir(directory_path) if file_name.endswith(".pdf")]
        for file_name in file_names:
            executor.submit(process_single_cv, file_name, directory_path)


# Example usage
cv_directory = "../cv-s"  # Directory where your CV files are located
process_cvs_in_directory(cv_directory)
