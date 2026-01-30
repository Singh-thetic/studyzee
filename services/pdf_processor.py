"""
PDF processing service for extracting course information from syllabi.
"""

import logging
from typing import Dict, Any, Optional
import PyPDF2

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from PDF file.

    Args:
        pdf_path: Path to PDF file.

    Returns:
        Extracted text content.

    Raises:
        IOError: If file cannot be read.
    """
    try:
        pdf_text = ""
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                pdf_text += page.extract_text()
        return pdf_text
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {pdf_path}: {str(e)}")
        raise IOError(f"Cannot read PDF file: {str(e)}")


def parse_course_sections(response_text: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse course information from AI response text.

    Args:
        response_text: AI-generated course information text.

    Returns:
        Dictionary with course sections and their details.
    """
    try:
        sections = response_text.split("### START OF SECTION")[1:]
        course_info = {}

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Extract section name
            section_name = (
                section.split("###")[0]
                .replace(" ", "")
                .replace("*", "")
                .replace("[", "")
                .replace("]", "")
                .strip()
            )

            course_info[section_name] = {}

            # Extract lecture days
            try:
                lecture_date = section.split("111-LectureDays: [")[1].split("] -111")[0].strip()
                course_info[section_name]["lecture_days"] = _parse_days(lecture_date)
            except (IndexError, ValueError) as e:
                logger.warning(f"Could not parse lecture days: {str(e)}")
                course_info[section_name]["lecture_days"] = []

            # Extract instructor info
            try:
                instructor_name = section.split("222-InstructorName: [")[1].split("] -222")[0].strip()
                course_info[section_name]["instructor_name"] = instructor_name
            except (IndexError, ValueError) as e:
                logger.warning(f"Could not parse instructor name: {str(e)}")
                course_info[section_name]["instructor_name"] = "Unknown"

            try:
                instructor_email = section.split("222-InstructorEmail: [")[1].split("] -222")[0].strip()
                course_info[section_name]["instructor_email"] = instructor_email
            except (IndexError, ValueError) as e:
                logger.warning(f"Could not parse instructor email: {str(e)}")
                course_info[section_name]["instructor_email"] = "Unknown"

            # Extract weightage table
            try:
                weightage_section = section.split("333-Weightage table-333")[1].split("333-Weightage table-333")[0].strip()
                weightage_items = weightage_section.split("\n")
                course_info[section_name]["weightage"] = {}

                for item in weightage_items:
                    item = item.strip()
                    if not item:
                        continue
                    item = item.replace("[", "").replace("]", "")
                    parsed = _parse_weightage_item(item)
                    if parsed:
                        course_info[section_name]["weightage"].update(parsed)
            except (IndexError, ValueError) as e:
                logger.warning(f"Could not parse weightage table: {str(e)}")
                course_info[section_name]["weightage"] = {}

        return course_info
    except Exception as e:
        logger.error(f"Failed to parse course sections: {str(e)}")
        return {}


def _parse_days(day_string: str) -> list[str]:
    """
    Parse day abbreviations into full day names.

    Args:
        day_string: String with day abbreviations (e.g., 'MTWF').

    Returns:
        List of full day names.
    """
    from utils.constants import DAY_ABBREVIATIONS

    days = []
    i = 0
    while i < len(day_string):
        if i + 1 < len(day_string) and day_string[i : i + 2] in DAY_ABBREVIATIONS:
            days.append(DAY_ABBREVIATIONS[day_string[i : i + 2]])
            i += 2
        elif day_string[i] in DAY_ABBREVIATIONS:
            days.append(DAY_ABBREVIATIONS[day_string[i]])
            i += 1
        else:
            i += 1
    return days


def _parse_weightage_item(item: str) -> Optional[Dict[str, Dict[str, str]]]:
    """
    Parse a single weightage item line.

    Args:
        item: Single weightage line from table.

    Returns:
        Dictionary with parsed item or None if parsing failed.
    """
    try:
        parts = item.split(": ")
        if len(parts) < 2:
            return None

        element_key = parts[0].strip()
        rest = ": ".join(parts[1:])

        name = rest.split(" -")[0].strip()
        weight = rest.split("-")[1].split("-")[0].strip()
        due_date = rest.split("DUE ")[1].split(" TIME")[0].strip() if "DUE " in rest else "[TBD]"
        due_time = rest.split("TIME ")[1].split("-")[0].strip() if "TIME " in rest else "[TBD]"

        return {
            name: {
                "weight": weight,
                "due_date": due_date,
                "due_time": due_time,
            }
        }
    except (IndexError, ValueError) as e:
        logger.warning(f"Could not parse weightage item: {str(e)}")
        return None
