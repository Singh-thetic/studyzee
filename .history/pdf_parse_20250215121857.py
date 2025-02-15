import openai
import PyPDF2
import os

openai.api_key = os.getenv('OPENAI_API_KEY')

def extract_text_from_pdf(pdf_path):
    pdf_text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            pdf_text += page.extract_text()
    return pdf_text

def query_openai(prompt):
    response = openai.Completion.create(
        engine="gpt-4o",
        prompt=prompt,
        max_tokens=250
    )
    return response.choices[0].text.strip()

def main():
    pdf_path = '267_syllabus.pdf'
    pdf_text = extract_text_from_pdf(pdf_path)
    
    query = """Here is a pdf about the syllabus for a course. Can you summarize it for me? I need you to identify the following information:
    1. Lecture time and location(class schedule)
    2. Instructor's name and email
    3. A table of weightage for assignments, quizzes, and exams(should be python parasable for easy information retrieval.)
    # If there are multiple assignments (like 5 assignment for total 40%, you should write each sepearately like assignment 1 = 8%)"""
    prompt = f"{pdf_text}\n\n{query}"
    
    response = query_openai(prompt)
    print("Response from OpenAI:", response)

if __name__ == "__main__":
    main()