import gradio as gr
import logging
import dwani
import os
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG)  # DEBUG for detailed logs
logger = logging.getLogger(__name__)

# Configure dwani API settings from environment variables
dwani.api_key = os.getenv("DWANI_API_KEY")
dwani.api_base = os.getenv("DWANI_API_BASE_URL")

def translate_to_kannada(text):
    """Translate English text to Kannada using dwani.Translate.run_translate."""
    if not text or text.strip() == "":
        return ""

    start_time = time.time()
    try:
        logger.debug(f"Translating text of length {len(text)}")
        resp = dwani.Translate.run_translate(
            sentences=text,
            src_lang="english",
            tgt_lang="kannada"
        )
        elapsed = time.time() - start_time
        logger.info(f"Translation took {elapsed:.2f} seconds")

        if isinstance(resp, dict):
            translated = resp.get("translated_text")
            if translated:
                return translated.strip()
            if "translations" in resp and isinstance(resp["translations"], list):
                return " ".join(t.strip() for t in resp["translations"] if isinstance(t, str))
            return str(resp).strip()
        elif isinstance(resp, str):
            return resp.strip()
        else:
            return str(resp).strip()
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return f"Translation error: {e}"

def process_pdf(pdf_file):
    logger.debug("Received inputs - PDF: %s", pdf_file)
    overall_start = time.time()

    if not pdf_file:
        logger.error("No PDF file provided")
        return None

    file_path = pdf_file.name if hasattr(pdf_file, 'name') else pdf_file
    pages = {1, 2}
    src_lang_code = "eng_Latn"
    tgt_lang_code = "kan_Knda"

    results = {}
    extraction_start = time.time()
    for page_number in pages:
        try:
            result = dwani.Documents.run_extract(
                file_path=file_path,
                page_number=page_number,
                src_lang=src_lang_code,
                tgt_lang=tgt_lang_code
            )
            page_data = None
            for p in result.get('pages', []):
                if p.get('processed_page') == page_number:
                    page_data = p
                    break

            if page_data is None:
                results[f"Page {page_number}"] = {"error": "No data returned for this page"}
                continue

            results[f"Page {page_number}"] = {
                "Original Text": page_data.get("page_content", "N/A"),
                "Response": ""
            }
        except dwani.exceptions.DwaniAPIError as e:
            logger.error(f"Dhwani API error on page {page_number}: {str(e)}")
            results[f"Page {page_number}"] = {"error": f"API error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error on page {page_number}: {str(e)}")
            results[f"Page {page_number}"] = {"error": f"Unexpected error: {str(e)}"}
    extraction_elapsed = time.time() - extraction_start
    logger.info(f"Extraction from PDF took {extraction_elapsed:.2f} seconds")

    extraction_text_start = time.time()
    contact_en = extract_contact_details(results)
    objective_en = extract_objective(results)
    education_en = extract_education_details(results)
    work_experience_en = extract_workexperience_details(results)
    skills_en = extract_skill(results)
    certifications_en = extract_certifications(results)
    extraction_text_elapsed = time.time() - extraction_text_start
    logger.info(f"Section extraction took {extraction_text_elapsed:.2f} seconds")

    # Translate each section individually to avoid marker issues
    translation_start = time.time()
    contact_kan = translate_to_kannada(contact_en)
    objective_kan = translate_to_kannada(objective_en)
    education_kan = translate_to_kannada(education_en)
    work_experience_kan = translate_to_kannada(work_experience_en)
    skills_kan = translate_to_kannada(skills_en)
    certifications_kan = translate_to_kannada(certifications_en)
    translation_elapsed = time.time() - translation_start
    logger.info(f"Translation of all sections took {translation_elapsed:.2f} seconds")

    # Check for translation errors
    for section_name, section_text in [
        ("Contact Details", contact_kan),
        ("Objective", objective_kan),
        ("Education", education_kan),
        ("Work Experience", work_experience_kan),
        ("Skills", skills_kan),
        ("Certifications", certifications_kan),
    ]:
        if section_text.startswith("Translation error:"):
            logger.error(f"Translation failed for section {section_name}: {section_text}")
            return None

    formatted_resume = format_resume(contact_kan, objective_kan, education_kan, work_experience_kan, skills_kan, certifications_kan)

    text_filename = "resume.txt"
    with open(text_filename, "w", encoding="utf-8") as f:
        f.write(formatted_resume)

    overall_elapsed = time.time() - overall_start
    logger.info(f"Total process_pdf runtime: {overall_elapsed:.2f} seconds")

    return text_filename

def extract_text_from_response(chat_response):
    if isinstance(chat_response, dict):
        for key in ("text", "response", "content"):
            if key in chat_response and isinstance(chat_response[key], str):
                return chat_response[key]
        return str(chat_response)
    elif isinstance(chat_response, str):
        return chat_response
    else:
        return str(chat_response)

def extract_contact_details(extracted_resume):
    resume_str = str(extracted_resume)
    prompt = resume_str + " return only contact details from the resume "
    response = dwani.Chat.direct(prompt=prompt, model="gemma3")
    return extract_text_from_response(response)

def extract_objective(extracted_resume):
    resume_str = str(extracted_resume)
    prompt = resume_str + " return only objective or professional summary from the resume "
    response = dwani.Chat.direct(prompt=prompt, model="gemma3")
    return extract_text_from_response(response)

def extract_education_details(extracted_resume):
    resume_str = str(extracted_resume)
    prompt = resume_str + " return only education details from the resume "
    response = dwani.Chat.direct(prompt=prompt, model="gemma3")
    return extract_text_from_response(response)

def extract_workexperience_details(extracted_resume):
    resume_str = str(extracted_resume)
    prompt = resume_str + " return only work experience from the resume "
    response = dwani.Chat.direct(prompt=prompt, model="gemma3")
    return extract_text_from_response(response)

def extract_skill(extracted_resume):
    resume_str = str(extracted_resume)
    prompt = resume_str + " return only skills from the resume "
    response = dwani.Chat.direct(prompt=prompt, model="gemma3")
    return extract_text_from_response(response)

def extract_certifications(extracted_resume):
    resume_str = str(extracted_resume)
    prompt = resume_str + " return only certifications from the resume "
    response = dwani.Chat.direct(prompt=prompt, model="gemma3")
    return extract_text_from_response(response)

def safe_strip(value):
    if isinstance(value, dict):
        value = extract_text_from_response(value)
    return str(value).strip()

def format_resume(contact, objective, education, work_experience, skills, certifications):
    return f"""# Resume (Kannada)

## ಸಂಪರ್ಕ ವಿವರಗಳು (Contact Details)
{safe_strip(contact)}

## ಉದ್ದೇಶ (Objective)
{safe_strip(objective)}

## ಶಿಕ್ಷಣ (Education)
{safe_strip(education)}

## ಕೆಲಸದ ಅನುಭವ (Work Experience)
{safe_strip(work_experience)}

## ಕೌಶಲ್ಯಗಳು (Skills)
{safe_strip(skills)}

## ಪ್ರಮಾಣಪತ್ರಗಳು (Certifications)
{safe_strip(certifications)}
"""

with gr.Blocks(title="Resume Translator with Kannada Translation") as resume_translator:
    gr.Markdown("# Resume Upload")
    gr.Markdown("Upload a Resume PDF to extract, translate to Kannada, and download.")

    with gr.Row():
        with gr.Column():
            pdf_input = gr.File(label="Upload Resume", file_types=[".pdf"])
            submit_btn = gr.Button("Process")

        with gr.Column():
            text_output = gr.File(label="Download Formatted Resume (.txt)")

    submit_btn.click(
        fn=process_pdf,
        inputs=[pdf_input],
        outputs=text_output,
        show_progress=False  # Disable processing spinner
    )

if __name__ == "__main__":
    resume_translator.launch()
