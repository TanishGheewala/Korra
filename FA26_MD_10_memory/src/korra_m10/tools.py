"""Structured tool inputs, shared unchanged by the SQLite and Postgres graphs."""
from langchain_core.tools import tool
from .database import read_students, save_student


@tool
def save_database(name: str, email: str, major: str, gpa: float, enrollment_date: str) -> dict:
    """Save a new student, without enrolling them in courses or overwriting an email.

    Supply name, email, major, GPA (0 to 4), and enrollment_date (YYYY-MM-DD).
    Returns status success, refused (duplicate/invalid input), or error.
    """
    return save_student(name, email, major, gpa, enrollment_date)


@tool
def read_database(email: str = "") -> dict:
    """Read the student with this email, or list students when email is empty.

    Returns success with students and counts, not_found, or error.
    The tool reads records only; it does not run model-supplied SQL.
    """
    return read_students(email)
