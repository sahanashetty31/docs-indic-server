import gradio as gr
import logging
import dwani
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure dwani API settings from environment variables
dwani.api_key = os.getenv("DWANI_API_KEY")
dwani.api_base = os.getenv("DWANI_API_BASE_URL")


def translate_to_kannada(text):
    """Translate English text to Kannada using dwani.Translate.run_translate."""
    if not text or text.strip() == "":
        return ""

    try:
        resp = dwani.Translate.run_translate(
            sentences=text,
            src_lang="english",
            tgt_lang="kannada"
        )
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

    if not pdf_file:
        logger.error("No PDF file provided")
        return None

    file_path = pdf_file.name if hasattr(pdf_file, 'name') else pdf_file
    pages = {1, 2}
    src_lang_code = "eng_Latn"
    tgt_lang_code = "kan_Knda"

    results = {}
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
    extracted_details = extract_resume_sections(results)

    translation = translate_to_kannada(extracted_details)

 #   formatted_resume = format_resume(contact_kan, objective_kan, education_kan, work_experience_kan, skills_kan, certifications_kan)

    text_filename = "resume.txt"
    with open(text_filename, "w", encoding="utf-8") as f:
        f.write(translation)

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
    
def extract_resume_sections(extracted_resume):
    resume_str = str(extracted_resume)
    prompt = (
        resume_str +
        "\n\nExtract the following details from the resume:\n"
        "1. Contact details\n"
        "2. Objective or professional summary\n"
        "3. Education details\n"
        "4. Work experience\n"
        "5. Skills\n"
        "6. Certifications\n\n"
        "Return the information in a JSON format with keys: "
        "'contact_details', 'objective', 'education', 'work_experience', 'skills', 'certifications'."
    )
    response = dwani.Chat.direct(prompt=prompt, model="gemma3")
    return extract_text_from_response(response)

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
        outputs=text_output
    )

if __name__ == "__main__":
    resume_translator.launch()
