import gradio as gr
import requests
import os
from PyPDF2 import PdfReader

# Hardcoded maximum number of pages to extract per PDF
MAX_PAGES = 3

# Load the text extraction API URL from environment variable
TEXT_EXTRACTION_API_URL = os.environ.get("TEXT_EXTRACTION_API_URL")
if not TEXT_EXTRACTION_API_URL:
    raise EnvironmentError(
        "Environment variable TEXT_EXTRACTION_API_URL is not set. "
        "Please set it to the API endpoint URL."
    )

def get_pdf_page_count(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        raise ValueError(f"Could not read PDF file to get page count: {e}")

def call_text_extraction_api(pdf_path, page_number):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File {pdf_path} does not exist")

    with open(pdf_path, "rb") as f:
        files = {
            "file": (os.path.basename(pdf_path), f, "application/pdf")
        }
        data = {
            "page_number": str(page_number)
        }
        headers = {
            "accept": "application/json"
        }
        response = requests.post(TEXT_EXTRACTION_API_URL, headers=headers, files=files, data=data, timeout=60)

        response.raise_for_status()

        if not response.content:
            raise ValueError("Empty response from text extraction API")

        try:
            resp_json = response.json()
        except ValueError:
            raise ValueError(f"Invalid JSON response: {response.text}")

        text = resp_json.get("text") or resp_json.get("page_content")
        if not text:
            raise ValueError(f"No text found in API response: {resp_json}")
        return text.strip()

def process_pdf(pdf_path):
    try:
        total_pages = get_pdf_page_count(pdf_path)
    except Exception as e:
        return f"❌ Error reading PDF page count: {e}"

    limit_pages = min(total_pages, MAX_PAGES)
    results = []
    for page_number in range(1, limit_pages + 1):
        try:
            extracted_text = call_text_extraction_api(pdf_path, page_number)
            lines = extracted_text.split('\n')
            formatted_lines = "\n".join(f"{idx + 1}. {line}" for idx, line in enumerate(lines) if line.strip())
            results.append(f"✅ {os.path.basename(pdf_path)} - Page {page_number}:\n{formatted_lines}")
        except Exception as e:
            results.append(f"❌ {os.path.basename(pdf_path)} - Page {page_number} - Text extraction API error: {e}")
    if total_pages > MAX_PAGES:
        results.append(f"\n⚠️ Note: Extracted only first {MAX_PAGES} pages out of {total_pages} total pages.")
    return "\n\n".join(results)

def process_image(image_path, filename):
    # Placeholder for image processing; extend if needed
    return f"❌ {filename} - Image processing not implemented with new API."

def ocr_from_files(files, prompt):
    if not files:
        return "❌ No files uploaded."

    results = []
    for file_obj in files:
        file_path = getattr(file_obj, "name", None)
        if not file_path or not os.path.exists(file_path):
            results.append("❌ Could not access uploaded file.")
            continue
        filename = os.path.basename(file_path)

        if filename.lower().endswith(".pdf"):
            extracted_text = process_pdf(file_path)
        else:
            extracted_text = process_image(file_path, filename)

        combined_result = f"📝 Prompt:\n{prompt}\n\n📄 Extracted Text:\n{extracted_text}"
        results.append(combined_result)

    return "\n\n---\n\n".join(results)

with gr.Blocks() as demo:
    gr.Markdown("## Browse & OCR Extract PDFs/Images (Batch)")

    with gr.Row():
        file_input = gr.File(
            label="Upload Files",
            file_types=[".pdf", ".png", ".jpg", ".jpeg", ".webp"],
            file_count="multiple"
        )

    prompt_input = gr.Textbox(
        label="Enter your prompt",
        placeholder="Enter any instructions or questions here...",
        lines=3,
        interactive=True
    )

    output_text = gr.Textbox(
        label="Extracted Text Results",
        interactive=False,
        lines=20,
        placeholder="OCR results will appear here..."
    )

    submit_btn = gr.Button("Extract Text")
    submit_btn.click(
        ocr_from_files,
        inputs=[file_input, prompt_input],
        outputs=output_text
    )

if __name__ == "__main__":
    demo.launch()
