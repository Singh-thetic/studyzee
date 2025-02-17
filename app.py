from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from pdf_parse import *
import shutil
import time
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from study_assist import *
import secrets
import json
# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = "supersecretkey"  # Required for flash messages and session security
CORS(app)  # Enable CORS
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable WebSocket support

# Initialize Flask extensions
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "home"

# Supabase client setup
SUPABASE_URL = "https://mmtdthmtsasvthysqwrx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1tdGR0aG10c2FzdnRoeXNxd3J4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczOTY0NjMxNCwiZXhwIjoyMDU1MjIyMzE0fQ.uUo4VvRjUKmL-mx5MpN_I6K4lgMQUz_ctb26OHNd3ak"
BUCKET_NAME = "course"
os.makedirs("static/uploads", exist_ok=True)

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
course_data = {}

level_dict = {"undergraduate": "Undergraduate", "masters": "Masters", "phd": "PhD"}
major_dict = {
    "business-management": "Business & Management",
    "cs-it-data-science": "Computer Science, IT & Data Science",
    "engineering-technology": "Engineering & Technology",
    "mathematics-statistics": "Mathematics & Statistics",
    "natural-environmental-sciences": "Natural Sciences & Environmental Studies",
    "health-sciences-medicine": "Health Sciences, Nursing & Medicine",
    "pharmacy-pharmaceutical-sciences": "Pharmacy & Pharmaceutical Sciences",
    "education-teaching": "Education & Teaching",
    "law-legal-studies": "Law & Legal Studies",
    "social-sciences-humanities": "Social Sciences & Humanities",
    "economics-finance": "Economics & Finance",
    "architecture-urban-planning": "Architecture & Urban Planning",
    "fine-arts-design": "Fine Arts & Design",
    "communications-media-studies": "Communications & Media Studies",
    "agriculture-forestry": "Agriculture & Forestry",
    "hospitality-tourism": "Hospitality & Tourism"
}

COUNTRIES = [
    "Afghanistan",
    "Albania",
    "Algeria",
    "Andorra",
    "Angola",
    "Antigua and Barbuda",
    "Argentina",
    "Armenia",
    "Australia",
    "Austria",
    "Azerbaijan",
    "Bahamas",
    "Bahrain",
    "Bangladesh",
    "Barbados",
    "Belarus",
    "Belgium",
    "Belize",
    "Benin",
    "Bhutan",
    "Bolivia (Plurinational State of)",
    "Bosnia and Herzegovina",
    "Botswana",
    "Brazil",
    "Brunei Darussalam",
    "Bulgaria",
    "Burkina Faso",
    "Burundi",
    "Côte d'Ivoire",
    "Cabo Verde",
    "Cambodia",
    "Cameroon",
    "Canada",
    "Central African Republic",
    "Chad",
    "Chile",
    "China",
    "Colombia",
    "Comoros",
    "Congo",
    "Costa Rica",
    "Croatia",
    "Cuba",
    "Cyprus",
    "Czechia (Czech Republic)",
    "Democratic People's Republic of Korea",
    "Democratic Republic of the Congo",
    "Denmark",
    "Djibouti",
    "Dominica",
    "Dominican Republic",
    "Ecuador",
    "Egypt",
    "El Salvador",
    "Equatorial Guinea",
    "Eritrea",
    "Estonia",
    "Eswatini",
    "Ethiopia",
    "Fiji",
    "Finland",
    "France",
    "Gabon",
    "Gambia",
    "Georgia",
    "Germany",
    "Ghana",
    "Greece",
    "Grenada",
    "Guatemala",
    "Guinea",
    "Guinea-Bissau",
    "Guyana",
    "Haiti",
    "Honduras",
    "Hungary",
    "Iceland",
    "India",
    "Indonesia",
    "Iran (Islamic Republic of)",
    "Iraq",
    "Ireland",
    "Israel",
    "Italy",
    "Jamaica",
    "Japan",
    "Jordan",
    "Kazakhstan",
    "Kenya",
    "Kiribati",
    "Kuwait",
    "Kyrgyzstan",
    "Lao People's Democratic Republic",
    "Latvia",
    "Lebanon",
    "Lesotho",
    "Liberia",
    "Libya",
    "Liechtenstein",
    "Lithuania",
    "Luxembourg",
    "Madagascar",
    "Malawi",
    "Malaysia",
    "Maldives",
    "Mali",
    "Malta",
    "Marshall Islands",
    "Mauritania",
    "Mauritius",
    "Mexico",
    "Micronesia (Federated States of)",
    "Monaco",
    "Mongolia",
    "Montenegro",
    "Morocco",
    "Mozambique",
    "Myanmar",
    "Namibia",
    "Nauru",
    "Nepal",
    "Netherlands",
    "New Zealand",
    "Nicaragua",
    "Niger",
    "Nigeria",
    "Niue",
    "North Macedonia",
    "Norway",
    "Oman",
    "Pakistan",
    "Palau",
    "Panama",
    "Papua New Guinea",
    "Paraguay",
    "Peru",
    "Philippines",
    "Poland",
    "Portugal",
    "Qatar",
    "Republic of Korea",
    "Republic of Moldova",
    "Romania",
    "Russian Federation",
    "Rwanda",
    "Saint Kitts and Nevis",
    "Saint Lucia",
    "Saint Vincent and the Grenadines",
    "Samoa",
    "San Marino",
    "Sao Tome and Principe",
    "Saudi Arabia",
    "Senegal",
    "Serbia",
    "Seychelles",
    "Sierra Leone",
    "Singapore",
    "Slovakia",
    "Slovenia",
    "Solomon Islands",
    "Somalia",
    "South Africa",
    "South Sudan",
    "Spain",
    "Sri Lanka",
    "Sudan",
    "Suriname",
    "Sweden",
    "Switzerland",
    "Syrian Arab Republic",
    "Tajikistan",
    "Thailand",
    "Timor-Leste",
    "Togo",
    "Tonga",
    "Trinidad and Tobago",
    "Tunisia",
    "Türkiye (Turkey)",
    "Turkmenistan",
    "Tuvalu",
    "Uganda",
    "Ukraine",
    "United Arab Emirates",
    "United Kingdom of Great Britain and Northern Ireland",
    "United Republic of Tanzania",
    "United States of America",
    "Uruguay",
    "Uzbekistan",
    "Vanuatu",
    "Venezuela (Bolivarian Republic of)",
    "Viet Nam",
    "Yemen",
    "Zambia",
    "Zimbabwe"
]

ETHNICITIES = [
    "Asian",
    "Black",
    "Hispanic/Latino",
    "White",
    "South Asian",
    "Middle Eastern/North African",
    "Indigenous American",
    "Pacific Islander",
    "Jewish",
    "African",
    "East Asian",
    "Central Asian",
    "Caribbean",
    "Other"
]

GOALS = [
    "Graduate with honors",
    "Get a research position",
    "Start a business",
    "Pursue higher education",
    "Secure a job in my field",
    "Develop technical skills",
    "Gain international experience",
    "Contribute to community service",
    "Publish academic papers",
    "Network with professionals",
    "Other"
]


class User(UserMixin):
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    response = supabase_client.from_("users").select("*").eq("id", user_id).maybe_single().execute()
    user_data = response.data if response else None
    if user_data:
        return User(user_data["id"], user_data["email"], user_data["password_hash"])
    return None


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    input_password = request.form.get("password")

    response = supabase_client.from_("users").select("*").eq("username", username).maybe_single().execute()
    user = response.data if response else None
    
    if user and bcrypt.check_password_hash(user["password_hash"], input_password):
        user_obj = User(user["id"], user["email"], user["password_hash"])
        login_user(user_obj)
        flash("Login successful!", "success")
        return redirect(url_for("dashboard"))
    
    else:
        return render_template(("login.html"), error="Invalid username or password")


@app.route("/signup", methods=["POST"])
def signup():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    if password != confirm_password:
        return render_template("login.html", stage="signup", error="Passwords do not match")
    name = request.form.get("full_name")
    study_level = request.form.get("study_level")
    year_of_study = request.form.get("year_of_study")
    major = request.form.get("major")
    response = supabase_client.from_("users").select("*").eq("username", username).execute()
    existing_user = response.data[0] if response and response.data else None
    
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

@app.route("/edit_profile", methods=["POST", "GET"])
@login_required
def edit_profile():
    if request.method == "POST":
        study_level = request.form.get("study_level")
        year_of_study = request.form.get("year_of_study")
        major = request.form.get("major")

        #optional
        home_country = request.form.get("home_country")
        ethnicity = request.form.get("ethnicity")
        gender = request.form.get("gender")
        academic_goal = request.form.get("academic_goal")


        supabase_client.from_("users").update({"study_level": study_level, "study_year": year_of_study, "major": major, "home_country": home_country, "ethnicity": ethnicity, "gender": gender, "academic_goal": academic_goal}).eq("id", current_user.id).execute()
        response = supabase_client.from_("users").select("*").eq("id", current_user.id).maybe_single().execute()
        user = response.data
        return render_template("profile.html", user=user)
    
    elif request.method == "GET":
        response = supabase_client.from_("users").select("*").eq("id", current_user.id).maybe_single().execute()
        user = response.data
        return render_template("profile.html", user=user)
    
@app.route("/change_name", methods=["POST"])
@login_required
def change_name():
    new_name = request.form.get("new_name")
    supabase_client.from_("users").update({"full_name": new_name}).eq("id", current_user.id).execute()
    return redirect(url_for("edit_profile"))

@app.route("/add_course", methods=["GET", "POST"])
@login_required
def add_course():
    if request.method == "POST":
        global course_data
        # Handle the POST request here
        subject = request.form.get("subject")
        course_code = request.form.get("course_code")
        course_data = {'subject': subject, 'course_code': course_code}
        return render_template("add_course.html", stage=2, course_data=course_data)

    return render_template("add_course.html", stage=1)


@app.route("/upload_course", methods=["POST"])
@login_required
def upload_course():
    if "files" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    files = request.files.getlist("files")
    if not files or len(files) == 0:
        return jsonify({"error": "No file selected"}), 400
    
    uploaded_files = []
    for file in files:
        if file and file.filename.endswith(".pdf"):
            filename = secure_filename(file.filename)
            UPLOAD_FOLDER = f"static/uploads/{current_user.id}"
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            with open(file_path, "rb") as f:
                response = supabase_client.storage.from_(BUCKET_NAME).upload(file_path, f, {"content_type": "application/pdf"})
            # Convert response to dictionary (if necessary)
            res_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            if isinstance(res_dict, dict) and "error" in res_dict and res_dict["error"]:
                return jsonify({"error": "Upload failed", "details": res_dict["error"]}), 500
            
            file_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{filename}"
            supabase_client.table("documents").insert({
                "file_name": filename,
                "file_url": file_url,
                "user_id": current_user.id,  # Use the user_id of the current logged in user
            }).execute()
            temp_folder = f"static/uploads/{current_user.id}/temp"
            if not os.path.exists(temp_folder):
                os.makedirs(temp_folder)
            temp_file_path = os.path.join(temp_folder, filename)
            shutil.copy(file_path, temp_file_path)

            uploaded_files.append(temp_file_path)
            os.remove(file_path)

        else:
            return jsonify({"error": "Invalid file format"}), 400
    global course_data
    return redirect(url_for("confirm_course", course_data=course_data, uploaded_files=uploaded_files))

@app.route("/confirm_course", methods=["GET", "POST"])
@login_required
def confirm_course():
    global course_data
    if request.method == "POST":
        section = request.form.get("section")
        if section:
            course_data = {section: course_data[section]}
            return render_template("add_course.html", course_data=course_data, stage=4)
        else:
            for key, value in course_data.items():
                course_data[key]['subject_id'] = request.form.get(f"{key}_subject")
                course_data[key]['course_code'] = request.form.get(f"{key}_code")
                course_data[key]['professor_email'] = request.form.get(f"{key}_email")
                course_data[key]['professor'] = request.form.get(f"{key}_name")
                course_data[key]['class_schedule'] = request.form.getlist(f"{key}_days")

                for w_key in value['WeightageTable'].keys():
                    due_date = request.form.get(f"{key}_{w_key}_due_date")
                    due_time = request.form.get(f"{key}_{w_key}_due_time")
                    course_data[key]['WeightageTable'][w_key]['due_date'] = due_date if due_date != "TBD" else None
                    course_data[key]['WeightageTable'][w_key]['due_time'] = due_time if due_time != "TBD" else None
                    course_data[key]['WeightageTable'][w_key]['weightage'] = request.form.get(f"{key}_{w_key}_weight")

            print(course_data)  # Debugging print statement
            
            for details in course_data.values():
                existing_course = supabase_client.table("course").select("course_id") \
                                .ilike("section", f"%{details.get('section', '')}%") \
                                .ilike("course_code", f"%{details.get('course_code', '')}%") \
                                .ilike("subject_id", f"%{details.get('subject_id', '')}%") \
                                .ilike("professor", f"%{details.get('professor', '')}%") \
                                .maybe_single().execute()

                if existing_course and existing_course.data:
                    course_id = existing_course.data["course_id"]
                else:
                    course_insert = {
                        "subject_id": details.get("subject_id", "Unknown")[:10],
                        "course_code": details.get("course_code", "Unknown")[:10],
                        "term": details.get("term", "Unknown Term")[:10],
                        "year": details.get("year", 2025),
                        "section": key,
                        "course_name": details.get("course_name", "Unknown Course"),
                        "professor": details.get("professor", "Unknown"),
                        "class_schedule": ",".join(details.get("class_schedule", []))[:100],
                        "professor_email": details.get("professor_email", "Unknown")[:100],
                    }
                    try:
                        response = supabase_client.table("course").insert(course_insert).execute()
                        if response.data:
                            course_id = response.data[0]["course_id"]
                    except Exception as e:
                        if 'duplicate key value violates unique constraint' in str(e):
                            existing_course = supabase_client.table("course").select("course_id") \
                                .ilike("course_code", f"%{details.get('course_code', '')}%") \
                                .ilike("subject_id", f"%{details.get('subject_id', '')}%") \
                                .ilike("section", f"%{details.get('section', '')}%") \
                                .ilike("professor", f"%{details.get('professor', '')}%") \
                                .maybe_single().execute()
                            if existing_course and existing_course.data:
                                course_id = existing_course.data["course_id"]
                            else:
                                raise ValueError("Course exists but could not fetch course_id")
                        else:
                            raise e

                    if response and response.data:
                        course_id = response.data[0]["course_id"]

                supabase_client.table("user_courses").insert({"user_id": current_user.id, "course_id": course_id}).execute()

                for work_name, work_data in details["WeightageTable"].items():
                    existing_work = supabase_client.table("work_template").select("work_id").eq("course_id", course_id).eq("name", work_name).execute()
                    
                    if existing_work.data:
                        work_id = existing_work.data[0]["work_id"]
                    else:
                        work_date = work_data.get("due_date")
                        if work_date in ["TBD", ""]:
                            work_date = None
                        work_time = work_data.get("due_time")
                        if work_time in ["TBD", ""]:
                            work_time = None
                        work_insert = {
                            "course_id": course_id,
                            "name": work_name,
                            "weightage": float(work_data.get("weightage", 0)),
                            "due_date": work_date,
                            "due_time": work_time,
                        }
                        work_response = supabase_client.table("work_template").insert(work_insert).execute()
                        if work_response.data:
                            work_id = work_response.data[0]["work_id"]

                        assigned_work = {
                            "user_id": current_user.id,
                            "work_id": work_id,
                            "course_id": course_id,
                            "weightage": float(work_data.get("weightage", 0)),
                            "due_date": work_date,
                            "due_time": work_time,
                            "done": False,
                        }
                        supabase_client.table("assigned_work").insert(assigned_work).execute()

        return redirect(url_for("dashboard"))
    else:
        course_data = request.args.get("course_data")
        if course_data:
            course_data = eval(course_data)
        else:
            flash("Course data is missing", "error")
            return redirect(url_for("add_course"))

        uploaded_files = request.args.getlist("uploaded_files")
        course_information = course_info(uploaded_files)
        for course in course_information:
            course_information[course] = {
                'course_code': course_data.get('course_code', 'Unknown'),
                'subject': course_data.get('subject', 'Unknown'),
                **course_information[course]
            }
        course_data = course_information
        print(course_data)
    
    if len(course_data) > 1:
        return render_template("add_course.html", course_data=course_data, stage=3)
    else:
        return render_template("add_course.html", course_data=course_data, stage=4)


@app.route("/dashboard")
@login_required
def dashboard():
    user_data = supabase_client.from_("users").select("*").eq("id", current_user.id).maybe_single().execute().data
    user_data["major"] = major_dict[user_data["major"]]
    user_data["study_level"] = level_dict[user_data["study_level"]]
    user_courses = supabase_client.from_("user_courses").select("course_id").eq("user_id", current_user.id).execute().data
    course_ids = [course["course_id"] for course in user_courses]
    if course_ids:
        course_d = supabase_client.from_("course").select("subject_id, course_code").in_("course_id", course_ids).execute().data
    else:
        course_d = []
    
    courses = [f"{d.get('subject_id')} {d.get('course_code')}" for d in course_d]
    
    task = supabase_client.from_("tasks").select("*").eq("user_id", current_user.id).eq("done", False).execute().data
    assigned_work = supabase_client.from_("assigned_work").select("*, work_template(name)").eq("user_id", current_user.id).eq("done", False).execute().data
    tasks = []
    for t in task:
        tasks.append([t.get("task_name"), t.get("due_date"), t.get("done"), t.get("task_id"), "task"])
    for a in assigned_work:
        tasks.append([a.get("work_template").get("name"), a.get("due_date"), a.get("done"), a.get("id"), "work"])
    user_courses = supabase_client.from_("user_courses").select("course_id").eq("user_id", current_user.id).execute().data
    course_ids = [course["course_id"] for course in user_courses]
    if course_ids:
        course_data = supabase_client.from_("course").select("course_id, subject_id, course_code").in_("course_id", course_ids).execute().data
    else:
        course_data = []

    courses = [{"subject_id": c["subject_id"],"course_code": c["course_code"]} for c in course_data]

    return render_template("dashboard.html", user_data=user_data, courses=courses, tasks=tasks)

@app.route("/delete_course")
@login_required
def delete_course():
    return render_template("delete_course.html")


@app.route("/complete_task", methods=["GET", "POST"])
@login_required
def complete_task():
    task_id = request.args.get("task_id")  # Use args for GET requests
    task_type = request.args.get("type")   # Get type from URL parameters

    if not task_id or not task_type:
        return redirect(url_for("dashboard"))  # Handle missing data safely

    if task_type == "task":
        supabase_client.from_("tasks").update({"done": True}).eq("task_id", task_id).execute()
    elif task_type == "work":
        supabase_client.from_("assigned_work").update({"done": True}).eq("id", task_id).execute()

    return redirect(url_for("dashboard"))

@app.route('/update_pic', methods=["POST"])
@login_required
def update_pic():
    if "profile_pic" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["profile_pic"]
    if file.filename == "":
        flash("No selected file", "error")
        return redirect(url_for("edit_profile"))

    if file and file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        filename = f"{current_user.id}_{secure_filename(file.filename)}"
        UPLOAD_FOLDER = f"static/profile_pics"
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        with open(file_path, "rb") as f:
            response = supabase_client.storage.from_("pictures").upload(filename, f)

        res_dict = response.model_dump() if hasattr(response, 'model_dump') else response
        if isinstance(res_dict, dict) and "error" in res_dict and res_dict["error"]:
            flash("Upload failed", "error")
            return redirect(url_for("edit_profile"))

        file_url = f"{SUPABASE_URL}/storage/v1/object/public/pictures/{filename}"
        supabase_client.from_("users").update({"profile_picture": file_url}).eq("id", current_user.id).execute()

        flash("Profile picture updated successfully!", "success")
        return redirect(url_for("edit_profile"))

    else:
        flash("Invalid file format", "error")
        return redirect(url_for("edit_profile"))




@socketio.on('message')
def handle_message(msg):
    """Handles real-time messages from clients."""
    print(f"Message received: {msg}")
    send(msg, broadcast=True)  # Broadcast to all clients

@socketio.on('custom_event')
def handle_custom_event(data):
    """Handles custom events with JSON data."""
    print(f"Received data: {data}")
    emit('response_event', {'message': 'Hello from server!'}, broadcast=True)

@socketio.on('join_room')
def handle_join_room(data):
    """Handles users joining a chat room."""
    room = data["room"]
    join_room(room)

@socketio.on('send_message')
def handle_send_message(data):
    """Handles sending messages in a room and storing them in Supabase."""
    room = data["room"]
    message = data["message"]
    user_id = data["sender_id"]  # Ensure sender_id is passed correctly

    # Store message in Supabase
    response = supabase_client.from_("chat_messages").insert({
        "room": room,
        "message": message,
        "sender_id": user_id
    }).execute()

    # Extract message ID if storage was successful
    if response.data:
        message_id = response.data[0]["id"]
    else:
        message_id = f"{user_id}-{int(time.time())}"  # Fallback in case of error

    # Emit the message to other users in the room, excluding the sender
    emit("receive_message", {
        "message": message,
        "sender_id": user_id,
        "message_id": message_id
    }, room=room, include_self=False)


@app.route("/")
def home():
    return render_template("login.html", stage="login")

@app.route("/chat")
@login_required
def chat():
    """Renders the chat page for a specific room."""
    room_code = request.args.get("room")  # Get the room code from the URL

    if not room_code:
        flash("Invalid chat room!", "error")
        return redirect(url_for("dashboard"))

    # Validate that the user is part of the room
    chat_room = supabase_client.from_("private_chat_rooms").select("*") \
        .eq("room_code", room_code) \
        .maybe_single().execute()

    if not chat_room:
        flash("Chat room does not exist!", "error")
        return redirect(url_for("dashboard"))

    # Check if the user is allowed in this chat
    if current_user.id not in [chat_room.data["user1_id"], chat_room.data["user2_id"]]:
        flash("You are not authorized to access this chat room!", "error")
        return redirect(url_for("dashboard"))
    
    friend_id = chat_room.data["user1_id"] if chat_room.data["user1_id"] != current_user.id else chat_room.data["user2_id"]
    friend_name_response = supabase_client.from_("users").select("full_name").eq("id", friend_id).maybe_single().execute()
    friend_name = friend_name_response.data["full_name"] if friend_name_response.data else "Your Friend"
    friend_profile_pic_response = supabase_client.from_("users").select("profile_picture").eq("id", friend_id).maybe_single().execute()
    friend_profile_pic = friend_profile_pic_response.data["profile_picture"] if friend_profile_pic_response.data else "https://mmtdthmtsasvthysqwrx.supabase.co/storage/v1/object/public/pictures//default-pfp.jpg"

    return render_template("chat.html", room_code=room_code, user_id=current_user.id, friend_name=friend_name, friend_pfp=friend_profile_pic)


@app.route("/send_friend_request", methods=["POST"])
@login_required
def send_friend_request():
    data = request.json
    receiver_id = data.get("receiver_id")
    message = data.get("message", "")

    # Ensure request is not duplicated
    existing_request = supabase_client.from_("friend_requests") \
        .select("*").eq("sender_id", current_user.id).eq("receiver_id", receiver_id).maybe_single().execute()

    if existing_request:
        return jsonify({"error": "Friend request already sent"}), 400

    # Store friend request
    supabase_client.from_("friend_requests").insert({
        "sender_id": current_user.id,
        "receiver_id": receiver_id,
        "message": message,
        "status": "pending"
    }).execute()

    # Notify receiver
    supabase_client.from_("notifications").insert({
        "user_id": receiver_id,
        "type": "friend_request",
        "message": f"You have a new friend request from {current_user.email}"
    }).execute()

    return jsonify({"message": "Friend request sent!"}), 200

@app.route("/respond_friend_request", methods=["POST"])
@login_required
def respond_friend_request():
    data = request.json
    request_id = data.get("request_id")
    response = data.get("response")  # "accepted" or "rejected"

    print(f"DEBUG: Received request_id={request_id}, response={response}")

    if not request_id:
        return jsonify({"error": "Invalid request ID"}), 400

    # Fetch request details
    friend_request = supabase_client.from_("friend_requests").select("*").eq("id", request_id).execute()

    if not friend_request.data or len(friend_request.data) == 0:
        print("DEBUG: Friend request not found in database")
        return jsonify({"error": "Friend request not found"}), 404

    friend_request = friend_request.data[0]
    sender_id = friend_request["sender_id"]

    if response == "accepted":
        # Generate unique chat room code
        room_code = f"chat_{min(current_user.id, sender_id)}_{max(current_user.id, sender_id)}"
        print(f"DEBUG: Generated room_code={room_code}")

        # Store the friendship
        supabase_client.from_("friends").insert({
            "user1_id": current_user.id,
            "user2_id": sender_id,
            "chat_room_code": room_code
        }).execute()

        # Check if a room with the same room code already exists to avoid duplicates
        existing_room = supabase_client.from_("private_chat_rooms").select("room_code") \
            .eq("room_code", room_code) \
            .maybe_single().execute()

        if not existing_room:
            print("DEBUG: Creating new chat room in private_chat_rooms")
            supabase_client.from_("private_chat_rooms").insert({
                "user1_id": current_user.id,
                "user2_id": sender_id,
                "room_code": room_code
            }).execute()
        else:
            print(f"DEBUG: kk Chat room already exists for {room_code}")

        # Notify sender
        supabase_client.from_("notifications").insert({
            "user_id": sender_id,
            "type": "friend_request",
            "message": f"{current_user.email} accepted your friend request!"
        }).execute()

    # Update friend request status
    update_response = supabase_client.from_("friend_requests").update({"status": response}).eq("id", request_id).execute()

    print(f"DEBUG: Update response for friend_requests: {update_response}")

    return jsonify({"message": f"Friend request {response}!"}), 200


# @app.route("/suggested_friends", methods=["GET"])
# @login_required
# def suggested_friends():
#     # Get the current user's enrolled courses
#     user_courses_response = supabase_client.from_("user_courses").select("course_id") \
#         .eq("user_id", current_user.id).execute()

#     user_course_ids = {uc["course_id"] for uc in user_courses_response.data} if user_courses_response.data else set()

#     if not user_course_ids:
#         return jsonify({"suggestions": []})

#     # Find users in the same courses
#     same_course_users_response = supabase_client.from_("user_courses").select("user_id") \
#         .in_("course_id", list(user_course_ids)).execute()

#     same_course_user_ids = {user["user_id"] for user in same_course_users_response.data} if same_course_users_response.data else set()

#     # Remove already friends and pending requests
#     existing_friends = supabase_client.from_("friends").select("user2_id") \
#         .eq("user1_id", current_user.id).execute()
#     friend_ids = {friend["user2_id"] for friend in existing_friends.data} if existing_friends.data else set()

#     pending_requests = supabase_client.from_("friend_requests").select("receiver_id") \
#         .eq("sender_id", current_user.id).execute()
#     pending_ids = {req["receiver_id"] for req in pending_requests.data} if pending_requests.data else set()

#     exclude_ids = friend_ids | pending_ids | {current_user.id}

#     # Filter out users who are already friends, pending, or themselves
#     potential_friends = same_course_user_ids - exclude_ids

#     if not potential_friends:
#         return jsonify({"suggestions": []})

#     # Get user details for potential friends
#     response = supabase_client.from_("users").select("id, email, full_name") \
#         .in_("id", list(potential_friends)).limit(5).execute()

#     return jsonify({"suggestions": response.data if response.data else []})


@app.route("/friend_requests", methods=["GET"])
@login_required
def get_friend_requests():
    """Fetches all pending friend requests for the current user."""
    response = supabase_client.from_("friend_requests").select("id, sender_id, message") \
        .eq("receiver_id", current_user.id).eq("status", "pending").execute()

    if not response.data:
        return jsonify({"requests": []})

    friend_requests = []
    for req in response.data:
        sender_data = supabase_client.from_("users").select("email").eq("id", req["sender_id"]).maybe_single().execute()
        sender_email = sender_data.data["email"] if sender_data.data else "Unknown User"

        friend_requests.append({
            "id": req["id"],
            "sender_email": sender_email,
            "message": req["message"]
        })

    return jsonify({"requests": friend_requests})


@app.route("/friends_list", methods=["GET"])
@login_required
def friends_list():
    response = supabase_client.from_("friends").select("*") \
        .or_(f"user1_id.eq.{current_user.id},user2_id.eq.{current_user.id}").execute()

    friends = []
    for f in response.data:
        friend_id = f["user2_id"] if f["user1_id"] == current_user.id else f["user1_id"]
        friend_data = supabase_client.from_("users").select("id, username").eq("id", friend_id).maybe_single().execute()
        friends.append({"id": friend_data.data["id"], "username": friend_data.data["username"], "room_code": f["chat_room_code"]})

    return jsonify({"friends": friends})

# Update the chat_history endpoint to include sender_id
@app.route("/chat_history/<room_code>")
@login_required
def chat_history(room_code):
    messages_response = supabase_client.from_("chat_messages").select("message, sender_id, id") \
        .eq("room", room_code).execute()
    
    messages = [{"message": msg["message"], "sender_id": msg["sender_id"], "message_id": msg["id"]} 
               for msg in messages_response.data] if messages_response.data else []

    return jsonify({"messages": messages})

@socketio.on("send_message")
def handle_private_message(data):
    room = data["room"]
    message = data["message"]

    # Store message
    supabase_client.from_("chat_messages").insert({
        "room": room,
        "message": message,
        "sender_id": current_user.id
    }).execute()

    # Notify friend
    friend_id = supabase_client.from_("friends").select("user1_id, user2_id") \
        .eq("chat_room_code", room).maybe_single().execute()
    receiver_id = friend_id.data["user1_id"] if friend_id.data["user2_id"] == current_user.id else friend_id.data["user2_id"]

    supabase_client.from_("notifications").insert({
        "user_id": receiver_id,
        "type": "message",
        "message": "New message from " + current_user.email
    }).execute()

    emit("receive_message", {"message": message}, room=room)


@app.route("/practice/<set_id>")
def practice_flashcards(set_id):
    print(f"Received set_id: {set_id}")  # Debugging output

    # Ensure set_id is a valid UUID
    if not set_id or set_id == "undefined":
        return jsonify({"error": "Invalid set_id"}), 400

    try:
        response = supabase_client.table('flashcards').select('question', 'answer').eq('set_id', set_id).execute()
        flashcards = response.data if response.data else []
        flashcards = [{"question": card["question"], "answer": card["answer"]} for card in flashcards]

        return render_template('practice.html', flashcards=flashcards)
    
    except Exception as e:
        print(f"Database query error: {e}") 

@app.route("/flashcards")
def flashcards():
    return render_template("flashcards.html")


@app.route('/flashcard-sets')
def get_flashcard_sets():
    user_id = current_user.id
    response = supabase_client.table('flashcard_sets').select('*').eq('user_id', user_id).execute()
    sets = response.data if response.data else []
    return jsonify({"sets": sets})

@app.route('/flashcards/<set_id>')
def get_flashcards(set_id):
    response = supabase_client.table('flashcards').select('*').eq('set_id', set_id).execute()
    flashcards = response.data if response.data else []
    return jsonify({"flashcards": flashcards})

@app.route('/upload-notes', methods=['POST'])
def upload_notes():
    if 'notes_file' not in request.files:
        return jsonify({"message": "No file uploaded"}), 400

    os.makedirs("uploads", exist_ok=True)
    notes_file = request.files['notes_file']
    filename = secure_filename(notes_file.filename)
    file_path = os.path.join("uploads", filename)
    notes_file.save(file_path)

    # Upload the file to the Supabase bucket
    with open(file_path, "rb") as f:
        response = supabase_client.storage.from_("course").upload(filename, f)

    res_dict = response.model_dump() if hasattr(response, 'model_dump') else response
    if isinstance(res_dict, dict) and "error" in res_dict and res_dict["error"]:
        return jsonify({"error": "Upload failed", "details": res_dict["error"]}), 500

    # AI model generates flashcards from the notes
    flashcards = generate_flashcards(file_path)

    # Store flashcards in Supabase
    response = supabase_client.table('flashcard_sets').insert({
        "user_id": current_user.id,  # Use the actual user ID from the current session
        "name": request.form.get("set_name", "Untitled Set")
    }).execute()

    set_id = response.data[0]['set_id']  # Get the auto-generated set_id from the response

    for i, card in enumerate(flashcards):
        supabase_client.table('flashcards').insert({
            "set_id": set_id,
            "question_no": i + 1,
            "question": card[0],
            "answer": card[1]
        }).execute()


    return jsonify({"message": "Flashcards generated and saved!"})

@app.route("/meet_new_friends")
@login_required
def meet_new_friends():
    return render_template('meet_new_friends.html')

@app.route("/suggested_friends", methods=["GET"])
@login_required
def suggested_friends():
    """Suggest users based on ethnicity, study level, major, and courses (not mandatory)."""

    # Get current user's details
    user_data_response = supabase_client.from_("users").select("ethnicity, study_level, major") \
        .eq("id", current_user.id).maybe_single().execute()

    if not user_data_response.data:
        return jsonify({"suggestions": []})

    user_ethnicity = user_data_response.data["ethnicity"]
    user_study_level = user_data_response.data["study_level"]
    user_major = user_data_response.data["major"]

    # Step 1: Find users based on **ethnicity, study level, or major** (Higher priority)
    similar_users_response = supabase_client.from_("users").select("id") \
        .or_(f"ethnicity.eq.{user_ethnicity}, study_level.eq.{user_study_level}, major.eq.{user_major}") \
        .neq("id", current_user.id).execute()

    similar_users_ids = {user["id"] for user in similar_users_response.data} if similar_users_response.data else set()

    # Step 2: Find users in the same courses (Lower priority)
    user_courses_response = supabase_client.from_("user_courses").select("course_id") \
        .eq("user_id", current_user.id).execute()

    user_course_ids = {uc["course_id"] for uc in user_courses_response.data} if user_courses_response.data else set()

    same_course_user_ids = set()
    if user_course_ids:
        same_course_users_response = supabase_client.from_("user_courses").select("user_id") \
            .in_("course_id", list(user_course_ids)).execute()

        same_course_user_ids = {user["user_id"] for user in same_course_users_response.data} if same_course_users_response.data else set()

    # Merge users from both sources
    potential_friends = similar_users_ids | same_course_user_ids

    # Step 3: Remove already friends and pending requests
    existing_friends = supabase_client.from_("friends").select("user2_id") \
        .eq("user1_id", current_user.id).execute()
    friend_ids = {friend["user2_id"] for friend in existing_friends.data} if existing_friends.data else set()

    pending_requests = supabase_client.from_("friend_requests").select("receiver_id") \
        .eq("sender_id", current_user.id).execute()
    pending_ids = {req["receiver_id"] for req in pending_requests.data} if pending_requests.data else set()

    exclude_ids = friend_ids | pending_ids | {current_user.id}
    potential_friends -= exclude_ids

    if not potential_friends:
        return jsonify({"suggestions": []})

    # Step 4: Fetch details of suggested users
    response = supabase_client.from_("users").select("id, email, full_name, ethnicity, study_level, major") \
        .in_("id", list(potential_friends)).limit(10).execute()

    suggestions = []
    for user in response.data:
        match_reasons = []

        if user["ethnicity"] == user_ethnicity:
            match_reasons.append("Same ethnicity")

        if user["study_level"] == user_study_level:
            match_reasons.append("Same year of study")

        if user["major"] == user_major:
            match_reasons.append("Same major")

        if user["id"] in same_course_user_ids:
            match_reasons.append("You share a course")

        suggestions.append({
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "match_reason": ", ".join(match_reasons)
        })

    return jsonify({"suggestions": suggestions})

@app.route("/group_chat")
@login_required
def group_chat():
    """
    Renders the group chat page if the user is a member
    of the group associated with the given room_key.
    URL pattern example: /group_chat?room_key=<roomKey>
    """
    room_key = request.args.get("room_key")
    if not room_key:
        flash("Missing room key for group chat!", "error")
        return redirect(url_for("dashboard"))

    # Check if this room_key exists in group_chatrooms
    room_response = supabase_client.from_("group_chatrooms") \
        .select("*") \
        .eq("room_key", room_key) \
        .maybe_single() \
        .execute()

    if not room_response.data:
        flash("This group chat room does not exist!", "error")
        return redirect(url_for("dashboard"))

    chatroom_data = room_response.data
    study_group_id = chatroom_data["study_group_id"]

    # Check if current_user is part of this group
    membership_response = supabase_client.from_("group_members") \
        .select("id") \
        .eq("study_group_id", study_group_id) \
        .eq("user_id", current_user.id) \
        .maybe_single() \
        .execute()

    if not membership_response.data:
        flash("You are not a member of this study group!", "error")
        return redirect(url_for("dashboard"))

    # Optionally fetch group name & icon from study_groups
    group_response = supabase_client.from_("study_groups") \
        .select("name, description") \
        .eq("id", study_group_id) \
        .maybe_single() \
        .execute()

    group_name = group_response.data["name"] if group_response.data else "Study Group"
    group_icon = None  # or fetch from your DB

    users = supabase_client.from_("group_members").select("user_id") \
        .eq("study_group_id", study_group_id).execute().data
    user_ids = [user["user_id"] for user in users]
    users = supabase_client.from_("users").select("id, username") \
        .in_("id", user_ids).execute().data
    users = {user["id"]: user for user in users}

    return render_template(
        "groupchat.html",
        room_key=room_key,
        user_id=current_user.id,
        group_name=group_name,
        group_icon=group_icon,
        users_json=json.dumps(users)
    )

@app.route("/group_chat_history/<room_key>")
@login_required
def group_chat_history(room_key):
    """
    Returns a JSON list of messages for the specified group chat room.
    """
    # Validate the group chat exists
    room_response = supabase_client.from_("group_chatrooms") \
        .select("id, study_group_id") \
        .eq("room_key", room_key) \
        .maybe_single() \
        .execute()

    if not room_response.data:
        return jsonify({"messages": []})  # Or raise an error

    chatroom_id = room_response.data["id"]
    study_group_id = room_response.data["study_group_id"]

    # Ensure user is a member
    membership_response = supabase_client.from_("group_members") \
        .select("id") \
        .eq("study_group_id", study_group_id) \
        .eq("user_id", current_user.id) \
        .maybe_single() \
        .execute()

    if not membership_response.data:
        return jsonify({"messages": []})  # Or raise an error

    # Fetch messages from group_messages
    messages_response = supabase_client.from_("group_messages") \
        .select("id, message, sender_id") \
        .eq("chatroom_id", chatroom_id) \
        .order("id") \
        .execute()

    messages = []
    if messages_response.data:
        for msg in messages_response.data:
            messages.append({
                "message": msg["message"],
                "sender_id": msg["sender_id"],
                "message_id": msg["id"]
            })

    return jsonify({"messages": messages})


# --------------------------------------------------------------------------
#                            SOCKET.IO EVENTS
# --------------------------------------------------------------------------

@socketio.on("join_group_room")
def handle_join_group_room(data):
    """
    Handles a user joining a group chat room (Socket.IO).
    """
    room_key = data.get("room_key")
    join_room(room_key)  # Socket.IO built-in
    print(f"[SocketIO] User joined room: {room_key}")

@socketio.on("send_group_message")
def handle_send_group_message(data):
    """
    Handles sending group messages in a given room,
    and stores them in the `group_messages` table on Supabase.
    """
    room_key   = data.get("room_key")
    message    = data.get("message")
    sender_id  = data.get("sender_id")
    message_id = data.get("message_id")  # optional from client

    # 1. Fetch the chatroom by room_key
    room_response = supabase_client.from_("group_chatrooms") \
        .select("id") \
        .eq("room_key", room_key) \
        .maybe_single() \
        .execute()

    if not room_response.data:
        print("[SocketIO] Invalid group room key:", room_key)
        return  # or handle error

    chatroom_id = room_response.data["id"]

    # 2. Insert the new message into group_messages
    inserted = supabase_client.from_("group_messages").insert({
        "chatroom_id": chatroom_id,
        "sender_id": sender_id,
        "message": message
    }).execute()

    if inserted.data:
        db_message_id = inserted.data[0]["id"]
    else:
        db_message_id = message_id or f"{sender_id}-{int(time.time())}"  # fallback

    # 3. Emit the message event to all users in the room
    #    We can optionally exclude the sender if they've already appended
    emit("receive_group_message", {
        "message": message,
        "sender_id": sender_id,
        "message_id": db_message_id
    }, room=room_key, include_self=False)

    print(f"[SocketIO] Message saved & broadcast in room {room_key}: {message}")

@app.route("/study_groups", methods=["GET"])
@login_required
def study_groups():
    """
    Displays a page where the user can:
      - See the groups they've joined.
      - Search for groups by name.
      - Create a new group (handled by POST /create_group).
      - Join a group from the search results.
    """
    search_query = request.args.get("search", "").strip()

    # 1. Get groups the current user belongs to
    # Example query from group_members -> study_groups
    # You can do a direct join or a select with an embedded join.
    user_groups_response = supabase_client.from_("group_members") \
        .select("study_group_id, study_groups (id, name, description, admin_user_id)") \
        .eq("user_id", current_user.id) \
        .execute()

    user_groups = []
    if user_groups_response.data:
        # Data might look like [{'study_group_id': 1, 'study_groups': {...}}]
        for row in user_groups_response.data:
            group_id = row["study_group_id"]
            group_data = row["study_groups"]
            if group_data:
                # Fetch room_key from group_chatrooms
                chatroom_response = supabase_client.from_("group_chatrooms") \
                    .select("room_key") \
                    .eq("study_group_id", group_id) \
                    .maybe_single() \
                    .execute()

                room_key = chatroom_response.data["room_key"] if chatroom_response.data else None

                user_groups.append({
                    "id": group_data["id"],
                    "name": group_data["name"],
                    "description": group_data["description"],
                    "admin_user_id": group_data["admin_user_id"],
                    "room_key": room_key
                })

    # 2. If user typed a search query, find matching groups
    search_results = []
    if search_query:
        # Searching by name (case-insensitive) using ilike
        search_response = supabase_client.from_("study_groups") \
            .select("id, name, description") \
            .ilike("name", f"%{search_query}%") \
            .execute()

        if search_response.data:
            search_results = search_response.data

    return render_template(
        "study_groups.html",
        user_groups=user_groups, 
        search_results=search_results
    )

@app.route("/create_study_group", methods=["POST"])
@login_required
def create_study_group():
    """
    Creates a new study group and sets the current user as admin.
    Also inserts the user into group_members with role = 'admin'.
    Optionally creates a group_chatroom entry with a unique room_key.
    """
    group_name = request.form.get("group_name", "").strip()
    group_description = request.form.get("group_description", "").strip()

    if not group_name:
        flash("Group name is required.", "error")
        return redirect(url_for("study_groups"))

    # 1. Insert into study_groups
    insert_group = supabase_client.from_("study_groups").insert({
        "name": group_name,
        "description": group_description,
        "admin_user_id": current_user.id
    }).execute()


    new_group_id = insert_group.data[0]["id"]

    # 2. Insert the user into group_members (role = admin)
    insert_member = supabase_client.from_("group_members").insert({
        "study_group_id": new_group_id,
        "user_id": current_user.id,
        "role": "admin"
    }).execute()


    # 3. Optionally create a group_chatroom + unique room_key
    room_key = secrets.token_hex(8)  # e.g., "e3b29f7d9f4f2c21"
    insert_chatroom = supabase_client.from_("group_chatrooms").insert({
        "study_group_id": new_group_id,
        "room_key": room_key
    }).execute()


    return redirect(url_for("study_groups"))

@app.route("/join_study_group", methods=["POST"])
@login_required
def join_study_group():
    """
    Joins an existing study group if the user is not already a member.
    """
    group_id = request.form.get("group_id", type=int)
    if not group_id:
        flash("Invalid group ID.", "error")
        return redirect(url_for("study_groups"))

    # 1. Check if user is already in the group
    membership_check = supabase_client.from_("group_members") \
        .select("id") \
        .eq("study_group_id", group_id) \
        .eq("user_id", current_user.id) \
        .maybe_single() \
        .execute()

    if membership_check:
        flash("You're already a member of this group.", "info")
        return redirect(url_for("study_groups"))

    # 2. Insert user as a member
    insert_member = supabase_client.from_("group_members").insert({
        "study_group_id": group_id,
        "user_id": current_user.id,
        "role": "member"
    }).execute()
    room_key = supabase_client.from_("group_chatrooms").select("room_key").eq("study_group_id", group_id).maybe_single().execute().data["room_key"]
    curr_user = supabase_client.from_("users").select("id, username, profile_picture").eq("id", current_user.id).maybe_single().execute().data
    user_info = {
        "id": curr_user["id"],
        "username": curr_user["username"],
        "profile_picture": curr_user["profile_picture"]
    }
    socketio.emit(
        "group_user_joined",
        user_info,
        to=room_key,
        namespace="/"    # or whatever namespace you're using
    )
    return redirect(url_for("study_groups"))



# --------------------------------------------------------------------
# SOCKET.IO Events (Optional)
# --------------------------------------------------------------------
@socketio.on("join_group_room")
def handle_join_group_room(data):
    """
    A user joins the group chat Socket.IO room by room_key
    """
    room_key = data.get("room_key")
    join_room(room_key)
    print(f"[SocketIO] user joined group room: {room_key}")

@socketio.on("send_group_message")
def handle_send_group_message(data):
    """
    Handles sending messages in a group chat room.
    Inserts the message into group_messages, then emits to the room.
    """
    room_key = data.get("room_key")
    message = data.get("message")
    sender_id = data.get("sender_id")
    client_message_id = data.get("message_id", None)

    # 1. Lookup chatroom by room_key
    chatroom_response = supabase_client.from_("group_chatrooms") \
        .select("id") \
        .eq("room_key", room_key) \
        .maybe_single() \
        .execute()

    if not chatroom_response.data:
        print("[SocketIO] Invalid group room key:", room_key)
        return

    chatroom_id = chatroom_response.data["id"]

    # 2. Insert into group_messages
    message_insert = supabase_client.from_("group_messages").insert({
        "chatroom_id": chatroom_id,
        "sender_id": sender_id,
        "message": message
    }).execute()

    db_message_id = message_insert.data[0]["id"]

    # 3. Emit to all in the room (excluding the sender if you want)
    socketio.emit("receive_group_message", {
        "message": message,
        "sender_id": sender_id,
        "message_id": db_message_id
    }, room=room_key, include_self=False)

@app.route("/create_event", methods=["GET", "POST"])
@login_required
def create_event():
    """
    Allows a user to create a new event with optional filtering
    by majors, ethnicities, countries, academic years.
    """
    if request.method == "POST":
        event_name = request.form.get("event_name", "").strip()
        event_description = request.form.get("event_description", "").strip()
        event_date = request.form.get("event_date")
        event_image = request.files.get("event_image")
        event_link = request.form.get("event_link", "").strip()
        print(event_image)
        if event_image:
            filename = f"{current_user.id}_{secure_filename(event_image.filename)}"
            UPLOAD_FOLDER = "static/event_images"
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            event_image.save(file_path)

            with open(file_path, "rb") as f:
                response = supabase_client.storage.from_("pictures").upload(filename, f)

            res_dict = response.model_dump() if hasattr(response, 'model_dump') else response
            if isinstance(res_dict, dict) and "error" in res_dict and res_dict["error"]:
                return redirect(url_for("create_event"), error="Upload failed")

            event_image_url = f"{SUPABASE_URL}/storage/v1/object/public/pictures/{filename}"
        else:
            event_image_url = None


        # We expect arrays of strings/ints from form checkboxes, multi-select, etc.
        target_majors = request.form.getlist("target_majors")        # e.g. ["Computer Science", "Engineering"]
        target_ethnicities = request.form.getlist("target_ethnicities")
        target_countries = request.form.get("target_countries", "").split(',')
        target_levels = request.form.getlist("target_study_levels")
        target_goals = request.form.getlist("target_goals")
        # For years, parse them as int if needed
        target_years = request.form.getlist("target_years")          # e.g. ["1","2","3"]
        target_years = [int(y) for y in target_years if y.isdigit()]

        if not event_name:
            flash("Event name is required.", "error")
            return redirect(url_for("create_event"))

        # Insert into DB
        response = supabase_client.from_("events").insert({
            "name": event_name,
            "description": event_description,
            "image_url": event_image_url,
            "link": event_link,
            "date": event_date,
            "creator_user_id": current_user.id,
            "target_majors": target_majors,
            "target_ethnicities": target_ethnicities,
            "target_countries": target_countries,
            "target_years": target_years,
            "target_goals": target_goals,
            "target_levels": target_levels
        }).execute()


        return redirect(url_for("event_feed"))
    
    # For GET requests, render form
    # Suppose we have a list of possible majors, countries, etc. in your code
    possible_ethnicities = ["Asian","Black","Hispanic","White","Other"]
    possible_countries = ["USA","Canada","UK","India","China","Other"]
    possible_years = [1,2,3,4,5,6]  # or maybe grad, postdoc, etc.

    return render_template("create_event.html",
                           possible_majors=major_dict,
                           possible_ethnicities=ETHNICITIES,
                           possible_countries=COUNTRIES,
                           possible_years=list(range(1, 6)),
                            possible_goals=GOALS)


@app.route("/event_feed", methods=["GET"])
@login_required
def event_feed():
    # 1. Fetch all events (or consider an 'ORDER BY created_at DESC')
    events_response = supabase_client.from_("events") \
        .select("*") \
        .order("created_at", desc=True) \
        .execute()

    all_events = events_response.data if events_response.data else []

    curr_user = supabase_client.from_("users").select("*").eq("id", current_user.id).execute().data
    curr_user = curr_user[0] if curr_user else None
    # 2. Get current user attributes
    user_major = curr_user["major"]      # e.g. "Computer Science"
    user_ethnicity = curr_user["ethnicity"]
    user_country = curr_user["home_country"]
    user_year = curr_user["study_year"]  # e.g. 2

    # 3. Filter
    filtered_events = []
    for ev in all_events:
        # If target_majors is empty => no major restriction
        event_majors = ev["target_majors"]  # array from DB
        if event_majors and user_major not in event_majors:
            continue

        event_ethnicities = ev["target_ethnicities"]
        if event_ethnicities and user_ethnicity not in event_ethnicities:
            continue

        event_countries = ev["target_countries"]
        if event_countries and user_country not in event_countries:
            continue

        event_years = ev["target_years"]  # array of INT
        if event_years and user_year not in event_years:
            continue

        # If we pass all checks, include the event
        filtered_events.append(ev)

    return render_template("event_feed.html", events=filtered_events)

@app.route("/course/<subject_id>-<int:course_code>", methods=["GET", "POST"])
@login_required
def course_page(subject_id, course_code):
    if request.method == "POST":
        # Collect data from the submitted form
        section = request.form.get("section")
        professor_name = request.form.get("professor_name")
        professor_email = request.form.get("professor_email")
        class_schedule = request.form.getlist("class_schedule")

        # Collect assignment data (iterate over submitted work_* fields)
        work_data = {}
        for field_name, value in request.form.items():
            if field_name.startswith("work_") and "_" in field_name:
                work_id = field_name.split("_")[1]
                if work_id not in work_data:
                    work_data[work_id] = {"work_id": work_id}

                # Determine which field we're processing
                if field_name.endswith("_name"):
                    if value in ["TBD", "",None]:
                            work_data[work_id]["name"] = None
                    else:work_data[work_id]["name"] = value
                elif field_name.endswith("_weightage"):
                    if value in ["TBD", "",None]:
                        work_data[work_id]["weightage"] = None
                    else:
                        work_data[work_id]["weightage"] = float(value)

                elif field_name.endswith("_marks_obtained"):
                    if value in ["TBD", "",None]:
                        work_data[work_id]["marks_obtained"] = None
                    else:
                        work_data[work_id]["marks_obtained"] = float(value)
                elif field_name.endswith("_due_date"):
                    if value in ["TBD", "",None]:
                        work_data[work_id]["due_date"] = None
                    else:
                        work_data[work_id]["due_date"] = value
                   
                elif field_name.endswith("_due_time"):
                    if value in ["TBD", "",None]:
                        work_data[work_id]["due_time"] = None
                    else:
                        work_data[work_id]["due_time"] = value

        print("work_data:", work_data)

        # Update the course info in the database
        course_update = {
            "section": section,
            "professor": professor_name,
            "professor_email": professor_email,
            "class_schedule": ",".join(class_schedule),
        }
        supabase_client.from_("course").update(course_update).eq("course_code", course_code).eq("subject_id", subject_id).execute()
        
        user_id = current_user.id

        # Update each assignment in the database
        for work_id, work_fields in work_data.items():
            supabase_client.from_("work_template").update({
                "name": work_fields.get("name"),
                "weightage": work_fields.get("weightage"),
                "due_date": work_fields.get("due_date"),
                "due_time": work_fields.get("due_time"),
            }).eq("work_id", work_id).execute()

            supabase_client.from_("assigned_work").update({
                "weightage": work_fields.get("weightage"),
                "marks_obtained": work_fields.get("marks_obtained"),
                "due_date": work_fields.get("due_date"),
                "due_time": work_fields.get("due_time"),
            }).eq("user_id", user_id).eq("work_id", work_id).execute()

        return redirect(url_for("course_page", subject_id=subject_id, course_code=course_code))

    else:

        print(f"Received course_code: {course_code}, subject_id: {subject_id}")  # Debugging output
        # Retrieve course and assignment data to prefill the form
        course_data_response = supabase_client.from_("course").select("*").eq("course_code", course_code).eq("subject_id", subject_id).execute()
        course_data = course_data_response.data if course_data_response.data else {}
        # Fetch the course_id from user_courses if multiple rows are returned
        if isinstance(course_data_response.data, list) and len(course_data_response.data) > 1:
            user_courses_response = supabase_client.from_("user_courses").select("course_id").eq("user_id", current_user.id).execute()
            user_course_ids = {uc["course_id"] for uc in user_courses_response.data} if user_courses_response.data else set()
            course_data = next((cd for cd in course_data_response.data if cd["course_id"] in user_course_ids), {})
        else:
            course_data = course_data_response.data if course_data_response.data else {}

        course_id = course_data[0].get("course_id") if course_data else None
        if not course_id:
            return redirect(url_for("dashboard"))
        print("course_id", course_id)
        print("course_data:", course_data)
        # Fetch assignments related to this course
        assigned_work_response = supabase_client.from_("assigned_work").select("work_id, due_date, due_time, weightage, marks_obtained").eq("course_id", course_id).eq("user_id", current_user.id).execute()
        assigned_work_data = assigned_work_response.data if assigned_work_response.data else []

        work_template_response = supabase_client.from_("work_template").select("work_id, name").eq("course_id", course_id).execute()
        work_template_data = work_template_response.data if work_template_response.data else []

        # Combine data from assigned_work and work_template into a uniform format
        print("assigned_work_data:", assigned_work_data)  # Debugging print statement
        print("work_template_data:", work_template_data)  # Debugging print statement
        combined_work_data = []
        for assigned_work in assigned_work_data:
            work_template = next((wt for wt in work_template_data if wt["work_id"] == assigned_work["work_id"]), {})
            combined_work_data.append({
                "work_id": assigned_work["work_id"],
                "name": work_template.get("name", "Untitled"),
                "weightage": assigned_work.get("weightage", 0),
                "marks_obtained": assigned_work.get("marks_obtained"),
                "due_date": assigned_work.get("due_date", "TBD"),
                "due_time": assigned_work.get("due_time", "TBD"),
            })
        print("combined_work_data:", combined_work_data)

        # Create a structured dictionary for the template
        course_info = {
            "subject_id": course_data[0].get("subject_id", "N/A"),
            "course_code": course_data[0].get("course_code", "N/A"),
            "section": course_data[0].get("section", "N/A"),
            "professor": {
                "name": course_data[0].get("professor", "Unknown"),
                "email": course_data[0].get("professor_email", "N/A"),
            },
            "class_schedule": (course_data[0].get("class_schedule") or "").split(","),
            "assigned_work": combined_work_data,
        }

        # Render the course.html template
        return render_template("course.html", course=course_info)

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)