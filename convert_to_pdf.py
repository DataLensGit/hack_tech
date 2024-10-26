import os
from docx import Document
from fpdf import FPDF


def convert_docx_to_pdf(docx_path, pdf_path):
    # Megnyitjuk a .docx fájlt
    doc = Document(docx_path)

    # Létrehozunk egy PDF objektumot
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Minden bekezdést hozzáadunk a PDF-hez
    for para in doc.paragraphs:
        pdf.multi_cell(0, 10, para.text)

    # Mentjük a PDF fájlt
    pdf.output(pdf_path)


def convert_folder_docx_to_pdf(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".docx"):
            docx_path = os.path.join(folder_path, filename)
            pdf_filename = os.path.splitext(filename)[0] + ".pdf"
            pdf_path = os.path.join(folder_path, pdf_filename)

            convert_docx_to_pdf(docx_path, pdf_path)
            print(f'Konvertálva: {filename} -> {pdf_filename}')


# Mappa elérési útjának beállítása
folder_path = './cv-s'
convert_folder_docx_to_pdf(folder_path)
