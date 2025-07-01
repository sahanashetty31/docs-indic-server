import gradio as gr
import os
import tempfile
import dwani
import logging


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


def results_to_markdown(results):
    """
    Convert the results dictionary into a Markdown formatted string,
    without translation sections.
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

            response_text = content.get('Response', '')
            if response_text:
                md_lines.append("Response:\n\n" + response_text + "\n")

            md_lines.append("**Processed Page:** " + str(content.get('Processed Page', '')) + "\n")

        md_lines.append("\n---\n")
    return "\n".join(md_lines)


def process_pdf(pdf_file, pages_str, prompt, src_lang):
    logger.debug("Received inputs - PDF: %s, Pages: %s, Prompt: %s, Source Lang: %s",
                 pdf_file, pages_str, prompt, src_lang)


    # Validate inputs
    if not pdf_file:
        logger.error("No PDF file provided")
        return "Error: Please upload a PDF file", None


    if not prompt.strip():
        logger.error("Prompt is empty")
        return "Error: Please provide a non-empty prompt", None


    pages = parse_page_numbers(pages_str)
    if not pages:
        logger.error("Invalid or empty page numbers input: %s", pages_str)
        return "Error: Please provide valid page numbers (e.g., 1,3,5 or 1-3)", None


    # Get source language code
    src_lang_code = lang_code_map.get(src_lang)
    if not src_lang_code:
        logger.error("Invalid source language selection: %s", src_lang)
        return "Error: Invalid source language selection", None


    # Get file path from Gradio File object
    file_path = pdf_file.name if hasattr(pdf_file, 'name') else pdf_file


    logger.debug("Calling API with file: %s, pages: %s, prompt: %s, src_lang: %s",
                 file_path, pages, prompt, src_lang_code)


    results = {}
    for page_number in pages:
        try:
            # Call the extraction API without translation parameters
            result = dwani.Documents.run_extract(
                file_path=file_path,
                page_number=page_number,
                src_lang=src_lang_code,
                # Removed tgt_lang parameter
             # Assuming API supports prompt param here
            )
            logger.debug("API response for page %d: %s", page_number, result)


            # Extract page data from response
            page_data = None
            for p in result.get('pages', []):
                if p.get('processed_page') == page_number:
                    page_data = p
                    break


            if page_data is None:
                results[f"Page {page_number}"] = {"error": "No data returned for this page"}
                continue


            results[f"Page {page_number}"] = {
                "Processed Page": page_data.get("processed_page", "N/A"),
                "Original Text": page_data.get("page_content", "N/A"),
                # No translation or translated content
                "Response": page_data.get("response", "")  # If API provides a response field
            }
        except dwani.exceptions.DwaniAPIError as e:
            logger.error("Dhwani API error on page %d: %s", page_number, str(e))
            results[f"Page {page_number}"] = {"error": f"API error: {str(e)}"}
        except Exception as e:
            logger.error("Unexpected error on page %d: %s", page_number, str(e))
            results[f"Page {page_number}"] = {"error": f"Unexpected error: {str(e)}"}
    # Convert results to markdown text
    markdown_text = results_to_markdown(results)


    # Save markdown to a temporary file for download
    temp_md_file = tempfile.NamedTemporaryFile(delete=False, suffix=".md", mode='w', encoding='utf-8')
    temp_md_file.write(markdown_text)
    temp_md_file.close()


    # Return markdown text and file path for download
    return markdown_text, temp_md_file.name



# Define Gradio interface
with gr.Blocks(title="PDF Custom Prompt Processor with Multi-Page Support") as demo:
    gr.Markdown("# PDF Custom Prompt Processor")
    gr.Markdown("Upload a PDF, specify page numbers (comma-separated or ranges), enter a prompt, and select source language.")


    with gr.Row():
        with gr.Column():
            pdf_input = gr.File(label="Upload PDF", file_types=[".pdf"])
            pages_input = gr.Textbox(
                label="Page Numbers",
                placeholder="e.g., 1,3,5 or 1-3",
                value="1",
                lines=1
            )
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
            submit_btn = gr.Button("Process")


        with gr.Column():
            output_md = gr.Markdown(label="Response (Markdown)")
            download_md = gr.File(label="Download Markdown File")


    submit_btn.click(
        fn=process_pdf,
        inputs=[pdf_input, pages_input, prompt, src_lang_input],
        outputs=[output_md, download_md]
    )



# Launch the interface
if __name__ == "__main__":
    if not dwani.api_key or not dwani.api_base:
        logger.error("API key or base URL not set. Please set DWANI_API_KEY and DWANI_API_BASE_URL environment variables.")
        print("Error: Please set DWANI_API_KEY and DWANI_API_BASE_URL environment variables.")
    else:
        logger.debug("Starting Gradio interface...")
        demo.launch()
