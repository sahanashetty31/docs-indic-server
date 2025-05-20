import gradio as gr
import requests
import mimetypes
import os

# Load the text extraction API URL from environment variable
TEXT_EXTRACTION_API_URL = os.environ.get("TEXT_EXTRACTION_API_URL")
if not TEXT_EXTRACTION_API_URL:
    raise EnvironmentError(
        "Environment variable TEXT_EXTRACTION_API_URL is not set. "
        "Please set it to the API endpoint URL."
    )

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

        # Check HTTP status
        response.raise_for_status()

        # Check if response content is empty
        if not response.content:
            raise ValueError("Empty response from text extraction API")

        # Try to parse JSON safely
        try:
            resp_json = response.json()
        except ValueError:
            # Response is not valid JSON
            raise ValueError(f"Invalid JSON response: {response.text}")

        text = resp_json.get("text") or resp_json.get("page_content")
        if not text:
            raise ValueError(f"No text found in API response: {resp_json}")
        return text.strip()


def process_pdf(pdf_path, page_number):
    try:
        extracted_text = call_text_extraction_api(pdf_path, page_number)
        # Split the text into lines
        lines = extracted_text.split('\n')
        # Format lines with line numbers and skip empty lines
        formatted_lines = "\n".join(f"{idx + 1}. {line}" for idx, line in enumerate(lines) if line.strip())
        return f"✅ {os.path.basename(pdf_path)} - Page {page_number}:\n{formatted_lines}"
    except Exception as e:
        return f"❌ {os.path.basename(pdf_path)} - Text extraction API error: {e}"

def process_image(image_path, filename):
    # Placeholder for image processing; extend if needed
    return f"❌ {filename} - Image processing not implemented with new API."

def ocr_from_files(files, page_number):
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
            result = process_pdf(file_path, page_number)
        else:
            result = process_image(file_path, filename)
        results.append(result)

    return "\n\n".join(results)

with gr.Blocks() as demo:
    gr.Markdown("## Browse & OCR Extract PDFs/Images (Batch)")

    with gr.Row():
        file_input = gr.File(
            label="Upload Files",
            file_types=[".pdf", ".png", ".jpg", ".jpeg", ".webp"],
            file_count="multiple"
        )
        page_number_input = gr.Number(
            label="PDF Page Number (for PDFs)",
            value=1,
            precision=0,
            minimum=1,
            interactive=True
        )

    output_text = gr.Textbox(
        label="Extracted Text Results",
        interactive=False,
        lines=15,
        placeholder="OCR results will appear here..."
    )

    submit_btn = gr.Button("Extract Text")
    submit_btn.click(
        ocr_from_files,
        inputs=[file_input, page_number_input],
        outputs=output_text
    )

if __name__ == "__main__":
    demo.launch()
