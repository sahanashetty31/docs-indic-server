import dwani        
import os

dwani.api_key = os.getenv("DWANI_API_KEY")
dwani.api_base = os.getenv("DWANI_API_BASE_URL")
"""
result = dwani.Documents.run_ocr_all(
            file_path="sahana_shetty_resume_2024.pdf", model="gemma3"
        )
"""
page_number1_result = dwani.Documents.run_ocr_number(
            file_path="sahana_shetty_resume_2024.pdf", page_number=1, model="gemma3"
        )
#print("Document Query Response: gemma3- ", page_number1_result)

#print("----------------------------")
page_number2_result= dwani.Documents.run_ocr_number(
            file_path="sahana_shetty_resume_2024.pdf", page_number=2, model="gemma3"
        )
#print("Document Query Response: gemma3- ", page_number2_result)

extracted_resume = page_number1_result["page_content"] + page_number2_result["page_content"]
#print(extracted_resume)

resume_str = str(extracted_resume)
"""
prompt1 = (
        "You are an expert in resume parsing. Given the text of a resume below:\n\n"
        f"{resume_str}\n\n"
        "Extract the following details clearly and accurately:\n"
        "1. Contact details (e.g., name, phone number, email, address)\n"
        "2. Objective or professional summary (if present)\n"
        "3. Education details (include degree, institution, year)\n"
        "4. Work experience (job title, company, dates, description)\n"
        "5. Skills (technical and non-technical)\n"
        "6. Certifications (name and issuing authority)\n\n"
        "Ignore any unrelated information.\n"
        "Return the extracted information in a JSON format with the following keys exactly: "
        "'contact_details', 'objective', 'education', 'work_experience', 'skills', 'certifications'.\n"
        
    )
response1 = dwani.Chat.direct(prompt=prompt1, model="gemma3")
print(response1)

print("--------------------------------")
"""
prompt2 =(
    "You are an expert in resume parsing. Given the text of a resume below:\n\n"
    f"{resume_str}\n\n"
    "Extract and format the following details into a clean, professional **resume** using **Markdown formatting**.\n"
    "Organize the information under the following section headings:\n\n"
    "## Contact Information\n"
    "(Include Name, Phone Number, Email, Address)\n\n"
    "## Professional Summary\n"
    "(Include only if present)\n\n"
    "## Education\n"
    "(Degree, Institution, Year)\n\n"
    "## Work Experience\n"
    "(Job Title, Company, Dates, Description)\n\n"
    "## Skills\n"
    "(List technical and non-technical skills)\n\n"
    "## Awards\n"
    "(Name and Issuing Authority)\n\n"
    "Use bullet points or line breaks where appropriate. Ignore unrelated or repetitive content."

)


response2 = dwani.Chat.direct(prompt=prompt2, model="gemma3")
print(response2)

markdown_resume = response2["response"]  # Adjust key if needed based on the actual response format
output_file = "parsed_resume.md"

with open(output_file, "w", encoding="utf-8") as f:
    f.write(markdown_resume)

print(f"Markdown resume saved to: {output_file}")
"""
print("--------------------------------")

prompt3 = (
        "You are an expert in resume parsing. Given the text of a resume below:\n\n"
        f"{resume_str}\n\n"
        "Extract the following details clearly and accurately:\n"
        "1. Contact details \n"
        "2. Objective or professional summary \n"
        "3. Education details \n"
        "4. Work experience \n"
        "5. Skills \n"
        "6. Certifications \n\n"
        "Ignore any unrelated information.\n"
        "Return the extracted information in a JSON format with the following keys exactly: "
        "'contact_details', 'objective', 'education', 'work_experience', 'skills', 'certifications'.\n"
        
    )
response3 = dwani.Chat.direct(prompt=prompt3, model="gemma3")
print(response3)

print("--------------------------------")

prompt4 = (
        "You are an expert in resume parsing. Given the text of a resume below:\n\n"
        f"{resume_str}\n\n"
        "Extract the following details clearly and accurately:\n"
        "1. Contact details \n"
        "2. Objective or professional summary \n"
        "3. Education details \n"
        "4. Work experience \n"
        "5. Skills \n"
        "6. Certifications \n\n"
        "Ignore any unrelated information.\n"
        "Return the extracted information in a JSON format with the following keys exactly: "
        "'contact_details', 'objective', 'education', 'work_experience', 'skills', 'certifications'.\n"
        
    )
response4 = dwani.Chat.direct(prompt=prompt4, model="gemma3")
print(response4)

print("--------------------------------")

prompt5 = (
        "You are an expert in resume parsing. Given the text of a resume below:\n\n"
        f"{resume_str}\n\n"
        "Extract the following details clearly and accurately:\n"
        "1. Contact details \n"
        "2. Objective or professional summary \n"
        "3. Education details \n"
        "4. Work experience \n"
        "5. Skills \n"
        "6. Certifications \n\n"
        "Ignore any unrelated information.\n"
        "Return the extracted information in a JSON format with the following keys exactly: "
        "'contact_details', 'objective', 'education', 'work_experience', 'skills', 'certifications'.\n"
        
    )
response5 = dwani.Chat.direct(prompt=prompt5, model="gemma3")
print(response5)

print("--------------------------------")

prompt6 = (
        "You are an expert in resume parsing. Given the text of a resume below:\n\n"
        f"{resume_str}\n\n"
        "Extract the following details clearly and accurately:\n"
        "1. Contact details \n"
        "2. Objective or professional summary \n"
        "3. Education details \n"
        "4. Work experience \n"
        "5. Skills \n"
        "6. Certifications \n\n"
        "Ignore any unrelated information.\n"
        "Return the extracted information in a JSON format with the following keys exactly: "
        "'contact_details', 'objective', 'education', 'work_experience', 'skills', 'certifications'.\n"
        
    )
response6 = dwani.Chat.direct(prompt=prompt6, model="gemma3")
print(response6)

print("--------------------------------")

prompt7 = (
        "You are an expert in resume parsing. Given the text of a resume below:\n\n"
        f"{resume_str}\n\n"
        "Extract the following details clearly and accurately:\n"
        "1. Contact details \n"
        "2. Objective or professional summary \n"
        "3. Education details \n"
        "4. Work experience \n"
        "5. Skills \n"
        "6. Certifications \n\n"
        "Ignore any unrelated information.\n"
        "Return the extracted information in a JSON format with the following keys exactly: "
        "'contact_details', 'objective', 'education', 'work_experience', 'skills', 'certifications'.\n"
        
    )
response7 = dwani.Chat.direct(prompt=prompt7, model="gemma3")
print(response7)

print("--------------------------------")

prompt8 = (
        "You are an expert in resume parsing. Given the text of a resume below:\n\n"
        f"{resume_str}\n\n"
        "Extract the following details clearly and accurately:\n"
        "1. Contact details \n"
        "2. Objective or professional summary \n"
        "3. Education details \n"
        "4. Work experience \n"
        "5. Skills \n"
        "6. Certifications \n\n"
        "Ignore any unrelated information.\n"
        "Return the extracted information in a JSON format with the following keys exactly: "
        "'contact_details', 'objective', 'education', 'work_experience', 'skills', 'certifications'.\n"
        
    )
response8 = dwani.Chat.direct(prompt=prompt8, model="gemma3")
print(response8)

print("--------------------------------")

prompt9 = (
        "You are an expert in resume parsing. Given the text of a resume below:\n\n"
        f"{resume_str}\n\n"
        "Extract the following details clearly and accurately:\n"
        "1. Contact details \n"
        "2. Objective or professional summary \n"
        "3. Education details \n"
        "4. Work experience \n"
        "5. Skills \n"
        "6. Certifications \n\n"
        "Ignore any unrelated information.\n"
        "Return the extracted information in a JSON format with the following keys exactly: "
        "'contact_details', 'objective', 'education', 'work_experience', 'skills', 'certifications'.\n"
        
    )
response9 = dwani.Chat.direct(prompt=prompt9, model="gemma3")
print(response9)

print("--------------------------------")

prompt10 = (
        "You are an expert in resume parsing. Given the text of a resume below:\n\n"
        f"{resume_str}\n\n"
        "Extract the following details clearly and accurately:\n"
        "1. Contact details \n"
        "2. Objective or professional summary \n"
        "3. Education details \n"
        "4. Work experience \n"
        "5. Skills \n"
        "6. Certifications \n\n"
        "Ignore any unrelated information.\n"
        "Return the extracted information in a JSON format with the following keys exactly: "
        "'contact_details', 'objective', 'education', 'work_experience', 'skills', 'certifications'.\n"
        
    )
response10 = dwani.Chat.direct(prompt=prompt10, model="gemma3")
print(response10)

"""
