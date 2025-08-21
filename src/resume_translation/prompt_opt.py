import dwani
import os

# Set up the API key and base URL
dwani.api_key = os.getenv("DWANI_API_KEY")
dwani.api_base = os.getenv("DWANI_API_BASE_URL")

# Load the document and run OCR on page 1 and page 2
page_number1_result = dwani.Documents.run_ocr_page(
    file_path="Sahana_S_Shetty.pdf", page_number=1, model="gemma3"
)
page_number2_result = dwani.Documents.run_ocr_page(
    file_path="Sahana_S_Shetty.pdf", page_number=2, model="gemma3"
)

# Combine the text content from both pages
extracted_resume = page_number1_result["page_content"] + page_number2_result["page_content"]
resume_str = str(extracted_resume)

# First prompt: Extract Contact Information, Professional Summary, and Skills
prompt1 = (
    "You are an expert in resume parsing. Given the text of a resume below:\n\n"
    f"{resume_str}\n\n"
    "Extract the following details and format them cleanly using **Markdown formatting**.\n"
    "Organize the information under the following section headings:\n\n"
    "## Contact Information\n"
    "(Include Name, Phone Number, Email, Address, if available)\n\n"
    "## Professional Summary\n"
    "(Include only if present. This is usually a short description or objective statement.)\n\n"
    "## Skills\n"
    "(List technical  skills)\n\n"
    
)

# Second prompt: Extract Education, Work Experience, Certifications, and Awards
prompt2 = (
    "You are an expert in resume parsing. Given the text of a resume below:\n\n"
    f"{resume_str}\n\n"
    "Extract and format the following details into a clean, professional **resume** using **Markdown formatting**.\n"
    "Organize the information under the following section headings:\n\n"
    "## Education\n"
    "(Degree, Institution, Year)\n\n"
    "## Work Experience\n"
    "(Job Title, Company, Dates, Description)\n\n"
    "## Certifications / Awards\n"
    "(Certification Name, Issuing Authority, Date or Duration)\n\n"
    "Please make sure to include bullet points, line breaks, or sections where appropriate."
    "Do not include capstone project and tech stack in education"
    "Do not repeat the data"
    "Extract first name of institution also in education"
    "Extract all the work experience, do not exclude any"
)

# Send the first prompt to the model
response1 = dwani.Chat.direct(prompt=prompt1, model="gemma3")

# Send the second prompt to the model
response2 = dwani.Chat.direct(prompt=prompt2, model="gemma3")

# Combine the responses from both parts into one markdown formatted resume
markdown_resume = response1["response"] + "\n" + response2["response"]

# Save the result to a file
output_file = "parsed_resume3.md"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(markdown_resume)

print(f"Markdown resume saved to: {output_file}")
