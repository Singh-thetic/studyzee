"""
AI assistant service for OpenAI integration.

Handles course parsing, flashcard generation, and other AI-powered features.
"""

import logging
import os
from typing import Dict, Any, List, Tuple
import openai

logger = logging.getLogger(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")


def parse_course_info(pdf_texts: List[str]) -> Dict[str, Any]:
    """
    Parse course information from PDF texts using OpenAI.

    Args:
        pdf_texts: List of extracted PDF text content.

    Returns:
        Dictionary with parsed course information.
    """
    combined_text = "\n\n".join(pdf_texts)

    prompt = """Here is a pdf about the syllabus for a course. Can you summarize it for me? I need you to identify the following information:
    1. Lecture time and location (class schedule)
    2. Instructor's name and email
    3. A table of weightage for assignments, quizzes, and exams

    The format should be like this:
    111-LectureDays: [MTWRF] -111
    111-LectureTime: [HH:MM-HH:MM] -111
    111-LectureLocation: [Building, Room] -111
    222-InstructorName: [First Last] -222
    222-InstructorEmail: [email] -222
    333-Weightage table-333
    element[no]: [name] -[percentage]- -DUE [MM/DD/YY] TIME [HH:MM]-
    333-Weightage table-333

    If there are multiple sections, write them separately with separators like:
    ### START OF SECTION *code* ###
    DATA
    ### END OF SECTION *code* ###
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for parsing course syllabi."},
                {"role": "user", "content": f"{combined_text}\n\n{prompt}"},
            ],
            max_tokens=2000,
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        logger.error(f"Failed to parse course info with AI: {str(e)}")
        return {}


def generate_flashcards(pdf_text: str) -> List[Tuple[str, str]]:
    """
    Generate flashcards from study notes using OpenAI.

    Args:
        pdf_text: Extracted text from study notes PDF.

    Returns:
        List of (question, answer) tuples.
    """
    prompt = """Here are notes from a topic. Can you create flashcards for me?

    You should ask information as question-answer pairs. For example:
    Q: What is the definition of a term?
    A: The definition of a term is...

    The format should be like this:
    #Q#: [Question]
    #A#: [Answer]

    Try to make 15-20 important questions. Keep the output text parsable by mathjax."""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful study assistant."},
                {"role": "user", "content": f"{pdf_text}\n\n{prompt}"},
            ],
            max_tokens=2500,
        )
        response_text = response.choices[0].message["content"].strip()
        return _parse_flashcard_response(response_text)
    except Exception as e:
        logger.error(f"Failed to generate flashcards: {str(e)}")
        return []


def _parse_flashcard_response(response_text: str) -> List[Tuple[str, str]]:
    """
    Parse flashcard response from AI.

    Args:
        response_text: Raw response from OpenAI.

    Returns:
        List of (question, answer) tuples.
    """
    flashcards = []
    try:
        pairs = response_text.split("#Q")[1:]
        for pair in pairs:
            if pair:
                try:
                    question, answer = pair.split("#A")
                    q_text = question.split(": ", 1)[1].strip() if ": " in question else question.strip()
                    a_text = answer.split(": ", 1)[1].split("\n")[0].strip() if ": " in answer else answer.strip()
                    if q_text and a_text:
                        flashcards.append((q_text, a_text))
                except (IndexError, ValueError) as e:
                    logger.warning(f"Could not parse flashcard pair: {str(e)}")
                    continue
    except Exception as e:
        logger.error(f"Failed to parse flashcard response: {str(e)}")
    return flashcards
