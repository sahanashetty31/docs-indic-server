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

def call_text_extraction_api(pdf_path, page_number, src_lang="eng_Latn", tgt_lang="eng_Latn", prompt="describe the image"):
    """
    Call the PDF text extraction API with multipart/form-data as per the curl command.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File {pdf_path} does not exist")

    with open(pdf_path, "rb") as f:
        files = {
            "file": (os.path.basename(pdf_path), f, "application/pdf")
        }
        data = {
            "page_number": str(page_number),
            "src_lang": src_lang,
            "tgt_lang": tgt_lang,
            "prompt": prompt
        }
        headers = {
            "accept": "application/json"
        }
        response = requests.post(TEXT_EXTRACTION_API_URL, headers=headers, files=files, data=data, timeout=60)
        response.raise_for_status()
        resp_json = response.json()

        # Accept 'text' or 'page_content' as the extracted text key
        text = resp_json.get("text") or resp_json.get("page_content")
        if not text:
            raise ValueError(f"No text found in API response: {resp_json}")
        return text.strip()

def process_pdf(pdf_path, page_number):
    try:
        extracted_text = call_text_extraction_api(pdf_path, page_number)
        return f"✅ {os.path.basename(pdf_path)} - Page {page_number}:\n{extracted_text}"
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
