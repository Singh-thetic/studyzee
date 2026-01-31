"""
User model for Studyzee application.
"""

from flask_login import UserMixin
from typing import Optional, Dict, Any


class User(UserMixin):
    """User model representing a Studyzee user."""

    def __init__(self, user_id: str, username: str, email: str, full_name: str, **kwargs) -> None:
        """
        Initialize User object.

        Args:
            user_id: Unique user identifier (UUID).
            username: User's username.
            email: User's email address.
            full_name: User's full name.
            **kwargs: Additional user attributes from database.
        """
        self.id = user_id
        self.username = username
        self.email = email
        self.full_name = full_name
        
        # Dynamically set all additional attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """
        Create User object from database record.

        Args:
            data: Dictionary with user data from database.

        Returns:
            User instance.
        """
        # Extract required fields
        required = {
            "user_id": data["id"],
            "username": data["username"],
            "email": data["email"],
            "full_name": data["full_name"],
        }
        
        # Pass all other fields as kwargs
        additional = {k: v for k, v in data.items() if k not in ["id", "username", "email", "full_name"]}
        
        return cls(**required, **additional)

    def reload_from_db(self, db) -> None:
        """
        Reload user data from database.
        
        Args:
            db: Database instance.
        """
        user_data = db.select_one("users", "id", self.id)
        if user_data:
            # Update all attributes
            for key, value in user_data.items():
                setattr(self, key if key != "id" else "id", value)
    
    def __repr__(self) -> str:
        """Return string representation of User."""
        return f"<User {self.username}>"
