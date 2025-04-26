import gradio as gr
import requests
import mimetypes

API_URL = "http://209.20.158.215:7862/v1/visual_query/?src_lang=eng_Latn&tgt_lang=kan_Knda"

def ocr_from_paths(file_paths, query):
    results = []
    if isinstance(file_paths, str):
        file_paths = [file_paths]
    
    for path in file_paths:
        filename = path.split("/")[-1]
        mime_type, _ = mimetypes.guess_type(path)
        if not mime_type:
            results.append(f"❌ {filename}: Unsupported file type")
            continue
            
        with open(path, "rb") as f:
            files_param = {"file": (filename, f, mime_type)}
            data_param = {"query": query or "describe the image"}  # default query if empty
            
            try:
                response = requests.post(
                    API_URL,
                    files=files_param,
                    data=data_param,
                    headers={"accept": "application/json"}  # do NOT set Content-Type here
                )
                if response.status_code == 200:
                    resp_json = response.json()
                    extracted_text = resp_json.get("result") or resp_json.get("text") or str(resp_json)
                    results.append(f"✅ {filename}:\n{extracted_text}")
                else:
                    results.append(f"❌ {filename}: API Error ({response.status_code})")
            except Exception as e:
                results.append(f"❌ {filename}: {str(e)}")
    
    return "\n\n".join(results)

with gr.Blocks() as demo:
    gr.Markdown("## Browse & OCR Extract PDFs/Images (Batch)")
    with gr.Row():
        file_input = gr.File(
            label="Upload Files",
            file_types=[".pdf", ".png", ".jpg", ".jpeg", ".webp"],
            file_count="multiple"
        )
        query_input = gr.Textbox(
            label="Query (optional)",
            placeholder="Enter a query string for the API"
        )
    
    output_text = gr.Textbox(
        label="Extracted Text Results",
        interactive=False,
        lines=15,
        placeholder="OCR results will appear here..."
    )
    
    submit_btn = gr.Button("Extract Text")
    submit_btn.click(
        ocr_from_paths,
        inputs=[file_input, query_input],
        outputs=output_text
    )

if __name__ == "__main__":
    demo.launch()
