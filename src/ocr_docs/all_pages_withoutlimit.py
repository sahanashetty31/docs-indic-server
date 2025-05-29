import gradio as gr
import os
import dwani
import logging
from PyPDF2 import PdfReader

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Dwani API settings from environment variables
dwani.api_key = os.getenv("DWANI_API_KEY")
dwani.api_base = os.getenv("DWANI_API_BASE_URL")

if not dwani.api_key or not dwani.api_base:
    logger.error("DWANI_API_KEY and DWANI_API_BASE_URL must be set as environment variables.")

# Language options for dropdowns (display name and corresponding Dwani language code)
language_options = [
    ("English", "eng_Latn"),
    ("Kannada", "kan_Knda"),
    ("Hindi", "hin_Deva")
]
language_names = [lang[0] for lang in language_options]
lang_code_map = {lang[0]: lang[1] for lang in language_options}

def get_pdf_page_count(pdf_path):
    """Return the number of pages in the PDF."""
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        raise ValueError(f"Could not read PDF file to get page count: {e}")

def process_pdf_with_dwani(pdf_file, page_number, prompt, src_lang, tgt_lang):
    """
    Process the given PDF file page with Dwani API using custom prompt and language options.
    Returns a dict with API response or error message.
    """
    logger.info(f"Processing PDF: {pdf_file}, Page: {page_number}, Prompt: {prompt}, SrcLang: {src_lang}, TgtLang: {tgt_lang}")

    if not pdf_file:
        return {"error": "Please upload a PDF file."}
    if not prompt.strip():
        return {"error": "Please provide a non-empty prompt."}

    # Validate page number
    try:
        page_number = int(page_number)
        if page_number < 1:
            return {"error": "Page number must be at least 1."}
    except Exception:
        return {"error": "Page number must be a positive integer."}

    # Map language names to codes
    src_lang_code = lang_code_map.get(src_lang)
    tgt_lang_code = lang_code_map.get(tgt_lang)
    if not src_lang_code or not tgt_lang_code:
        return {"error": "Invalid source or target language selection."}

    # Get the actual file path from Gradio File object
    file_path = getattr(pdf_file, "name", None)
    if not file_path or not os.path.exists(file_path):
        return {"error": "Uploaded file not accessible."}

    # Check if page number is within PDF page count
    try:
        total_pages = get_pdf_page_count(file_path)
        if page_number > total_pages:
            return {"error": f"Page number {page_number} exceeds total pages {total_pages}."}
    except Exception as e:
        return {"error": f"Error reading PDF: {e}"}

    # Call Dwani API to process the document page
    try:
        result = dwani.Documents.run_doc_query(
            file_path=file_path,
            prompt=prompt,
            page_number=page_number,
            src_lang=src_lang_code,
            tgt_lang=tgt_lang_code
        )
        logger.info("Dwani API call successful")
        return {
            "Original Text": result.get("original_text", "N/A"),
            "Response": result.get("response", "N/A"),
            "Processed Page": result.get("processed_page", "N/A"),
            "Translated Response": result.get("translated_response", "N/A")
        }
    except dwani.exceptions.DhwaniAPIError as e:
        logger.error(f"Dhwani API error: {e}")
        return {"error": f"API error: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": f"Unexpected error: {str(e)}"}

# Gradio UI setup
with gr.Blocks(title="PDF Custom Prompt Processor with Dwani API") as demo:
    gr.Markdown("# PDF Custom Prompt Processor")
    gr.Markdown("Upload a PDF, specify a page number, enter a prompt, and select source and target languages.")

    with gr.Row():
        with gr.Column():
            pdf_input = gr.File(label="Upload PDF", file_types=[".pdf"])
            page_number = gr.Number(label="Page Number", value=1, minimum=1, precision=0)
            prompt = gr.Textbox(
                label="Custom Prompt",
                placeholder="e.g., List the key points",
                value="List the key points",
                lines=3
            )
            src_lang_input = gr.Dropdown(
                label="Source Language",
                choices=language_names,
                value="English"
            )
            tgt_lang_input = gr.Dropdown(
                label="Target Language",
                choices=language_names,
                value="Kannada"
            )
            submit_btn = gr.Button("Process")

        with gr.Column():
            output = gr.JSON(label="Dwani API Response")

    submit_btn.click(
        fn=process_pdf_with_dwani,
        inputs=[pdf_input, page_number, prompt, src_lang_input, tgt_lang_input],
        outputs=output
    )

if __name__ == "__main__":
    if not dwani.api_key or not dwani.api_base:
        print("Error: Please set DWANI_API_KEY and DWANI_API_BASE_URL environment variables.")
    else:
        demo.launch()
