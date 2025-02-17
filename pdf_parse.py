import openai
import PyPDF2
import os
from dotenv import load_dotenv
load_dotenv()
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

def course_info(pdf_paths: list):
    pdf_text = ""
    for pdf_path in pdf_paths:
        pdf_text += extract_text_from_pdf(pdf_path)
    
    query = """Here is a pdf about the syllabus for a course. Can you summarize it for me? I need you to identify the following information:
    1. Lecture time and location(class schedule)
    2. Instructor's name and email
    3. A table of weightage for assignments, quizzes, and exams(should be python parasable for easy information retrieval.)
    # If there are multiple assignments (like 5 assignment for total 40%, you should write each sepearately like assignment 1 = 8%)
    # 

     The format should be like this:
     111-LectureDays: [MTWRF] -111    ## Keep the format in single alphabet for each day, use M FOR 'MONDAY', T FOR 'TUESDAY' AND 'TU', W FOR 'WEDNESDAY', R FOR 'THURSDAY' AND 'Th', F FOR 'FRIDAY'
     111-LectureTime: [HH:MM-HH:MM] -111
     111-LectureLocation: [Building, Room] -111
     222-InstructorName: [First Last] -222
     222-InstructorEmail: [email] -222
     333-Weightage table-333
     element[no]: [name] -[percentage]- -DUE [MM/DD/YY] TIME [HH:MM]-     #ELSE [TBD] for any information not accessible #the format is strict and cannot be changed(for date, and time, if not available in that frmat, just write [TBD], THE SQUARE BRACKETS ARE MANDATORY)
     If there are multiple sections, write them separately entirely with a seperator like:
     ### START OF SECTION *code* ###
     DATA
        ### END OF SECTION *code* ###  
     If there is something like best 7 of 8, assign the percentage to the first 7 and write the 8th with zero percent weightage.
     For example a best 3 out of 4 assignments for 10 percent should be written as: (remove any percentage sign if any and keep all square brackets wherever shown)
     element1: assignment 1 -[3.33]- -DUE [02/12/25] TIME [23:59]-
     element2: assignment 2 -[3.33]- -DUE [02/19/25] TIME [23:59]-
     element3: assignment 3 -[3.33]- -DUE [02/26/25] TIME [23:59]-
     element4: assignment4 -[0]- -DUE [03/05/25] TIME [23:59]-
     333-Weightage table-333
     Keep in fractions for accurate representation.
     FOR ELEMENTS WITH information like due mondays at 6 pm, make them also seperately like elemetn1, 2 and so on, try to find information regarding how many elements there are in other parts of the pdf.
     """
    prompt = f"{pdf_text}\n\n{query}"
    
    response = query_openai(prompt)
    with open("response.txt", "w") as file:
        file.write(response)
    return parse_course_results(response)

def parse_course_results(response):
    sections = response.split("### START OF SECTION")[1:]
    course_info = {}
    for section in sections:
        section = section.strip()
        if not section:
            continue
        section_name = section.split("###")[0].replace(" ", "").replace("*", "").replace("[", "").replace("]", "").strip()
        course_info[section_name] = {}
        lecture_date= section.split("111-LectureDays: [")[1].split("] -111")[0].strip()
        dayname = {"M": "Monday", "T": "Tuesday", "W": "Wednesday", "R": "Thursday", "F": "Friday", "Th": "Thursday", "Tu": "Tuesday"}
        course_info[section_name]["LectureDays"] = []
        i = 0
        while i < len(lecture_date):
            if lecture_date[i:i+2] in dayname:
                course_info[section_name]["LectureDays"].append(dayname[lecture_date[i:i+2]])
                i += 2
            else:
                course_info[section_name]["LectureDays"].append(dayname[lecture_date[i]])
                i += 1
        # lecture_time = section.split("111-LectureTime: [")[1].split("] -111")[0].strip()
        # # course_info[section_name]["LectureTime"] = lecture_time
        # # lecture_location = section.split("111-LectureLocation: [")[1].split("] -111")[0].strip()
        # course_info[section_name]["LectureLocation"] = lecture_location
        instructor_name = section.split("222-InstructorName: [")[1].split("] -222")[0].strip()
        course_info[section_name]["InstructorName"] = instructor_name
        instructor_email = section.split("222-InstructorEmail: [")[1].split("] -222")[0].strip()
        course_info[section_name]["InstructorEmail"] = instructor_email
        weightage_table = section.split("333-Weightage table-333")[1].split('333-Weightage table-333')[0].strip()
        weightage_table = weightage_table.split("\n")
        course_info[section_name]["WeightageTable"] = {}
        for element in weightage_table:
            element = element.strip()
            if not element:
                continue
            element = element.replace("[", "").replace("]", "")
            element_name = element.split(": ")[1].split(" -")[0].strip()
            element_weight = element.split("-")[1].split("-")[0].strip()
            element_due_date = element.split("DUE ")[1].split(" TIME")[0].strip()
            element_due_time = element.split("TIME ")[1].split("-")[0].strip()
            course_info[section_name]["WeightageTable"][element_name] = {
                "Weight": element_weight,
                "DueDate": element_due_date,
                "DueTime": element_due_time
            }

    return course_info


if __name__ == "__main__":
    course_info(["365_syllabus.pdf"])
