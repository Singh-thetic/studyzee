"""
Authentication routes for login, signup, and logout.
"""

import logging
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user, login_required, current_user
from utils.validators import validate_email, validate_password, validate_username
from utils.db import DatabaseClient
from models.user import User
from config import Config

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)
bcrypt = Bcrypt()

# Database client will be initialized in app setup
db = None


def init_auth(database_client: DatabaseClient) -> None:
    """Initialize auth module with database client."""
    global db
    db = database_client


@auth_bp.route("/")
def home():
    """Home/login page."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("login.html", stage="login")


@auth_bp.route("/login", methods=["POST"])
def login():
    """Handle user login."""
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        return render_template("login.html", stage="login", error="Username and password required")

    user_data = db.select_one("users", "username", username)
    if not user_data:
        logger.warning(f"Login attempt with non-existent username: {username}")
        return render_template("login.html", stage="login", error="Invalid username or password")

    if not bcrypt.check_password_hash(user_data["password_hash"], password):
        logger.warning(f"Failed login attempt for user: {username}")
        return render_template("login.html", stage="login", error="Invalid username or password")

    user_obj = User.from_dict(user_data)
    login_user(user_obj)
    logger.info(f"User logged in: {username}")
    flash("Login successful!", "success")
    return redirect(url_for("dashboard"))


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Handle user signup."""
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    full_name = request.form.get("full_name", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    # Validate inputs
    if not all([username, email, full_name, password]):
        return render_template(
            "login.html",
            stage="signup",
            error="All fields are required",
        )

    # Validate username
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        return render_template("login.html", stage="signup", error=error_msg)

    # Validate email
    if not validate_email(email):
        return render_template("login.html", stage="signup", error="Invalid email format")

    # Validate password
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return render_template("login.html", stage="signup", error=error_msg)

    if password != confirm_password:
        return render_template("login.html", stage="signup", error="Passwords do not match")

    # Check if user already exists
    existing_user = db.select_one("users", "username", username)
    if existing_user:
        logger.warning(f"Signup attempt with existing username: {username}")
        return render_template("login.html", stage="signup", error="Username already exists")

    existing_email = db.select_one("users", "email", email)
    if existing_email:
        logger.warning(f"Signup attempt with existing email: {email}")
        return render_template("login.html", stage="signup", error="Email already exists")

    # Create new user
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    user_data = {
        "username": username,
        "email": email,
        "full_name": full_name,
        "password_hash": hashed_password,
    }

    if not db.insert("users", user_data):
        logger.error(f"Failed to create new user: {username}")
        return render_template(
            "login.html",
            stage="signup",
            error="Failed to create account. Please try again.",
        )

    logger.info(f"New user registered: {username}")
    flash("Account created successfully! Please log in.", "success")
    return redirect(url_for("auth.home"))


@auth_bp.route("/logout")
@login_required
def logout():
    """Handle user logout."""
    logger.info(f"User logged out: {current_user.username}")
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("auth.home"))


@auth_bp.route("/change_name", methods=["POST"])
@login_required
def change_name():
    """Change user's full name."""
    new_name = request.form.get("new_name", "").strip()

    if not new_name:
        flash("Name cannot be empty", "error")
        return redirect(url_for("edit_profile"))

    if len(new_name) > 255:
        flash("Name is too long", "error")
        return redirect(url_for("edit_profile"))

    if db.update("users", "id", current_user.id, {"full_name": new_name}):
        current_user.full_name = new_name
        logger.info(f"User {current_user.username} changed name to {new_name}")
        flash("Name updated successfully!", "success")
    else:
        flash("Failed to update name", "error")

    return redirect(url_for("edit_profile"))
