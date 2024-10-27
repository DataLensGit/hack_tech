import os
from docx import Document
from fpdf import FPDF

def convert_docx_to_pdf(docx_path, pdf_path):
    # Megnyitjuk a .docx fájlt
    doc = Document(docx_path)

    # Létrehozunk egy PDF objektumot
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)  # Arial helyett Helvetica, amely támogatott az fpdf-ben

    # Minden bekezdést hozzáadunk a PDF-hez, kezelve a hosszú sorokat és az Unicode karaktereket
    for para in doc.paragraphs:
        if para.text.strip():  # Ellenőrizzük, hogy a bekezdés nem üres-e
            text = para.text.encode('latin-1', 'ignore').decode('latin-1')  # Unicode karakterek eltávolítása
            lines = text.split('\n')
            for line in lines:
                pdf.multi_cell(0, 10, line)
            pdf.ln(5)  # Egy kis üres helyet hagyunk a bekezdések között

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
