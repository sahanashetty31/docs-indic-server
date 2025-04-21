import gradio as gr
import requests
import mimetypes

API_URL = "http://209.20.158.215:7860/v1/visual_query/?src_lang=eng_Latn&tgt_lang=kan_Knda"

def ocr_from_paths(file_paths, query):
    results = []
    # Ensure file_paths is a list
    if isinstance(file_paths, str):
        file_paths = [file_paths]
    for path in file_paths:
        filename = path.split("/")[-1]
        mime_type, _ = mimetypes.guess_type(path)
        if not mime_type:
            results.append((filename, "Unsupported file type"))
            continue
        with open(path, "rb") as f:
            files_param = {
                "file": (filename, f, mime_type)
            }
            data_param = {
                "query": query or ""
            }
            try:
                response = requests.post(
                    API_URL,
                    files=files_param,
                    data=data_param,
                    headers={"accept": "application/json"}
                )
                if response.status_code == 200:
                    resp_json = response.json()
                    extracted_text = resp_json.get("result") or resp_json.get("text") or str(resp_json)
                    # Save result to a .txt file for output
                    out_path = f"output_{filename}.txt"
                    with open(out_path, "w", encoding="utf-8") as out_f:
                        out_f.write(extracted_text)
                    results.append(out_path)
                else:
                    results.append(f"API Error: {response.status_code} for {filename}")
            except Exception as e:
                results.append(f"Exception: {str(e)} for {filename}")
    return results if len(results) > 1 else results[0]

with gr.Blocks() as demo:
    gr.Markdown("## Browse & OCR Extract PDFs/Images (Batch)\nSelect files from server and extract text using OCR API.")
    with gr.Row():
        file_input = gr.File(
            label="Upload Files",
            file_types=[".pdf", ".png", ".jpg", ".jpeg", ".webp"], # Specify the file types you want to allow
            file_count="multiple"  # Allow multiple files to be uploaded
)
        
        query_input = gr.Textbox(
            label="Query (optional)",
            placeholder="Enter a query string for the API"
        )
    # Output: list of generated text files for download
    output_files = gr.File(
        label="Extracted Text Files",
        file_count="multiple"
    )
    submit_btn = gr.Button("Extract Text")
    submit_btn.click(
        ocr_from_paths,
        inputs=[file_input, query_input],
        outputs=output_files
    )

if __name__ == "__main__":
    demo.launch()
