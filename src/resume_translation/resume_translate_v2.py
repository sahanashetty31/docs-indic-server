import gradio as gr
import logging
import dwani
import os
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure dwani API settings from environment variables
dwani.api_key = os.getenv("DWANI_API_KEY")
dwani.api_base = os.getenv("DWANI_API_BASE_URL")


def process_pdf(pdf_file):
    logger.debug("Received inputs - PDF: %s", pdf_file)

    if not pdf_file:
        logger.error("No PDF file provided")
        return {}, None

    file_path = pdf_file.name if hasattr(pdf_file, 'name') else pdf_file
    pages = {1, 2, 3, 4}
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

    # Extract resume sections
    contact = extract_contact_details(results)
    objective = extract_objective(results)
    education = extract_education_details(results)
    work_experience = extract_workexperience_details(results)
    skills = extract_skill(results)
    certifications = extract_certifications(results)

    # Prepare JSON response dict
    json_response = {
        "Contact Details": contact,
        "Objective": objective,
        "Education": education,
        "Work Experience": work_experience,
        "Skills": skills,
        "Certifications": certifications
    }

    # Format resume text
    formatted_resume = format_resume(contact, objective, education, work_experience, skills, certifications)

    # Save formatted resume text file
    text_filename = "resume.txt"
    with open(text_filename, "w", encoding="utf-8") as f:
        f.write(formatted_resume)

    # Return JSON dict for interface display and path to downloadable text file
    return json_response, text_filename


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
    return f"""# Resume

## Contact Details
{safe_strip(contact)}

## Objective
{safe_strip(objective)}

## Education
{safe_strip(education)}

## Work Experience
{safe_strip(work_experience)}

## Skills
{safe_strip(skills)}

## Certifications
{safe_strip(certifications)}
"""


# Gradio interface
with gr.Blocks(title="Resume Translator") as resume_translator:
    gr.Markdown("# Resume Upload")
    gr.Markdown("Upload a Resume PDF to extract and translate details.")

    with gr.Row():
        with gr.Column():
            pdf_input = gr.File(label="Upload Resume", file_types=[".pdf"])
            submit_btn = gr.Button("Process")

        with gr.Column():
            json_output = gr.JSON(label="Extracted Resume Data (JSON)")
            text_output = gr.File(label="Download Formatted Resume (.txt)")

    submit_btn.click(
        fn=process_pdf,
        inputs=[pdf_input],
        outputs=[json_output, text_output]
    )


if __name__ == "__main__":
    resume_translator.launch()
