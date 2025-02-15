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
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )
    return response.choices[0].message['content'].strip()

def main():
    pdf_path = '225_syllabus.pdf'
    pdf_text = extract_text_from_pdf(pdf_path)
    
    query = """Here is a pdf about the syllabus for a course. Can you summarize it for me? I need you to identify the following information:
    1. Lecture time and location(class schedule)
    2. Instructor's name and email
    3. A table of weightage for assignments, quizzes, and exams(should be python parasable for easy information retrieval.)
    # If there are multiple assignments (like 5 assignment for total 40%, you should write each sepearately like assignment 1 = 8%)
    # 
     The format should be like this:
     111-LectureDays: [MTWRF] -111    ## Keep the format in single alphabet for each day, use R for Thursday
     111-LectureTime: [HH:MM-HH:MM] -111
     111-LectureLocation: [Building, Room] -111
     222-InstructorName: [First Last] -222
     222-InstructorEmail: [email] -222
     333-Weightage table-333
     element[no]: [name] -[percentage]
     
     If there is something like best 7 of 8, assign the percentage to the first 7 and write the 8th with zero percent weightage.
     For example a best 3 out of 4 assignments for 10 percent should be written as:
     element1: assignment 1 -[3.33]-
     element2: assignment 2 -[3.33]-
     element3: assignment 3 -[3.33]-
     element4: assignment4 -[0]-
     333-Weightage table-333
     Keep in fractions for accurate representation."""
    prompt = f"{pdf_text}\n\n{query}"
    
    response = query_openai(prompt)
    print("Response from OpenAI:", response)

if __name__ == "__main__":
    main()