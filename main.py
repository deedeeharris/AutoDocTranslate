import os
import io
import time
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_PARAGRAPH_ALIGNMENT
from docx.oxml.shared import OxmlElement, qn
import fitz  # PyMuPDF
#from google.colab import files # REMOVE: No longer needed in Streamlit
from IPython.display import display, HTML, clear_output #REMOVE
import logging
import streamlit as st # ADDED
#import ipywidgets as widgets # REMOVE: Not needed in Streamlit
#from ipywidgets import Dropdown, Button, HBox, VBox, Layout # REMOVE
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from google.api_core import exceptions as google_api_exceptions

# --- API Key Handling (Streamlit Secrets) ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("Please configure your Gemini API key in Streamlit Secrets.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# --- Generation Config, Model, Logging (same as before) ---
generation_config = {
  "temperature": 0,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
}

model = genai.GenerativeModel(
  model_name="gemini-2.0-pro-exp-02-05",
  generation_config=generation_config,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper Functions (same as before, but remove Colab-specific parts) ---
# ... (All your helper functions: create_header, extract_text_from_docx, etc.) ...
#   - Remove any calls to `files.upload()` or `display()` from IPython.
#   - Keep the PDF and DOCX generation functions.

def create_header(document, text):
    for section in document.sections:
        header = section.header
        paragraph = header.paragraphs[0]
        paragraph.text = text
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

def extract_text_from_docx(docx_bytes):
    try:
        doc = Document(io.BytesIO(docx_bytes))
        full_text = []
        for paragraph in doc.paragraphs:
            full_text.append(paragraph.text)
        return "\n\n".join(full_text)
    except Exception as e:
        logging.error(f"Error extracting text from DOCX: {e}")
        return ""

def extract_text_from_pdf(pdf_bytes):
    text = ""
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return ""

def split_into_paragraphs(text):
    paragraphs = text.split("\n\n")
    return [p.strip() for p in paragraphs if p.strip()]

def create_translation_prompt(source_language, target_language, document_summary, paragraph):
    prompt = f"""You are a professional translator... (rest of prompt)"""
    prompt = f"""You are a professional translator. Translate the following paragraph from {source_language} to {target_language}.
Maintain the original meaning and tone as closely as possible.

Here is a summary of the entire document for context:
{document_summary}

Paragraph to translate:
{paragraph}"""
    return prompt

def translate_paragraph(paragraph, source_language, target_language, document_summary, retries=3, delay=10):
    prompt = create_translation_prompt(source_language, target_language, document_summary, paragraph)

    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            if response.text:
                return response.text, "translated"
            # ... (rest of error handling) ...
            else:
                logging.warning(f"Empty response from Gemini on attempt {attempt + 1}.")
                return "", "failed"
        except google_api_exceptions.ClientError as e:  # Catch Google API Client Errors
            logging.error(f"Gemini API error on attempt {attempt + 1}: {e}")
            if e.code == 400 and "API key not valid" in str(e):
                raise ValueError("Invalid API Key provided.") from e # Re-raise as ValueError for clarity
            elif e.code == 429 or "Response is blocked" in str(e):
                logging.warning("Rate limit exceeded or response blocked. Waiting before retrying...")
            elif attempt < retries - 1:
                logging.info(f"Retrying in {delay} seconds...")
            else:
                return "", "failed"
        except Exception as e:
            logging.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                logging.info(f"Retrying in {delay} seconds...")
            else:
                return "", "failed"
        finally:
            if attempt < retries - 1:  # Only sleep if it's *not* the last attempt.
                time.sleep(delay)

    return "", "failed"  # Return failure only after all retries

def generate_summary(text, max_length=500):
    prompt = f"Summarize the following text... (rest of prompt)"
    prompt = f"Summarize the following text (not in markdown) in no more than {max_length} characters:\n\n{text}"
    try:
        response = model.generate_content(prompt) # Use generate_content
        return response.text if response.text else "Summary generation failed."
    except google_api_exceptions.ClientError as e:
        logging.error(f"Error generating summary: {e}")
        if e.code == 400 and "API key not valid" in str(e):
            raise ValueError("Invalid API Key provided.") from e
        return "Summary generation failed."
    except Exception as e:
        logging.error(f"Error generating summary: {e}")
        return "Summary generation failed."

def set_paragraph_rtl(paragraph):
    pPr = paragraph._element.get_or_add_pPr()
    bidi = OxmlElement('w:bidi')
    pPr.append(bidi)
    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

def set_table_rtl(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = OxmlElement('w:tblPr')
        tbl.append(tblPr)
    bidi_visual = OxmlElement('w:bidiVisual')
    tblPr.append(bidi_visual)

class MyTable(Table):  # No changes needed here
    def wrapOn(self, canv, availWidth, availHeight):
        # Call the original wrapOn method to do the initial calculations.
        width, height = Table.wrapOn(self, canv, availWidth, availHeight)
        # Store the calculated height.  We'll use this later.
        self.calculated_height = height
        return width, height

def create_pdf_with_table(df, filename, is_rtl=False):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    table_cell_style = ParagraphStyle(
        name='TableCellStyle',
        parent=styles['Normal'],
        fontSize=6,
        leading=6,
        alignment=TA_JUSTIFY,
        spaceBefore=0,
        spaceAfter=0,
    )

    data = [['Paragraph ID', 'Source Text', 'Target Text']]
    for index, row in df.iterrows():
        # Conditional alignment based on line count
        source_lines = row['source_text'].count('\n') + 1
        target_lines = row['target_text'].count('\n') + 1

        source_alignment = TA_LEFT if source_lines < 3 else TA_JUSTIFY
        target_alignment = TA_RIGHT if (is_rtl and target_lines < 3) else (TA_LEFT if target_lines < 3 else TA_JUSTIFY)


        wrapped_row = [
            Paragraph(str(row['paragraph_id']), table_cell_style),
            Paragraph(str(row['source_text']), ParagraphStyle(name='SourceStyle', parent=table_cell_style, alignment=source_alignment)),
            Paragraph(str(row['target_text']), ParagraphStyle(name='TargetStyle', parent=table_cell_style, alignment=target_alignment)),
        ]
        data.append(wrapped_row)

    table = Table(data, colWidths=[0.7*inch, 3*inch, 3*inch])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('PADDING', (0, 0), (-1, -1), 0),
    ])
    if is_rtl:
        style.add('RTL', (0, 0), (-1, -1))
    table.setStyle(style)
    elements.append(table)

    def header_footer(canvas, doc):
        canvas.saveState()
        styles = getSampleStyleSheet()
        header = Paragraph("Translated with AI, by Yedidya Harris", styles['Normal'])
        header.wrapOn(canvas, doc.width, doc.topMargin)
        header.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - header.height)
        canvas.restoreState()

    page_template = PageTemplate(id='basic', frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height)], onPage=header_footer)
    doc.addPageTemplates([page_template])
    doc.build(elements)

def create_pdf_from_paragraphs(paragraphs, filename, is_rtl=False):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    style = styles["Normal"]

    for para_text in paragraphs:
        # Count lines in the paragraph
        num_lines = para_text.count('\n') + 1

        # Set alignment based on line count and RTL
        if is_rtl:
            alignment = TA_RIGHT if num_lines < 3 else TA_JUSTIFY
        else:
            alignment = TA_LEFT if num_lines < 3 else TA_JUSTIFY

        style.alignment = alignment  # Set the calculated alignment
        p = Paragraph(para_text, style)
        elements.append(p)

        available_height = doc.height - doc.bottomMargin - doc.topMargin
        if elements:
            y = elements[-1].getSpaceAfter()
            available_height -= y
        w, h = p.wrap(doc.width, available_height)
        if h > available_height:
            elements.append(PageBreak())

    def header_footer(canvas, doc):
        canvas.saveState()
        styles = getSampleStyleSheet()
        header = Paragraph("Translated with AI, by Yedidya Harris", styles['Normal'])
        header.wrapOn(canvas, doc.width, doc.topMargin)
        header.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - header.height)
        canvas.restoreState()

    page_template = PageTemplate(id='basic', frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height)], onPage=header_footer)
    doc.addPageTemplates([page_template])
    doc.build(elements)

# --- Main Application Logic (Streamlit Version) ---

def main():
    st.title("Document Translator")

    # 1. File Upload
    uploaded_file = st.file_uploader("Upload a .docx or .pdf file", type=["docx", "pdf"])
    if uploaded_file is None:
        st.stop()

    # 2. Language Selection
    language_options = [
        ('English', 'en'), ('Spanish', 'es'), ('French', 'fr'), ('German', 'de'),
        ('Chinese (Simplified)', 'zh-CN'), ('Chinese (Traditional)', 'zh-TW'),
        ('Japanese', 'ja'), ('Korean', 'ko'), ('Russian', 'ru'),
        ('Arabic', 'ar'), ('Hebrew', 'he'), ('Portuguese', 'pt'),
        ('Italian', 'it'), ('Dutch', 'nl'), ('Swedish', 'sv'),
        ('Norwegian', 'no'), ('Danish', 'da'), ('Finnish', 'fi'),
        ('Turkish', 'tr'), ('Indonesian', 'id'), ('Vietnamese', 'vi'),
        ('Greek', 'el'), ('Polish', 'pl'), ('Czech', 'cs'),
        ('Hungarian', 'hu'), ('Romanian', 'ro'), ('Thai', 'th'),
        ('Hindi', 'hi')
    ]
    col1, col2 = st.columns(2)
    with col1:
      source_language = st.selectbox("Source Language", options=[lang[0] for lang in language_options], index=0, key="source_lang")
    with col2:
      target_language = st.selectbox("Target Language", options=[lang[0] for lang in language_options], index=0, key = "target_lang")

    source_language_code = [lang[1] for lang in language_options if lang[0] == source_language][0]
    target_language_code = [lang[1] for lang in language_options if lang[0] == target_language][0]

    is_target_rtl = target_language_code.lower() in ['he', 'ar', 'fa', 'ur', 'yi']

    if st.button("Translate"):
        with st.spinner("Translating..."):
            # 3. Document Preprocessing
            file_content = uploaded_file.read()  # Read file content as bytes
            filename = uploaded_file.name

            if filename.endswith(".docx"):
                text = extract_text_from_docx(file_content)
            elif filename.endswith(".pdf"):
                text = extract_text_from_pdf(file_content)
            else:
                st.error("Unsupported file type.")
                st.stop()

            if not text:
                st.error("Could not extract text from the document.")
                st.stop()

            paragraphs = split_into_paragraphs(text)
            try:
                document_summary = generate_summary(text)
                st.write("Document Summary:")
                st.write(document_summary)
            except ValueError as e:
                st.error(f"Error: {e}")
                st.stop()

            # 4. Translation
            df_data = []
            translated_paragraphs = []
            for i, paragraph in enumerate(paragraphs):
                try:
                    translated_text, status = translate_paragraph(paragraph, source_language_code, target_language_code, document_summary)
                    df_data.append({
                        "paragraph_id": i + 1,
                        "source_text": paragraph,
                        "target_text": translated_text,
                        "status": status
                    })
                    if status == "translated":
                        translated_paragraphs.append(translated_text)
                except ValueError as e:
                    st.error(f"Error: {e}")
                    st.stop()

                st.write(f"Translated paragraph {i + 1} of {len(paragraphs)}")

            df = pd.DataFrame(df_data)

            # 5. Output Generation (same as before, but use BytesIO for downloads)
            # --- DOCX Output ---
            combined_doc = Document()
            create_header(combined_doc, "Translated with AI, by Yedidya Harris")
            table = combined_doc.add_table(rows=1, cols=3)
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = 'Paragraph ID'
            hdr_cells[1].text = 'Source Text'
            hdr_cells[2].text = 'Target Text'

            if is_target_rtl:
                set_table_rtl(table)

            for index, row in df.iterrows():
                row_cells = table.add_row().cells
                row_cells[0].text = str(row['paragraph_id'])
                row_cells[1].text = row['source_text']
                row_cells[2].text = row['target_text']

                # Conditional Justification for DOCX (Table)
                for i, cell_text in enumerate([row['source_text'], row['target_text']]):
                    num_lines = cell_text.count('\n') + 1
                    if i == 0:  # Source Text
                        alignment = WD_ALIGN_PARAGRAPH.LEFT if num_lines < 3 else WD_ALIGN_PARAGRAPH.JUSTIFY
                    else:  # Target Text
                        if is_target_rtl:
                            alignment = WD_ALIGN_PARAGRAPH.RIGHT if num_lines < 3 else WD_ALIGN_PARAGRAPH.JUSTIFY
                        else:
                            alignment = WD_ALIGN_PARAGRAPH.LEFT if num_lines < 3 else WD_ALIGN_PARAGRAPH.JUSTIFY

                    for paragraph in row_cells[i+1].paragraphs:
                        paragraph.alignment = alignment
                        if is_target_rtl and i == 1: # Apply RTL if needed
                            set_paragraph_rtl(paragraph)

            # Save to BytesIO object
            combined_doc_bytes = io.BytesIO()
            combined_doc.save(combined_doc_bytes)
            combined_doc_bytes.seek(0)  # Important: Reset stream position to the beginning


            translated_doc = Document()
            create_header(translated_doc, "Translated with AI, by Yedidya Harris")
            for paragraph_text in translated_paragraphs:
                # Conditional Justification for DOCX (Translated Document)
                num_lines = paragraph_text.count('\n') + 1
                if is_target_rtl:
                    alignment = WD_ALIGN_PARAGRAPH.RIGHT if num_lines < 3 else WD_ALIGN_PARAGRAPH.JUSTIFY
                else:
                    alignment = WD_ALIGN_PARAGRAPH.LEFT if num_lines < 3 else WD_ALIGN_PARAGRAPH.JUSTIFY

                paragraph = translated_doc.add_paragraph(paragraph_text)
                paragraph.alignment = alignment
                if is_target_rtl:
                    set_paragraph_rtl(paragraph)
                translated_doc.add_paragraph("")  # Two line breaks
                translated_doc.add_paragraph("")

            # Save to BytesIO object
            translated_doc_bytes = io.BytesIO()
            translated_doc.save(translated_doc_bytes)
            translated_doc_bytes.seek(0)

            # --- PDF Output ---
            combined_pdf_bytes = io.BytesIO()
            create_pdf_with_table(df, combined_pdf_bytes, is_rtl=is_target_rtl)
            combined_pdf_bytes.seek(0)

            translated_pdf_bytes = io.BytesIO()
            create_pdf_from_paragraphs(translated_paragraphs, translated_pdf_bytes, is_rtl=is_target_rtl)
            translated_pdf_bytes.seek(0)

            # 6. Download Links (Streamlit Version)
            st.download_button("Download Combined Translation (DOCX)", data=combined_doc_bytes, file_name="combined_translation.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            st.download_button("Download Translated Document (DOCX)", data=translated_doc_bytes, file_name="translated_document.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            st.download_button("Download Combined Translation (PDF)", data=combined_pdf_bytes, file_name="combined_translation.pdf", mime="application/pdf")
            st.download_button("Download Translated Document (PDF)", data=translated_pdf_bytes, file_name="translated_document.pdf", mime="application/pdf")

            st.success("Translation complete!")
            st.dataframe(df)

if __name__ == "__main__":
    main()
