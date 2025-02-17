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
        flash("Invalid email or password", "error")
        return redirect(url_for("home"))


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
    existing_user = response.data[0] if response else None
    
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
        response = supabase_client.from_("users").select("*").eq("id", current_user.id).maybe_single().execute()
        user = response.data
        return render_template("profile.html", user=user)
    
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
    return redirect(url_for("edit_course", course_data=course_data, uploaded_files=uploaded_files))

@app.route("/confirm_course", methods=["GET", "POST"])
@login_required
def edit_course():
    global course_data
    if request.method == "POST":
        section = request.form.get("section")
        if section:
            course_data = {section: course_data[section]}
        else:
            # Create a dictionary to store the incoming data
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
            
            # Insert course data dynamically with validation
            for course_code, details in course_data.items():
                # Check if the course already exists
                existing_course = supabase_client.table("course").select("course_id") \
                    .eq("course_code", details.get("course_code", "")) \
                    .eq("section", details.get("section", "")) \
                    .eq("professor", details.get("professor", "")) \
                    .maybe_single().execute()

                # Ensure `execute()` properly returns a result
                if existing_course and existing_course.data:
                    course_id = existing_course.data["course_id"]  # Fetch existing course_id
                else:
                    # Insert new course if it doesn't exist
                    course_insert = {
                        "subject_id": details.get("subject_id", "Unknown")[:10],  # Truncate if needed
                        "course_code": details.get("course_code", "Unknown")[:10],  # Truncate to 10 chars
                        "term": details.get("term", "Unknown Term")[:10],  # If term has a length limit
                        "year": details.get("year", 2025),
                        "section": details.get("section", "A")[:10],  # Truncate section if needed
                        "course_name": details.get("course_name", "Unknown Course"),  # No need to truncate unless known limit
                        "professor": details.get("professor", "Unknown"),  
                        "class_schedule": ",".join(details.get("class_schedule", []))[:100],  # Truncate long schedules
                        "professor_email": details.get("professor_email", "Unknown")[:100],  # Avoid long emails
                    }
                    response = supabase_client.table("course").insert(course_insert).execute()
                    
                    if response.data:
                        course_id = response.data[0]["course_id"]  # Get the generated `course_id`

                    # Ensure the user is linked to the course in `user_courses`
                    supabase_client.table("user_courses").insert({"user_id": current_user.id, "course_id": course_id}).execute()

                    # Insert assignments into `work_template` and `assigned_work`
                    for work_name, work_data in details["WeightageTable"].items():
                        # Check if work already exists
                        existing_work = supabase_client.table("work_template").select("work_id").eq("course_id", course_id).eq("name", work_name).execute()
                        
                        if existing_work.data:
                            work_id = existing_work.data[0]["work_id"]
                        else:
                            # Insert new work into `work_template`

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

                        # Insert assignment into `assigned_work`
                        
                        
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
            course_data = eval(course_data)  # Convert string representation of dict back to dict
        else:
            flash("Course data is missing", "error")
            return redirect(url_for("add_course"))

        uploaded_files = request.args.getlist("uploaded_files")
        # Process the uploaded files to extract course information
        course_information = course_info(uploaded_files)
        for course in course_information:
            course_information[course] = {
                'course_code': course_data.get('course_code', 'Unknown'),
                'subject': course_data.get('subject', 'Unknown'),
                **course_information[course]
            }
        course_data = course_information
        print(course_data)
    
    # Render the template with the extracted course data
    return render_template("add_course.html", course_data=course_data, stage=3)



@app.route("/dashboard")
@login_required
def dashboard():
    user_data = supabase_client.from_("users").select("*").eq("id", current_user.id).maybe_single().execute().data
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
    return render_template("login.html")

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

    if not chat_room.data:
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

    if existing_request.data:
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

        # Check if a room already exists to avoid duplicates
        existing_room = supabase_client.from_("private_chat_rooms").select("room_code") \
        .or_(f"user1_id.eq.{current_user.id},user2_id.eq.{sender_id},user1_id.eq.{sender_id},user2_id.eq.{current_user.id}") \
        .maybe_single().execute()

        if not existing_room:
            print("DEBUG: Creating new chat room in private_chat_rooms")
            supabase_client.from_("private_chat_rooms").insert({
                "user1_id": current_user.id,
                "user2_id": sender_id,
                "room_code": room_code
            }).execute()
        else:
            print(f"DEBUG: Chat room already exists for {room_code}")

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
        friend_data = supabase_client.from_("users").select("id, email").eq("id", friend_id).maybe_single().execute()
        friends.append({"id": friend_data.data["id"], "email": friend_data.data["email"], "room_code": f["chat_room_code"]})

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

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)