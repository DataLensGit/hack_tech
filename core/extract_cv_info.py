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
    "FirstName", "LastName", "Email", "PhoneNumber", "Location", "LinkedInURL", "Summary",
    "Education", "Experience", "TechnicalSkills", "Languages", "RelevantCertifications", "Projects", "Attachments".

    Each section should be structured as follows:

    - Education: A list of dictionaries with "Degree", "FieldOfStudy", "Institution", "StartYear", and "EndYear".
    - Experience: A list of dictionaries with "JobTitle", "Company", "Location", "StartYear", "EndYear", and "Description".
    - TechnicalSkills: A list of dictionaries with "SkillName" and "Level" (e.g., Expert, Intermediate, Beginner).
    - Languages: A list of dictionaries with "Language" and "Proficiency" (e.g., Fluent, Intermediate).
    - RelevantCertifications: A list of dictionaries with "CertificationName", "IssuingOrganization", "IssueYear", "ExpirationYear", and "CertificateURL".
    - Projects: A list of dictionaries with "ProjectName", "Description", "StartYear", "EndYear", and "ProjectURL".
    - Attachments: A list of dictionaries with "FileName", "FilePath", and "UploadDate".

    Example format:
    {{
        "FirstName": "John",
        "LastName": "Doe",
        "Email": "johndoe@example.com",
        "PhoneNumber": "+1234567890",
        "Location": "New York, USA",
        "LinkedInURL": "https://www.linkedin.com/in/johndoe/",
        "Summary": "Experienced software engineer with expertise in backend systems and cloud solutions.",
        "Education": [
            {{"Degree": "Bachelor of Science", "FieldOfStudy": "Computer Science", "Institution": "XYZ University", "StartYear": 2015, "EndYear": 2019}},
            {{"Degree": "Master of Science", "FieldOfStudy": "Data Science", "Institution": "ABC University", "StartYear": 2020, "EndYear": 2022}}
        ],
        "Experience": [
            {{"JobTitle": "Software Engineer", "Company": "Tech Solutions", "Location": "San Francisco", "StartYear": 2019, "EndYear": 2021, "Description": "Developed backend APIs."}},
            {{"JobTitle": "Senior Developer", "Company": "Innovate Corp", "Location": "New York", "StartYear": 2021, "EndYear": 2023, "Description": "Led a team of developers."}}
        ],
        "TechnicalSkills": [
            {{"SkillName": "Python", "Level": "Expert"}},
            {{"SkillName": "JavaScript", "Level": "Intermediate"}}
        ],
        "Languages": [
            {{"Language": "English", "Proficiency": "Fluent"}},
            {{"Language": "French", "Proficiency": "Intermediate"}}
        ],
        "RelevantCertifications": [
            {{"CertificationName": "AWS Certified Solutions Architect", "IssuingOrganization": "Amazon", "IssueYear": 2021, "ExpirationYear": 2024, "CertificateURL": "https://aws.com/certified"}}
        ],
        "Projects": [
            {{"ProjectName": "Project A", "Description": "Built a cloud-based solution.", "StartYear": 2020, "EndYear": 2021, "ProjectURL": "https://project-a.com"}}
        ],
        "Attachments": [
            {{"FileName": "CV_JohnDoe.pdf", "FilePath": "/uploads/CV_JohnDoe.pdf", "UploadDate": "2024-10-26"}}
        ]
    }}

    CV Content:
    {cv_text}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        if response and 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content'].strip()
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                print("Error: The ChatGPT API response was not valid JSON format.")
                print(f"Received content: {content}")
                return None
        else:
            print("Error: The ChatGPT API did not provide a valid response.")
            return None

    except Exception as e:
        print(f"Error occurred during ChatGPT API call: {e}")
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

    print(f"\n=== Extracted Data ({file_name}) ===\n")
    print(json.dumps(extracted_info, indent=2, ensure_ascii=False))

    # Save the basic candidate information
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

    # Save education details
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

    # Save work experience
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

    # Save technical skills
    if "TechnicalSkills" in extracted_info:
        for skill in extracted_info["TechnicalSkills"]:
            add_skill(
                db=db_session,
                candidate_id=candidate.id,
                skill_name=skill.get("SkillName"),
                skill_level=skill.get("Level")
            )

    # Save languages
    if "Languages" in extracted_info:
        for language in extracted_info["Languages"]:
            add_language(
                db=db_session,
                candidate_id=candidate.id,
                language=language.get("Language"),
                proficiency=language.get("Proficiency")
            )

    # Save certifications
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

    # Save projects
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

    # Save attachments
    if "Attachments" in extracted_info:
        for attach in extracted_info["Attachments"]:
            add_attachment(
                db=db_session,
                candidate_id=candidate.id,
                file_name=attach.get("FileName"),
                file_path=attach.get("FilePath"),
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
