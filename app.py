from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_cors import CORS
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")  # Use environment variable for security
CORS(app)  # Enable CORS

# Supabase client setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase Client
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        flash("Email and password are required", "error")
        return redirect(url_for("home"))

    try:
        # Sign in the user with Supabase
        response = supabase_client.auth.sign_in_with_password({"email": email, "password": password})

        if response.session:  # Check session, not user
            session["user"] = {"email": email}
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password", "error")
            return redirect(url_for("home"))
    except Exception as e:
        flash(str(e), "error")
        return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))
    return render_template("dashboard.html")

@app.route("/signup", methods=["POST"])
def signup():
    email = request.form.get("email")
    password = request.form.get("password")
    name = request.form.get("display_name")

    if not email or not password:
        flash("Email and password are required", "error")
        return redirect(url_for("home"))

    try:
        # Sign up the user with Supabase
        response = supabase_client.auth.sign_up({
            "email": email,
            "password": password,
            "data": {"name": name}  # Store name in user metadata
        })

        if response.user:
            # Optional: Store additional user data in a separate "users" table
            supabase_client.table("Users").insert({"email": email, "Display name": name}).execute()
            flash("User created successfully! Please log in.", "success")
            return redirect(url_for("home"))
        else:
            flash("Failed to create user", "error")
            return redirect(url_for("home"))
    except Exception as e:
        flash(str(e), "error")
        return redirect(url_for("home"))
    
@app.route("/courses")
def courses():
    if "user" not in session:
        return redirect(url_for("home"))
    return render_template("courses.html")

@app.route("/tasks")
def tasks():
    if "user" not in session:
        return redirect(url_for("home"))
    return render_template("tasks.html")

@app.route("/logout")
def logout():
    session.pop("user", None)  # Remove user session
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))

@app.route("/profile", methods=["POST", "GET"])
def profile():
    if not supabase_client.auth.user():
        flash("You need to be logged in to edit your profile", "error")
        return redirect(url_for("home"))
    if request.method == "POST":
        name = request.form.get("name")
        study_level = request.form.get("study_level")
        study_year = request.form.get("study_year")
        home_country = request.form.get("home_country")
        ethnicity = request.form.get("ethnicity")
        gender = request.form.get("gender")
        major = request.form.get("major")
        academic_goal = request.form.get("academic_goal")

        if not name:
            flash("Full name is required", "error")
            return redirect(url_for("edit_profile"))

        user = supabase_client.auth.user()
        user_id = user["id"]

        # Update user profile
        response = supabase_client.from_("users").upsert({
            "id": user_id,
            "full_name": name,
            "study_level": study_level,
            "study_year": study_year,
            "home_country": home_country,
            "ethnicity": ethnicity,
            "gender": gender,
            "major": major,
            "academic_goal": academic_goal
        })

        if response["error"]:
            flash(response["error"], "error")
        else:
            flash("Profile updated successfully", "success")

    user = supabase_client.auth.user()
    user_id = user["id"]
    profile = supabase_client.from_("users").select("*").eq("id", user_id).single()
    profile_data = profile.get("data", {})
    for field in ["full_name", "study_level", "study_year", "home_country", "ethnicity", "gender", "major", "academic_goal"]:
        if profile_data.get(field) is None:
            profile_data[field] = ""

    return render_template("profile.html", profile=profile_data)  # Renders the edit profile page



if __name__ == "__main__":
    app.run(debug=True)
