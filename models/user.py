"""
User model for Studyzee application.
"""

from flask_login import UserMixin
from typing import Optional, Dict, Any


class User(UserMixin):
    """User model representing a Studyzee user."""

    def __init__(self, user_id: str, username: str, email: str, full_name: str) -> None:
        """
        Initialize User object.

        Args:
            user_id: Unique user identifier (UUID).
            username: User's username.
            email: User's email address.
            full_name: User's full name.
        """
        self.id = user_id
        self.username = username
        self.email = email
        self.full_name = full_name

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """
        Create User object from database record.

        Args:
            data: Dictionary with user data from database.

        Returns:
            User instance.
        """
        return cls(
            user_id=data["id"],
            username=data["username"],
            email=data["email"],
            full_name=data["full_name"],
        )

    def __repr__(self) -> str:
        """Return string representation of User."""
        return f"<User {self.username}>"
