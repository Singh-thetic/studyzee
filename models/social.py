"""
Social models for Studyzee (friends, study groups, etc.).
"""

from typing import Dict, Any, Optional


class Friend:
    """Friend relationship model."""

    def __init__(self, friend_id: str, username: str, full_name: str, email: str) -> None:
        """
        Initialize Friend object.

        Args:
            friend_id: User ID of friend.
            username: Friend's username.
            full_name: Friend's full name.
            email: Friend's email.
        """
        self.id = friend_id
        self.username = username
        self.full_name = full_name
        self.email = email

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Friend":
        """Create Friend from user data."""
        return cls(
            friend_id=data["id"],
            username=data["username"],
            full_name=data["full_name"],
            email=data["email"],
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Friend {self.username}>"


class StudyGroup:
    """Study group model."""

    def __init__(
        self,
        group_id: str,
        name: str,
        description: str = "",
        owner_id: Optional[str] = None,
    ) -> None:
        """
        Initialize StudyGroup object.

        Args:
            group_id: Unique group identifier.
            name: Group name.
            description: Group description.
            owner_id: ID of group owner.
        """
        self.id = group_id
        self.name = name
        self.description = description
        self.owner_id = owner_id

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StudyGroup":
        """Create StudyGroup from database record."""
        return cls(
            group_id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            owner_id=data.get("owner_id"),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<StudyGroup {self.name}>"


class ChatRoom:
    """Chat room model for private chats."""

    def __init__(
        self,
        room_id: str,
        room_code: str,
        user1_id: str,
        user2_id: str,
    ) -> None:
        """
        Initialize ChatRoom object.

        Args:
            room_id: Unique room identifier.
            room_code: Unique room code.
            user1_id: ID of first user.
            user2_id: ID of second user.
        """
        self.id = room_id
        self.room_code = room_code
        self.user1_id = user1_id
        self.user2_id = user2_id

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatRoom":
        """Create ChatRoom from database record."""
        return cls(
            room_id=data["id"],
            room_code=data["room_code"],
            user1_id=data["user1_id"],
            user2_id=data["user2_id"],
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<ChatRoom {self.room_code}>"
