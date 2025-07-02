import gradio as gr


def process_pdf(pdf_file):
    pass

# Define Gradio interface
with gr.Blocks(title="Resume Translator") as resume_translator:
    gr.Markdown("# Resume upload")
    gr.Markdown("Upload a Resume.")
    
    with gr.Row():
        with gr.Column():
            pdf_input = gr.File(label="Upload Resume", file_types=[".pdf"])

            submit_btn = gr.Button("Process")
        
        with gr.Column():
            output = gr.JSON(label="Response")
    
    submit_btn.click(
        fn=process_pdf,
        inputs=[pdf_input],
        outputs=output
    )



if __name__ == "__main__":
    resume_translator.launch()