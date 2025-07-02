import gradio as gr
import os
import tempfile
import dwani
import logging
import json
import re
from pathlib import Path

# Optional: for DOCX extraction
try:
    import docx
except ImportError:
    docx = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Dwani API
dwani.api_key = os.getenv("DWANI_API_KEY")
dwani.api_base = os.getenv("DWANI_API_BASE_URL")

language_options = [
    ("English", "eng_Latn"),
    ("Kannada", "kan_Knda"),
    ("Hindi", "hin_Deva"),
]
language_names = [lang[0] for lang in language_options]
lang_code_map = {lang[0]: lang[1] for lang in language_options}


def parse_page_numbers(pages_str):
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


def extract_text_from_docx(file_path):
    if not docx:
        logger.error("python-docx is not installed. Cannot process DOCX files.")
        return ""
    try:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        logger.error(f"Error reading DOCX file: {e}")
        return ""


def extract_text_from_txt(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading TXT file: {e}")
        return ""


def extract_name_from_text(text):
    # Look for lines with 2-3 capitalized words anywhere in the first 10 lines
    lines = text.strip().splitlines()[:10]
    for line in lines:
        words = line.strip().split()
        if 2 <= len(words) <= 3 and all(w.istitle() for w in words):
            return " ".join(words)
    return ""


def clean_phone_numbers(phone_list):
    cleaned = []
    for phone in phone_list:
        digits = re.sub(r"\D", "", phone)
        if len(digits) >= 7:
            cleaned.append(phone.strip())
    return list(set(cleaned))


def extract_contact_details_regex(text):
    name = extract_name_from_text(text)

    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    PHONE_REGEX = re.compile(
        r"(\+?\d{1,3}[\s-]?)?(\(?\d{2,4}\)?[\s-]?)?[\d\s-]{7,15}"
    )
    ADDRESS_REGEX = re.compile(
        r"\d{1,5}\s+\w+(\s+\w+)*,?\s*\w+(\s+\w+)*,?\s*[A-Za-z]{2,}\s*\d{5}(-\d{4})?",
        re.IGNORECASE,
    )

    emails = EMAIL_REGEX.findall(text)
    phones = PHONE_REGEX.findall(text)
    phones_flat = []
    for match in phones:
        phone = "".join(part for part in match if part).strip()
        if phone:
            phones_flat.append(phone)
    phones_flat = clean_phone_numbers(phones_flat)

    addresses = ADDRESS_REGEX.findall(text)
    addresses_flat = []
    for addr in addresses:
        if isinstance(addr, tuple):
            addresses_flat.append("".join(addr).strip())
        else:
            addresses_flat.append(addr.strip())

    return {
        "name": name,
        "emails": list(set(emails)),
        "phone_numbers": phones_flat,
        "addresses": list(set(addresses_flat)),
    }


def try_parse_json_from_string(s):
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        # Extract JSON substring using regex
        json_matches = re.findall(r"\{.*?\}", s, re.DOTALL)
        for match in json_matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
    return None


def results_to_markdown(results):
    md_lines = []
    for page, content in results.items():
        md_lines.append(f"## {page}\n")
        if "error" in content:
            md_lines.append(f"**Error:** {content['error']}\n")
        else:
            warnings = content.get("Warnings", [])
            if warnings:
                md_lines.append("**Warnings:**\n")
                for w in warnings:
                    md_lines.append(f"- {w}\n")
                md_lines.append("\n")

            contacts = content.get("Extracted Contacts", {})
            name = contacts.get("name", "")
            emails = contacts.get("emails", [])
            phones = contacts.get("phone_numbers", [])
            addresses = contacts.get("addresses", [])

            md_lines.append("**Extracted Contact Details:**\n")
            md_lines.append(f"- Name: {name if name else 'None found'}\n")
            md_lines.append(f"- Emails: {', '.join(emails) if emails else 'None found'}\n")
            md_lines.append(f"- Phone Numbers: {', '.join(phones) if phones else 'None found'}\n")
            md_lines.append(f"- Addresses: {', '.join(addresses) if addresses else 'None found'}\n")

        md_lines.append("\n---\n")
    return "\n".join(md_lines)


def process_document(file_obj, pages_str, src_lang):
    logger.debug(f"Received inputs - File: {file_obj}, Pages: {pages_str}, Source Lang: {src_lang}")

    if not file_obj:
        logger.error("No file provided")
        return "Error: Please upload a document file", None

    file_path = file_obj.name if hasattr(file_obj, "name") else file_obj
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        pages = parse_page_numbers(pages_str)
        if not pages:
            logger.error(f"Invalid or empty page numbers input: {pages_str}")
            return "Error: Please provide valid page numbers (e.g., 1,3,5 or 1-3)", None
    else:
        pages = [1]  # For non-PDF, treat whole document as single page

    src_lang_code = lang_code_map.get(src_lang)
    if not src_lang_code:
        logger.error(f"Invalid source language selection: {src_lang}")
        return "Error: Invalid source language selection", None

    results = {}
    all_contacts = {}

    if ext == ".pdf":
        for page_number in pages:
            try:
                extraction_result = dwani.Documents.run_extract(
                    file_path=file_path, page_number=page_number, src_lang=src_lang_code
                )
                logger.debug(f"Text extraction response for page {page_number}: {extraction_result}")

                page_data = None
                for p in extraction_result.get("pages", []):
                    if p.get("processed_page") == page_number:
                        page_data = p
                        break

                if page_data is None:
                    results[f"Page {page_number}"] = {"error": "No data returned for this page"}
                    continue

                text_content = page_data.get("page_content", "")

                fixed_prompt = (
                    "Extract only contact details (name, emails, phone numbers, addresses) from the following text. "
                    "Return ONLY a JSON object with keys: 'name', 'emails', 'phone_numbers', and 'addresses' as lists or string. "
                    "If none found, return empty strings or lists. Text:\n\n"
                )
                max_text_length = 1000 - len(fixed_prompt)
                text_truncated = text_content[:max_text_length]
                chat_prompt = fixed_prompt + text_truncated

                warnings = []
                if len(text_content) > max_text_length:
                    warnings.append(f"Text truncated to first {max_text_length} characters for API compliance")

                chat_response = dwani.Chat.direct(prompt=chat_prompt, model="gemma3")
                logger.debug(f"Raw Chat API response for page {page_number}: {repr(chat_response)}")

                contacts = None
                if isinstance(chat_response, dict):
                    if all(k in chat_response for k in ("name", "emails", "phone_numbers", "addresses")):
                        contacts = chat_response
                elif isinstance(chat_response, str):
                    contacts = try_parse_json_from_string(chat_response)

                if not contacts or not isinstance(contacts, dict) or any(
                    k not in contacts for k in ("name", "emails", "phone_numbers", "addresses")
                ):
                    logger.warning("Unexpected response format or missing keys, using regex fallback")
                    contacts = extract_contact_details_regex(text_content)

                all_contacts[f"Page_{page_number}"] = contacts
                results[f"Page {page_number}"] = {
                    "Extracted Contacts": contacts,
                    "Warnings": warnings,
                }

            except dwani.exceptions.DwaniAPIError as e:
                logger.error(f"Dhwani API error on page {page_number}: {e}")
                results[f"Page {page_number}"] = {"error": f"API error: {str(e)}"}
            except Exception as e:
                logger.error(f"Unexpected error on page {page_number}: {e}")
                results[f"Page {page_number}"] = {"error": f"Unexpected error: {str(e)}"}

    elif ext == ".docx":
        text_content = extract_text_from_docx(file_path)
        if not text_content:
            return "Error: Unable to extract text from DOCX file", None

        fixed_prompt = (
            "Extract only contact details (name, emails, phone numbers, addresses) from the following text. "
            "Return ONLY a JSON object with keys: 'name', 'emails', 'phone_numbers', and 'addresses' as lists or string. "
            "If none found, return empty strings or lists. Text:\n\n"
        )
        max_text_length = 1000 - len(fixed_prompt)
        text_truncated = text_content[:max_text_length]
        chat_prompt = fixed_prompt + text_truncated

        warnings = []
        if len(text_content) > max_text_length:
            warnings.append(f"Text truncated to first {max_text_length} characters for API compliance")

        try:
            chat_response = dwani.Chat.direct(prompt=chat_prompt, model="gemma3")
            logger.debug(f"Raw Chat API response for DOCX: {repr(chat_response)}")

            contacts = None
            if isinstance(chat_response, dict):
                if all(k in chat_response for k in ("name", "emails", "phone_numbers", "addresses")):
                    contacts = chat_response
            elif isinstance(chat_response, str):
                contacts = try_parse_json_from_string(chat_response)

            if not contacts or not isinstance(contacts, dict) or any(
                k not in contacts for k in ("name", "emails", "phone_numbers", "addresses")
            ):
                logger.warning("Unexpected response format or missing keys, using regex fallback")
                contacts = extract_contact_details_regex(text_content)

            all_contacts["Document"] = contacts
            results["Document"] = {
                "Extracted Contacts": contacts,
                "Warnings": warnings,
            }

        except Exception as e:
            logger.error(f"Error during Chat API call for DOCX: {e}")
            return f"Error during contact extraction: {e}", None

    elif ext == ".txt":
        text_content = extract_text_from_txt(file_path)
        if not text_content:
            return "Error: Unable to extract text from TXT file", None

        fixed_prompt = (
            "Extract only contact details (name, emails, phone numbers, addresses) from the following text. "
            "Return ONLY a JSON object with keys: 'name', 'emails', 'phone_numbers', and 'addresses' as lists or string. "
            "If none found, return empty strings or lists. Text:\n\n"
        )
        max_text_length = 1000 - len(fixed_prompt)
        text_truncated = text_content[:max_text_length]
        chat_prompt = fixed_prompt + text_truncated

        warnings = []
        if len(text_content) > max_text_length:
            warnings.append(f"Text truncated to first {max_text_length} characters for API compliance")

        try:
            chat_response = dwani.Chat.direct(prompt=chat_prompt, model="gemma3")
            logger.debug(f"Raw Chat API response for TXT: {repr(chat_response)}")

            contacts = None
            if isinstance(chat_response, dict):
                if all(k in chat_response for k in ("name", "emails", "phone_numbers", "addresses")):
                    contacts = chat_response
            elif isinstance(chat_response, str):
                contacts = try_parse_json_from_string(chat_response)

            if not contacts or not isinstance(contacts, dict) or any(
                k not in contacts for k in ("name", "emails", "phone_numbers", "addresses")
            ):
                logger.warning("Unexpected response format or missing keys, using regex fallback")
                contacts = extract_contact_details_regex(text_content)

            all_contacts["Document"] = contacts
            results["Document"] = {
                "Extracted Contacts": contacts,
                "Warnings": warnings,
            }

        except Exception as e:
            logger.error(f"Error during Chat API call for TXT: {e}")
            return f"Error during contact extraction: {e}", None

    else:
        return f"Unsupported file type: {ext}", None

    temp_json_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8")
    json.dump(all_contacts, temp_json_file, indent=4)
    temp_json_file.close()

    markdown_text = results_to_markdown(results)

    return markdown_text, temp_json_file.name


with gr.Blocks(title="Document Contact Details Extractor") as demo:
    gr.Markdown("# Document Contact Details Extractor")
    gr.Markdown("Upload a resume or document (PDF, DOCX, TXT). Specify pages for PDFs. Extract name, email, phone, and address.")

    with gr.Row():
        with gr.Column():
            file_input = gr.File(label="Upload Document", file_types=[".pdf", ".docx", ".txt"])
            pages_input = gr.Textbox(label="Page Numbers (PDF only)", placeholder="e.g., 1,3,5 or 1-3", value="1", lines=1)
            src_lang_input = gr.Dropdown(label="Source Language", choices=language_names, value="English")
            submit_btn = gr.Button("Extract Contact Details")

        with gr.Column():
            output_md = gr.Markdown(label="Extracted Contact Details")
            download_json = gr.File(label="Download Extracted Contacts (JSON)")

    submit_btn.click(fn=process_document, inputs=[file_input, pages_input, src_lang_input], outputs=[output_md, download_json])


if __name__ == "__main__":
    if not dwani.api_key or not dwani.api_base:
        logger.error("API key or base URL not set. Please set DWANI_API_KEY and DWANI_API_BASE_URL environment variables.")
        print("Error: Please set DWANI_API_KEY and DWANI_API_BASE_URL environment variables.")
    else:
        logger.debug("Starting Gradio interface...")
        demo.launch()
