import gradio as gr
import os
import tempfile
import dwani
import logging
import json
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure dwani API settings
dwani.api_key = os.getenv("DWANI_API_KEY")
dwani.api_base = os.getenv("DWANI_API_BASE_URL")

# Log API configuration for debugging
logger.debug("DWANI_API_KEY: %s", "Set" if dwani.api_key else "Not set")
logger.debug("DWANI_API_BASE_URL: %s", dwani.api_base)

# Language options for dropdown (display name and code)
language_options = [
    ("English", "eng_Latn"),
    ("Kannada", "kan_Knda"),
    ("Hindi", "hin_Deva")
]

# Create list for Gradio dropdown (display names only)
language_names = [lang[0] for lang in language_options]

# Map display names to language codes
lang_code_map = {lang[0]: lang[1] for lang in language_options}


def parse_page_numbers(pages_str):
    """
    Parse a string of comma-separated page numbers/ranges into a sorted list of unique integers.
    Example inputs:
        "1,3,5"
        "1-3,5"
    """
    pages = set()
    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                if start > end or start < 1:
                    continue
                pages.update(range(start, end + 1))
            except ValueError:
                continue
        else:
            try:
                page = int(part)
                if page >= 1:
                    pages.add(page)
            except ValueError:
                continue
    return sorted(pages)


def extract_contact_details(text):
    """
    Fallback extraction of emails and phone numbers using regex.
    Returns a dict with lists of emails and phones.
    """
    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    PHONE_REGEX = re.compile(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?){1,2}\d{4}")

    emails = EMAIL_REGEX.findall(text)
    phones = PHONE_REGEX.findall(text)

    phones_flat = []
    for match in phones:
        phone = ''.join(part for part in match if part).strip()
        if phone:
            phones_flat.append(phone)

    return {
        "emails": list(set(emails)),
        "phone_numbers": list(set(phones_flat))
    }


def results_to_markdown(results):
    """
    Convert the results dictionary into a Markdown formatted string.
    """
    md_lines = []
    for page, content in results.items():
        md_lines.append(f"## {page}\n")
        if "error" in content:
            md_lines.append(f"**Error:** {content['error']}\n")
        else:
            md_lines.append("**Original Text:**\n\n```")
            md_lines.append(content.get('Original Text', '') + "\n")
            md_lines.append("```\n")

            warnings = content.get("Warnings", [])
            if warnings:
                md_lines.append("**Warnings:**\n")
                for w in warnings:
                    md_lines.append(f"- {w}\n")
                md_lines.append("\n")

            contacts = content.get("Extracted Contacts", {})
            emails = contacts.get("emails", [])
            phones = contacts.get("phone_numbers", [])

            md_lines.append("**Extracted Contact Details:**\n")
            md_lines.append(f"- Emails: {', '.join(emails) if emails else 'None found'}\n")
            md_lines.append(f"- Phone Numbers: {', '.join(phones) if phones else 'None found'}\n")

            md_lines.append("**Processed Page:** " + str(content.get('Processed Page', '')) + "\n")

        md_lines.append("\n---\n")
    return "\n".join(md_lines)


def process_pdf(pdf_file, pages_str, src_lang):
    logger.debug("Received inputs - PDF: %s, Pages: %s, Source Lang: %s",
                 pdf_file, pages_str, src_lang)

    # Validate inputs
    if not pdf_file:
        logger.error("No PDF file provided")
        return "Error: Please upload a PDF file", None

    pages = parse_page_numbers(pages_str)
    if not pages:
        logger.error("Invalid or empty page numbers input: %s", pages_str)
        return "Error: Please provide valid page numbers (e.g., 1,3,5 or 1-3)", None

    src_lang_code = lang_code_map.get(src_lang)
    if not src_lang_code:
        logger.error("Invalid source language selection: %s", src_lang)
        return "Error: Invalid source language selection", None

    file_path = pdf_file.name if hasattr(pdf_file, 'name') else pdf_file

    results = {}
    all_contacts = {}

    for page_number in pages:
        try:
            # Extract text using Documents API
            extraction_result = dwani.Documents.run_extract(
                file_path=file_path,
                page_number=page_number,
                src_lang=src_lang_code
            )
            logger.debug("Text extraction response for page %d: %s", page_number, extraction_result)

            page_data = None
            for p in extraction_result.get('pages', []):
                if p.get('processed_page') == page_number:
                    page_data = p
                    break

            if page_data is None:
                results[f"Page {page_number}"] = {"error": "No data returned for this page"}
                continue

            text_content = page_data.get("page_content", "")

            # Prepare prompt with truncation to meet 1000 char limit
            fixed_prompt = (
                "Extract all contact details from the following text. Return ONLY a JSON object with two keys: "
                "'emails' (list of email strings) and 'phone_numbers' (list of phone number strings). "
                "If no contacts found, return empty lists. Text:\n\n"
            )
            max_text_length = 1000 - len(fixed_prompt)
            text_truncated = text_content[:max_text_length]
            chat_prompt = fixed_prompt + text_truncated

            # Initialize warnings list for this page
            warnings = []

            if len(text_content) > max_text_length:
                warnings.append(f"Text truncated to first {max_text_length} characters for API compliance")

            # Call Chat API
            chat_response = dwani.Chat.direct(
                prompt=chat_prompt,
                model="gemma3"
            )
            logger.debug("Chat API response for page %d: %s", page_number, chat_response)

            # Handle response (already a dict)
            if isinstance(chat_response, dict) and "emails" in chat_response and "phone_numbers" in chat_response:
                contacts = chat_response
            else:
                logger.warning("Unexpected response format, using regex fallback")
                contacts = extract_contact_details(text_content)

            all_contacts[f"Page_{page_number}"] = contacts
            results[f"Page {page_number}"] = {
                "Processed Page": page_data.get("processed_page", "N/A"),
                "Original Text": text_content,
                "Extracted Contacts": contacts,
                "Warnings": warnings
            }

        except dwani.exceptions.DwaniAPIError as e:
            logger.error("Dhwani API error on page %d: %s", page_number, str(e))
            results[f"Page {page_number}"] = {"error": f"API error: {str(e)}"}
        except Exception as e:
            logger.error("Unexpected error on page %d: %s", page_number, str(e))
            results[f"Page {page_number}"] = {"error": f"Unexpected error: {str(e)}"}

    # Save contacts to JSON file
    temp_json_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w', encoding='utf-8')
    json.dump(all_contacts, temp_json_file, indent=4)
    temp_json_file.close()

    # Convert results to markdown for display
    markdown_text = results_to_markdown(results)

    return markdown_text, temp_json_file.name


# Define Gradio interface
with gr.Blocks(title="PDF Contact Extractor") as demo:
    gr.Markdown("# PDF Contact Information Extractor")
    gr.Markdown("Upload a PDF and specify page numbers to extract contact information")

    with gr.Row():
        with gr.Column():
            pdf_input = gr.File(label="Upload PDF", file_types=[".pdf"])
            pages_input = gr.Textbox(
                label="Page Numbers",
                placeholder="e.g., 1,3,5 or 1-3",
                value="1",
                lines=1
            )
            src_lang_input = gr.Dropdown(
                label="Source Language",
                choices=language_names,
                value="English"
            )
            submit_btn = gr.Button("Extract Contacts")

        with gr.Column():
            output_md = gr.Markdown(label="Extraction Results")
            download_json = gr.File(label="Download Contacts (JSON)")

    submit_btn.click(
        fn=process_pdf,
        inputs=[pdf_input, pages_input, src_lang_input],
        outputs=[output_md, download_json]
    )


# Launch the interface
if __name__ == "__main__":
    if not dwani.api_key or not dwani.api_base:
        logger.error("API key or base URL not set. Please set DWANI_API_KEY and DWANI_API_BASE_URL environment variables.")
        print("Error: Please set DWANI_API_KEY and DWANI_API_BASE_URL environment variables.")
    else:
        logger.debug("Starting Gradio interface...")
        demo.launch()
