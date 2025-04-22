import gradio as gr
import requests
import mimetypes
import tempfile
import base64
import os
from pdf2image import convert_from_path
from io import BytesIO

API_URL = "http://209.20.158.215:7860/v1/visual_query/?src_lang=eng_Latn&tgt_lang=kan_Knda"

def render_pdf_to_base64png(pdf_path, page_number, target_longest_image_dim=1024):
    """
    Render a specific PDF page to a base64-encoded PNG image string.

    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int): 1-based page number to render.
        target_longest_image_dim (int): Max dimension (width or height) of output image.

    Returns:
        str: Base64 PNG image string without header.
    """
    images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number)
    if not images:
        raise ValueError(f"Page {page_number} not found in PDF.")

    img = images[0]

    max_dim = max(img.width, img.height)
    if max_dim > target_longest_image_dim:
        scale = target_longest_image_dim / max_dim
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size)

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    base64_str = base64.b64encode(img_bytes).decode("utf-8")
    return base64_str

def process_pdf(pdf_path, page_number):
    """
    Extract text from a PDF page by rendering page to image and querying the visual API.
    """
    try:
        image_base64 = render_pdf_to_base64png(pdf_path, page_number)
    except Exception as e:
        return f"❌ Failed to render PDF page {page_number}: {str(e)}"

    try:
        image_bytes = base64.b64decode(image_base64)
    except Exception as e:
        return f"❌ Failed to decode rendered image: {str(e)}"

    files = {
        "file": ("page.png", image_bytes, "image/png")
    }
    data = {
        "query": "describe the image",
        "src_lang": "eng_Latn",
        "tgt_lang": "eng_Latn"
    }
    headers = {"accept": "application/json"}

    try:
        response = requests.post(API_URL, headers=headers, files=files, data=data)
        response.raise_for_status()
        resp_json = response.json()
        page_content = resp_json.get("answer") or resp_json.get("result") or resp_json.get("text") or ""
        if not page_content:
            return f"❌ No text extracted from PDF page {page_number}."
        return f"✅ PDF Page {page_number}:\n{page_content}"
    except Exception as e:
        return f"❌ Visual query API request failed for PDF page {page_number}: {str(e)}"

def process_image(image_path, filename):
    """
    Extract text from an image file by sending it directly to the visual query API.
    """
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type or not mime_type.startswith("image/"):
        return f"❌ {filename}: Unsupported image file type"

    try:
        with open(image_path, "rb") as f:
            files_param = {"file": (filename, f, mime_type)}
            data_param = {
                "query": "describe the image",
                "src_lang": "eng_Latn",
                "tgt_lang": "eng_Latn"
            }
            response = requests.post(
                API_URL,
                files=files_param,
                data=data_param,
                headers={"accept": "application/json"}
            )
            if response.status_code == 200:
                resp_json = response.json()
                extracted_text = resp_json.get("answer") or resp_json.get("result") or resp_json.get("text") or ""
                if not extracted_text:
                    return f"❌ {filename}: No text extracted from image."
                return f"✅ {filename}:\n{extracted_text}"
            else:
                return f"❌ {filename}: API Error ({response.status_code})"
    except Exception as e:
        return f"❌ {filename}: {str(e)}"

def ocr_from_files(files, page_number):
    """
    Main function to handle multiple files and extract text.
    For PDFs, extract from specified page.
    For images, send directly.
    """
    if not files:
        return "❌ No files uploaded."

    results = []
    for file_obj in files:
        # Gradio v5: file_obj is a NamedString or similar, use .name (file path)
        file_path = file_obj.name if hasattr(file_obj, "name") else file_obj
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
