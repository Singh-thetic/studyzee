"""
Input validation utilities for Studyzee application.
"""

import re
from typing import Optional


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate.

    Returns:
        True if email format is valid, False otherwise.
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength.

    Args:
        password: Password to validate.

    Returns:
        Tuple of (is_valid, error_message). Error message is None if valid.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    return True, None


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    Validate username format.

    Args:
        username: Username to validate.

    Returns:
        Tuple of (is_valid, error_message). Error message is None if valid.
    """
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    if len(username) > 30:
        return False, "Username must be at most 30 characters long"
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    return True, None


def validate_file_extension(filename: str, allowed_extensions: set) -> bool:
    """
    Validate file extension.

    Args:
        filename: Name of the file.
        allowed_extensions: Set of allowed extensions (e.g., {'pdf', 'jpg', 'png'}).

    Returns:
        True if file extension is allowed, False otherwise.
    """
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in allowed_extensions


def validate_course_code(code: str) -> bool:
    """
    Validate course code format.

    Args:
        code: Course code to validate.

    Returns:
        True if course code is valid, False otherwise.
    """
    return bool(re.match(r"^[A-Z]{2,4}\d{3,4}$", code))
