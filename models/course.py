"""
Course and assignment related models for Studyzee.
"""

from typing import Dict, Any, Optional, List
from datetime import date, time


class Course:
    """Course model."""

    def __init__(
        self,
        course_id: str,
        subject_id: str,
        course_code: str,
        course_name: str,
        professor: str,
        professor_email: str,
        class_schedule: str,
    ) -> None:
        """
        Initialize Course object.

        Args:
            course_id: Unique course identifier.
            subject_id: Subject abbreviation (e.g., 'CS').
            course_code: Course code (e.g., '101').
            course_name: Full course name.
            professor: Instructor name.
            professor_email: Instructor email.
            class_schedule: Comma-separated schedule days.
        """
        self.id = course_id
        self.subject_id = subject_id
        self.course_code = course_code
        self.course_name = course_name
        self.professor = professor
        self.professor_email = professor_email
        self.class_schedule = class_schedule

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Course":
        """Create Course from database record."""
        return cls(
            course_id=data["course_id"],
            subject_id=data["subject_id"],
            course_code=data["course_code"],
            course_name=data.get("course_name", ""),
            professor=data.get("professor", ""),
            professor_email=data.get("professor_email", ""),
            class_schedule=data.get("class_schedule", ""),
        )

    def display_name(self) -> str:
        """Get display name for course."""
        return f"{self.subject_id} {self.course_code}"

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Course {self.display_name()}>"


class Assignment:
    """Assignment/Work model."""

    def __init__(
        self,
        work_id: str,
        name: str,
        course_id: str,
        weightage: float,
        due_date: Optional[date] = None,
        due_time: Optional[time] = None,
        done: bool = False,
    ) -> None:
        """
        Initialize Assignment object.

        Args:
            work_id: Unique assignment identifier.
            name: Assignment name.
            course_id: Related course ID.
            weightage: Weight percentage of assignment.
            due_date: Due date.
            due_time: Due time.
            done: Completion status.
        """
        self.id = work_id
        self.name = name
        self.course_id = course_id
        self.weightage = weightage
        self.due_date = due_date
        self.due_time = due_time
        self.done = done

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Assignment":
        """Create Assignment from database record."""
        return cls(
            work_id=data["id"],
            name=data["work_template"].get("name", ""),
            course_id=data["course_id"],
            weightage=float(data.get("weightage", 0)),
            due_date=data.get("due_date"),
            due_time=data.get("due_time"),
            done=data.get("done", False),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Assignment {self.name}>"


class Task:
    """Custom user task model."""

    def __init__(
        self,
        task_id: str,
        task_name: str,
        due_date: Optional[date] = None,
        due_time: Optional[time] = None,
        done: bool = False,
        description: str = "",
    ) -> None:
        """
        Initialize Task object.

        Args:
            task_id: Unique task identifier.
            task_name: Task name.
            due_date: Due date.
            due_time: Due time.
            done: Completion status.
            description: Task description.
        """
        self.id = task_id
        self.task_name = task_name
        self.due_date = due_date
        self.due_time = due_time
        self.done = done
        self.description = description

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create Task from database record."""
        return cls(
            task_id=data["task_id"],
            task_name=data["task_name"],
            due_date=data.get("due_date"),
            due_time=data.get("due_time"),
            done=data.get("done", False),
            description=data.get("description", ""),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Task {self.task_name}>"
