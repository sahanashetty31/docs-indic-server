import gradio as gr
import os
from PyPDF2 import PdfReader
import dwani

# Setup dwani credentials from environment variables
dwani.api_key = os.getenv("DWANI_API_KEY")
dwani.api_base = os.getenv("DWANI_API_BASE_URL")

if not dwani.api_key or not dwani.api_base:
    raise EnvironmentError(
        "Environment variables DWANI_API_KEY and DWANI_API_BASE_URL must be set."
    )

def get_pdf_page_count(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        raise ValueError(f"Could not read PDF file to get page count: {e}")

def call_text_extraction_api(pdf_path, page_number):
    try:
        # Extract text from the specific page using dwani
        response = dwani.Documents.run_extract(
            file_path=pdf_path,
            page_number=page_number,
            src_lang="eng_Latn",  # Adjust source language if needed
            tgt_lang="eng_Latn"   # Same as source if no translation required
        )
        pages = response.get("pages", [])
        if not pages:
            raise ValueError("No pages data in dwani response")

        page_content = pages[0].get("page_content")
        if not page_content:
            raise ValueError("No page_content found in dwani response")

        return page_content.strip()

    except Exception as e:
        raise ValueError(f"dwani API error: {e}")

def process_pdf(pdf_path):
    try:
        total_pages = get_pdf_page_count(pdf_path)
    except Exception as e:
        return f"❌ Error reading PDF page count: {e}"

    results = []
    for page_number in range(1, total_pages + 1):
        try:
            extracted_text = call_text_extraction_api(pdf_path, page_number)
            lines = extracted_text.split('\n')
            formatted_lines = "\n".join(f"{idx + 1}. {line}" for idx, line in enumerate(lines) if line.strip())
            results.append(f"✅ {os.path.basename(pdf_path)} - Page {page_number}:\n{formatted_lines}")
        except Exception as e:
            results.append(f"❌ {os.path.basename(pdf_path)} - Page {page_number} - Text extraction error: {e}")
    return "\n\n".join(results)

def process_image(image_path, filename):
    # Placeholder for image processing; extend if needed
    return f"❌ {filename} - Image processing not implemented with dwani API."

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
