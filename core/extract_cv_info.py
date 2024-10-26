import os
import openai
import json
import PyPDF2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


# Function to extract information from CV using ChatGPT
def extract_cv_info(cv_text):
    prompt = f"""
    Extract the following data from the candidate's CV. Provide the information in JSON format with the keys:
    "IndustryExperience", "TechnicalSkills", "RelevantCertifications", "JobTitles", "Responsibilities", "ToolsTechnologies".

    Example format:
    {{
        "IndustryExperience": ["Banking", "Healthcare"],
        "TechnicalSkills": [
            {{"SkillName": "Python", "Level": "Expert"}},
            {{"SkillName": "JavaScript", "Level": "Intermediate"}}
        ],
        "RelevantCertifications": ["AWS Certified Solutions Architect", "Certified Scrum Master"],
        "JobTitles": ["Software Engineer", "Backend Developer"],
        "Responsibilities": ["Led a team of 5 developers", "Implemented CI/CD pipelines"],
        "ToolsTechnologies": ["Docker", "Kubernetes", "AWS", "React"]
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

        # Check if the response has content
        if response and 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content'].strip()

            # Try parsing the content to JSON
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


# Function to process CV files in a directory
def process_cvs_in_directory(directory_path):
    for file_name in os.listdir(directory_path):
        if file_name.endswith(".pdf"):
            pdf_path = os.path.join(directory_path, file_name)
            print(f"\n=== Feldolgozás alatt: {file_name} ===\n")

            # Use PDF-to-text extraction
            cv_text = extract_text_from_pdf(pdf_path)

            # If text extraction was successful, proceed to ChatGPT API call
            if cv_text:
                extracted_info = extract_cv_info(cv_text)

                # Print the extracted information
                if extracted_info:
                    print("\n=== Kinyert adatok ===\n")
                    print(json.dumps(extracted_info, indent=2, ensure_ascii=False))


# Example usage
cv_directory = "../cv-s"  # Directory where your CV files are located
process_cvs_in_directory(cv_directory)
