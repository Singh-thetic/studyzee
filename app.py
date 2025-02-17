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
from flask_socketio import SocketIO, send, emit, join_room, leave_room

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

@app.route("/edit_course", methods=["GET", "POST"])
@login_required
def edit_course():
    
    course_data = request.args.get("course_data")
    uploaded_files = request.args.getlist("uploaded_files")
    print(uploaded_files)
    course_data = course_info(uploaded_files)
    
    return jsonify(course_data)


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
    
    courses = [f"{d.get("subject_id")} {d.get("course_code")}" for d in course_d]
    
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
    emit("receive_message", {"message": f"User joined room {room}"}, room=room)

@socketio.on('send_message')
def handle_send_message(data):
    """Handles sending messages in a room and storing them in Supabase."""
    room = data["room"]
    message = data["message"]
    user_id = data["user_id"]

    # Store message in Supabase
    supabase_client.from_("chat_messages").insert({
        "room": room,
        "message": message,
        "sender_id": user_id
    }).execute()

    emit("receive_message", {"message": message}, room=room)


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

    return render_template("chat.html", room_code=room_code, user_id=current_user.id)



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
@app.route("/chat_history/<room_code>")
@login_required
def chat_history(room_code):
    """Fetch all previous messages from the database for a given chat room."""
    messages_response = supabase_client.from_("chat_messages").select("message") \
        .eq("room", room_code).execute()

    messages = [msg["message"] for msg in messages_response.data] if messages_response.data else []
    
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

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)