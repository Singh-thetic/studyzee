"""
Social features - friends, events, profile management.
"""

import logging
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from utils.constants import ETHNICITIES, COUNTRIES, GOALS, MAJORS

logger = logging.getLogger(__name__)
social_bp = Blueprint("social", __name__)


# ============================================================================
# PROFILE ROUTES
# ============================================================================

@social_bp.route("/profile")
@login_required
def profile():
    """View current user's profile."""
    return render_template("profile.html", user=current_user)


@social_bp.route("/user/<user_id>")
@login_required
def user_profile(user_id):
    """View another user's profile."""
    db = current_app.db
    
    user_data = db.select_one("users", "id", user_id)
    if not user_data:
        flash("User not found", "error")
        return redirect(url_for("dashboard.dashboard"))
    
    return render_template("user_profile.html", profile_user=user_data)


@social_bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    """Edit user profile."""
    db = current_app.db
    
    if request.method == "POST":
        # Update profile fields - match template field names
        major = request.form.get("major", "").strip()
        ethnicity = request.form.get("ethnicity", "").strip()
        home_country = request.form.get("home_country", "").strip()
        study_year = request.form.get("year_of_study", type=int)  # Note: form uses 'year_of_study'
        study_level = request.form.get("study_level", "").strip()
        academic_goal = request.form.get("academic_goal", "").strip()
        gender = request.form.get("gender", "").strip()
        
        # Debug: Log what we received
        logger.info(f"Form data received - gender: '{gender}', academic_goal: '{academic_goal}'")
        logger.info(f"All form data: {dict(request.form)}")
        
        update_data = {
            "major": major if major else None,
            "ethnicity": ethnicity if ethnicity else None,
            "home_country": home_country if home_country else None,
            "study_year": study_year,
            "study_level": study_level if study_level else None,
            "gender": gender if gender else None,
            "academic_goal": academic_goal if academic_goal else None,
        }
        
        # Debug: Log what we're about to save
        logger.info(f"Update data before filtering: {update_data}")
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        # Debug: Log what we're saving
        logger.info(f"Update data after filtering: {update_data}")
        
        # Update database
        if update_data:
            result = db.update("users", "id", current_user.id, update_data)
            logger.info(f"Database update result: {result}")
            if result:
                # Reload user from database to get all updated fields
                current_user.reload_from_db(db)
                logger.info(f"After reload - gender: {getattr(current_user, 'gender', 'NOT SET')}, academic_goal: {getattr(current_user, 'academic_goal', 'NOT SET')}")
                flash("Profile updated successfully!", "success")
            else:
                flash("Failed to update profile", "error")
        else:
            flash("No changes to save", "info")
        
        return redirect(url_for("social.profile"))
    
    return render_template("profile.html", user=current_user, editing=True)


@social_bp.route("/change_name", methods=["POST"])
@login_required
def change_name():
    """Change user's full name."""
    db = current_app.db
    
    new_name = request.form.get("new_name", "").strip()
    
    if new_name:
        if db.update("users", "id", current_user.id, {"full_name": new_name}):
            current_user.reload_from_db(db)
            flash("Name updated successfully!", "success")
        else:
            flash("Failed to update name", "error")
    else:
        flash("Name cannot be empty", "error")
    
    return redirect(url_for("social.profile"))


@social_bp.route("/update_pic", methods=["POST"])
@login_required
def update_pic():
    """Update profile picture."""
    db = current_app.db
    
    if "profile_pic" in request.files:
        file = request.files["profile_pic"]
        if file and file.filename:
            # Create directory if doesn't exist
            os.makedirs("static/profile_pics", exist_ok=True)
            
            filename = f"{current_user.id}_{secure_filename(file.filename)}"
            filepath = os.path.join("static/profile_pics", filename)
            file.save(filepath)
            
            # Use local path for now (could upload to Supabase later)
            profile_pic_url = f"/static/profile_pics/{filename}"
            
            if db.update("users", "id", current_user.id, {"profile_picture": profile_pic_url}):
                current_user.reload_from_db(db)
                flash("Profile picture updated successfully!", "success")
            else:
                flash("Failed to update profile picture", "error")
        else:
            flash("No file selected", "error")
    else:
        flash("No file uploaded", "error")
    
    return redirect(url_for("social.profile"))


# ============================================================================
# FRIENDS ROUTES
# ============================================================================

@social_bp.route("/friends")
@login_required
def friends():
    """View friends list."""
    db = current_app.db
    
    # Note: This assumes a friends table exists or we're using a different approach
    # For now, we'll just show all users as potential friends
    all_users = db.select("users")
    
    friends_list = [u for u in (all_users or []) if u["id"] != current_user.id]
    
    return render_template("friends.html", friends=friends_list)


@social_bp.route("/meet_new_friends")
@login_required
def meet_new_friends():
    """Find new friends based on interests."""
    return render_template("meet_new_friends.html")


@social_bp.route("/suggested_friends")
@login_required
def suggested_friends():
    """API endpoint to get friend suggestions."""
    from flask import jsonify
    db = current_app.db
    
    # Get all users
    all_users = db.select("users")
    
    # Filter out current user
    suggestions = []
    for user in (all_users or []):
        if user["id"] != current_user.id:
            # Calculate match reason
            reasons = []
            if user.get("major") == current_user.major:
                reasons.append("Same major")
            if user.get("home_country") == current_user.home_country:
                reasons.append("Same country")
            if user.get("study_level") == current_user.study_level:
                reasons.append("Same study level")
            if user.get("academic_goal") == current_user.academic_goal:
                reasons.append("Same academic goal")
            
            match_reason = ", ".join(reasons) if reasons else "New user in your area"
            
            suggestions.append({
                "id": user["id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "match_reason": match_reason
            })
    
    return jsonify({"suggestions": suggestions[:10]})  # Limit to 10


@social_bp.route("/send_friend_request", methods=["POST"])
@login_required
def send_friend_request():
    """Send a friend request."""
    from flask import jsonify
    db = current_app.db
    
    data = request.get_json()
    receiver_id = data.get("receiver_id")
    message = data.get("message", "")
    
    if not receiver_id:
        return jsonify({"error": "Receiver ID required"}), 400
    
    # Check if already friends
    user_ids = sorted([current_user.id, receiver_id])
    existing_friendship = db.client.table("friendships").select("id").eq("user_id_1", user_ids[0]).eq("user_id_2", user_ids[1]).maybe_single().execute()
    
    if existing_friendship and existing_friendship.data:
        return jsonify({"error": "Already friends"}), 400
    
    # Check if request already exists
    existing_request = db.client.table("friend_requests").select("id").eq("sender_id", current_user.id).eq("receiver_id", receiver_id).eq("status", "pending").maybe_single().execute()
    
    if existing_request and existing_request.data:
        return jsonify({"error": "Friend request already sent"}), 400
    
    # Create friend request
    result = db.insert("friend_requests", {
        "sender_id": current_user.id,
        "receiver_id": receiver_id,
        "message": message,
        "status": "pending"
    })
    
    if result:
        return jsonify({"message": "Friend request sent successfully!"})
    else:
        return jsonify({"error": "Failed to send friend request"}), 500


@social_bp.route("/friends_list")
@login_required
def friends_list():
    """Get list of actual friends for the current user."""
    from flask import jsonify
    db = current_app.db
    
    # Get friendships where current user is involved
    friendships_response = db.client.table("friendships").select("*").or_(
        f"user_id_1.eq.{current_user.id},user_id_2.eq.{current_user.id}"
    ).execute()
    
    friends = []
    if friendships_response.data:
        for friendship in friendships_response.data:
            # Get the friend's ID (the one that's not current user)
            friend_id = friendship["user_id_2"] if friendship["user_id_1"] == current_user.id else friendship["user_id_1"]
            
            # Get friend's info
            friend_data = db.select_one("users", "id", friend_id)
            if friend_data:
                # Create room code for direct messaging
                user_ids = sorted([current_user.id, friend_id])
                room_code = f"dm_{user_ids[0]}_{user_ids[1]}"
                
                friends.append({
                    "id": friend_data["id"],
                    "username": friend_data["username"],
                    "full_name": friend_data["full_name"],
                    "room_code": room_code
                })
    
    return jsonify({"friends": friends})


@social_bp.route("/friend_requests")
@login_required
def friend_requests():
    """Get pending friend requests for current user."""
    from flask import jsonify
    db = current_app.db
    
    # Get pending requests where current user is the receiver
    requests_response = db.client.table("friend_requests").select("*").eq("receiver_id", current_user.id).eq("status", "pending").execute()
    
    logger.info(f"Friend requests for user {current_user.id}: {requests_response.data}")
    
    requests = []
    if requests_response.data:
        for req in requests_response.data:
            # Get sender's info
            sender = db.select_one("users", "id", req["sender_id"])
            if sender:
                requests.append({
                    "id": req["id"],
                    "sender_id": sender["id"],
                    "sender_email": sender["email"],
                    "sender_name": sender["full_name"],
                    "message": req.get("message", "")
                })
    
    logger.info(f"Formatted requests: {requests}")
    return jsonify({"requests": requests})


@social_bp.route("/respond_friend_request", methods=["POST"])
@login_required
def respond_friend_request():
    """Accept or reject a friend request."""
    from flask import jsonify
    db = current_app.db
    
    data = request.get_json()
    request_id = data.get("request_id")
    response = data.get("response")  # "accepted" or "rejected"
    
    logger.info(f"Responding to friend request: {request_id} with {response}")
    
    if not request_id or response not in ["accepted", "rejected"]:
        return jsonify({"error": "Invalid request"}), 400
    
    # Get the friend request using direct query
    try:
        friend_request_response = db.client.table("friend_requests").select("*").eq("id", request_id).execute()
        logger.info(f"Friend request response: {friend_request_response.data}")
        
        if not friend_request_response.data or len(friend_request_response.data) == 0:
            logger.error(f"Friend request not found in database")
            return jsonify({"error": "Friend request not found"}), 404
        
        friend_request = friend_request_response.data[0]
        logger.info(f"Friend request data: {friend_request}")
        
        if friend_request["receiver_id"] != current_user.id:
            logger.error(f"User not authorized to respond to this request")
            return jsonify({"error": "Not authorized"}), 403
    except Exception as e:
        logger.error(f"Error fetching friend request: {str(e)}")
        return jsonify({"error": "Failed to fetch friend request"}), 500
    
    # Update request status
    update_result = db.update("friend_requests", "id", request_id, {"status": response})
    logger.info(f"Update request status result: {update_result}")
    
    # If accepted, create friendship
    if response == "accepted":
        sender_id = friend_request["sender_id"]
        user_ids = sorted([current_user.id, sender_id])
        
        logger.info(f"Creating friendship between {user_ids[0]} and {user_ids[1]}")
        
        friendship_result = db.insert("friendships", {
            "user_id_1": user_ids[0],
            "user_id_2": user_ids[1]
        })
        
        logger.info(f"Friendship creation result: {friendship_result}")
        
        if not friendship_result:
            logger.error("Failed to create friendship")
            return jsonify({"error": "Failed to create friendship"}), 500
    
    return jsonify({"message": f"Friend request {response}!", "success": True})


# ============================================================================
# EVENTS ROUTES
# ============================================================================

@social_bp.route("/create_event", methods=["GET", "POST"])
@login_required
def create_event():
    """Create a new campus event."""
    db = current_app.db
    
    if request.method == "POST":
        event_name = request.form.get("event_name", "").strip()
        event_description = request.form.get("event_description", "").strip()
        event_date = request.form.get("event_date")
        event_link = request.form.get("event_link", "").strip()
        
        # Get targeting filters
        target_majors = request.form.getlist("target_majors")
        target_ethnicities = request.form.getlist("target_ethnicities")
        target_countries = request.form.get("target_countries", "").split(",")
        target_levels = request.form.getlist("target_study_levels")
        target_goals = request.form.getlist("target_goals")
        target_years = request.form.getlist("target_years")
        target_years = [int(y) for y in target_years if y.isdigit()]
        
        # Handle event image
        event_image_url = None
        if "event_image" in request.files:
            file = request.files["event_image"]
            if file and file.filename:
                filename = f"{current_user.id}_{secure_filename(file.filename)}"
                filepath = os.path.join("static/event_images", filename)
                file.save(filepath)
                
                # Upload to Supabase
                try:
                    with open(filepath, "rb") as f:
                        event_image_url = db.storage_upload("pictures", filename, f.read())
                except Exception as e:
                    logger.error(f"Failed to upload event image: {str(e)}")
        
        if not event_name:
            flash("Event name is required.", "error")
            return redirect(url_for("social.create_event"))
        
        # Insert into database
        db.insert("events", {
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
        })
        
        flash("Event created successfully!", "success")
        return redirect(url_for("social.event_feed"))
    
    # GET request
    return render_template(
        "create_event.html",
        possible_majors=MAJORS,
        possible_ethnicities=ETHNICITIES,
        possible_countries=COUNTRIES,
        possible_years=list(range(1, 6)),
        possible_goals=GOALS
    )


@social_bp.route("/event_feed", methods=["GET"])
@login_required
def event_feed():
    """Display filtered event feed based on user attributes."""
    db = current_app.db
    
    # Fetch all events
    events_response = db.client.table("events").select("*").order("created_at", desc=True).execute()
    
    all_events = events_response.data if events_response.data else []
    
    # Get current user attributes
    curr_user = db.select_one("users", "id", current_user.id)
    if not curr_user:
        return render_template("event_feed.html", events=[])
    
    user_major = curr_user.get("major")
    user_ethnicity = curr_user.get("ethnicity")
    user_country = curr_user.get("home_country")
    user_year = curr_user.get("study_year")
    
    # Filter events
    filtered_events = []
    for ev in all_events:
        # Check major filter
        event_majors = ev.get("target_majors")
        if event_majors and user_major and user_major not in event_majors:
            continue
        
        # Check ethnicity filter
        event_ethnicities = ev.get("target_ethnicities")
        if event_ethnicities and user_ethnicity and user_ethnicity not in event_ethnicities:
            continue
        
        # Check country filter
        event_countries = ev.get("target_countries")
        if event_countries and user_country and user_country not in event_countries:
            continue
        
        # Check year filter
        event_years = ev.get("target_years")
        if event_years and user_year and user_year not in event_years:
            continue
        
        # Event passes all filters
        filtered_events.append(ev)
    
    return render_template("event_feed.html", events=filtered_events)
