from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = "supersecretkey"  # Required for flash messages and session security
CORS(app)  # Enable CORS

# Initialize Flask extensions
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "home"

# Supabase client setup
SUPABASE_URL = "https://mmtdthmtsasvthysqwrx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1tdGR0aG10c2FzdnRoeXNxd3J4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk2NDYzMTQsImV4cCI6MjA1NTIyMjMxNH0.uxTcUuR2xAs2gQjbA0bqwsRyOVArXY6qD99eo2os9wU"
BUCKET_NAME = "course"

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class User(UserMixin):
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    response = supabase_client.from_("users").select("*").eq("id", user_id).single().execute()
    user_data = response.data
    if user_data:
        return User(user_data["id"], user_data["email"], user_data["password_hash"])
    return None

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    input_password = request.form.get("password")

    response = supabase_client.from_("users").select("*").eq("username", username).single().execute()
    user = response.data
    
    if user and bcrypt.check_password_hash(user["password_hash"], input_password):
        user_obj = User(user["id"], user["email"], user["password_hash"])
        login_user(user_obj)
        flash("Login successful!", "success")
        return redirect(url_for("dashboard"))
    
    else:
        flash("Invalid email or password", "error")
        return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/signup", methods=["POST"])
def signup():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    name = request.form.get("name")
    study_level = request.form.get("study_level")
    year_of_study = request.form.get("year_of_study")
    major = request.form.get("major")
    response = supabase_client.from_("users").select("*").eq("username", username).execute()
    existing_user = response.data[0] if response.data else None
    
    if existing_user:
        flash("User already exists", "error")
        return redirect(url_for("home"))

    if not username:
        flash("Username cannot be empty", "error")
        return redirect(url_for("home"))

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    supabase_client.from_("users").insert([{"username": username, "email": email, "password_hash": hashed_password, "full_name": name, "study_level": study_level, "study_year": year_of_study, "major": major}]).execute()
    
    flash("User created successfully! Please log in.", "success")
    return redirect(url_for("home"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("home"))

@app.route("/edit-profile", methods=["POST", "GET"])
@login_required
def edit_profile():
    if request.method == "POST":
        name = request.form.get("name")
        study_level = request.form.get("study_level")
        year_of_study = request.form.get("year_of_study")
        major = request.form.get("major")

        #optional
        home_country = request.form.get("home_country")
        ethnicity = request.form.get("ethnicity")
        gender = request.form.get("gender")
        academic_goal = request.form.get("academic_goal")

        supabase_client.from_("users").update({"full_name": name, "study_level": study_level, "study_year": year_of_study, "major": major, "home_country": home_country, "ethnicity": ethnicity, "gender": gender, "academic_goal": academic_goal}).eq("id", current_user.id).execute()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("dashboard"))
    
    elif request.method == "GET":
        response = supabase_client.from_("users").select("*").eq("id", current_user.id).single().execute()
        user = response.data
        return render_template("profile.html", user=user)

@app.route("/add-course")
@login_required
def add_course():
    return render_template("add_course.html")

@app.route("/upload-course", methods=["POST"])
@login_required
def upload_course():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    if file and file.filename.endswith(".pdf"):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        with open(file_path, "rb") as f:
            response = supabase_client.storage.from_(BUCKET_NAME).upload(file_path, f, {"content_type": "application/pdf"})

        if response.get("error"):
            return jsonify({"error": response["error"]["message"]}), 500
        
        file_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{filename}"
        supabase_client.table("documents").insert({
            "file_name": filename,
            "file_url": file_url,
            "user_id": current_user.id,  # Use the user_id of the current logged in user
        }).execute()
        os.remove(file_path)
        return jsonify({"message": "File uploaded successfully!"}), 200
    else:
        return jsonify({"error": "Invalid file format"}), 400


if __name__ == "__main__":
    app.run(debug=True)
