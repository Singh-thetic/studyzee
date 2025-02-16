import openai
import PyPDF2
import os
from pdf_parse import extract_text_from_pdf
openai.api_key = os.getenv('OPENAI_API_KEY')

def flashcards(file_path):
    pdf_text = extract_text_from_pdf(file_path)
    query = """Here are notes from a topic. Can you create flashcards for me? I need you to identify the following information:
    1. Definitions
    2. Key Concepts
    3. Important Points
    4. Examples
    5. Diagrams
    6. Formulas
    7. Mnemonics
    8. Acronyms
    9. Important Dates
    10. Important People
    11. Important Events
    12. Important Places
    13. Important Terms
    14. Important Quotes
    15. Important Ideas
    16. Important Theories
    17. Important Laws
    18. Important Principles
    19. Important Equations
    20. Important Experiments
    
    You should ask information as question-answer pairs. For example:
    Q: What is the definition of a term?
    A: The definition of a term is...

    The format should be like this:
    #Q#: [Question]
    #A#: [Answer]
    
    Try to make as much questions as possible. (MOST IMPORTANT 15-20 QUESTIONS)
    Keep the output text parsable by mathjax and not having any invalid escape sequence.
    """
    prompt = pdf_text + '\n\n' + query
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2500
    )
    questions = response.choices[0].message['content'].strip()
    pairs = questions.split("#Q")[1:]
    flashcards = []
    for pair in pairs:
        if pair:
            question, answer = pair.split("#A")
            flashcards.append((question.split(': ')[1].strip(), answer.split(': ')[1].split('\n')[0].strip()))
    return flashcards

if __name__ == "__main__":
    file_path = "mdps.pdf"
    print(flashcards(file_path))
