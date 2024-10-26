import PyPDF2
import re


def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF fájlból szöveg kinyerése"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Hiba történt a PDF feldolgozása közben: {e}")
    return text


def split_text_into_blocks(text: str) -> dict:
    """Nyers szöveg logikai blokkokra bontása"""
    # Alapértelmezett blokkok létrehozása
    blocks = {
        "personal_info": "",
        "education": [],
        "experience": [],
        "skills": []
    }

    # Szöveg sorokra bontása
    lines = text.split('\n')

    current_block = "personal_info"
    current_content = []

    # Kulcsszavak definíciója a blokkokhoz
    block_keywords = {
        "education": ["education", "study", "university", "degree"],
        "experience": ["experience", "employment", "worked", "professional"],
        "skills": ["skills", "technologies", "abilities", "competencies"]
    }

    # Sorok elemzése logikai blokkok szerint
    for line in lines:
        line_lower = line.strip().lower()

        # Blokk váltás, ha a sorban kulcsszó található
        if any(keyword in line_lower for keyword in block_keywords["education"]):
            if current_content:
                blocks[current_block].append(" ".join(current_content)) if isinstance(blocks[current_block], list) else \
                blocks[current_block] + " ".join(current_content)
                current_content = []
            current_block = "education"
        elif any(keyword in line_lower for keyword in block_keywords["experience"]):
            if current_content:
                blocks[current_block].append(" ".join(current_content)) if isinstance(blocks[current_block], list) else \
                blocks[current_block] + " ".join(current_content)
                current_content = []
            current_block = "experience"
        elif any(keyword in line_lower for keyword in block_keywords["skills"]):
            if current_content:
                blocks[current_block].append(" ".join(current_content)) if isinstance(blocks[current_block], list) else \
                blocks[current_block] + " ".join(current_content)
                current_content = []
            current_block = "skills"

        # Jelenlegi sor hozzáadása az aktuális blokkhoz
        if line.strip():
            current_content.append(line.strip())

    # Maradék tartalom hozzáadása az utolsó blokkhoz
    if current_content:
        blocks[current_block].append(" ".join(current_content)) if isinstance(blocks[current_block], list) else blocks[
                                                                                                                    current_block] + " ".join(
            current_content)

    return blocks
