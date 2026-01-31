"""
Study groups routes - create, join, manage groups.
"""

import logging
import secrets
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

logger = logging.getLogger(__name__)
study_groups_bp = Blueprint("study_groups", __name__)


@study_groups_bp.route("/study_groups", methods=["GET"])
@login_required
def study_groups():
    """
    Display study groups page with user's groups and search functionality.
    """
    db = current_app.db
    search_query = request.args.get("search", "").strip()
    
    # Get groups the user belongs to
    user_groups_response = db.client.table("group_members").select("study_group_id, study_groups (*)").eq("user_id", current_user.id).execute()
    
    user_groups = []
    if user_groups_response.data:
        for row in user_groups_response.data:
            group_data = row.get("study_groups")
            if group_data:
                group_id = row["study_group_id"]
                
                # Fetch room_key from group_chatrooms
                chatroom = db.select_one("group_chatrooms", "study_group_id", group_id)
                room_key = chatroom["room_key"] if chatroom else None
                
                user_groups.append({
                    "id": group_data["id"],
                    "name": group_data["name"],
                    "description": group_data.get("description", ""),
                    "admin_user_id": group_data.get("admin_user_id"),
                    "room_key": room_key
                })
    
    # Search for groups
    search_results = []
    if search_query:
        search_response = db.client.table("study_groups").select("id, name, description").ilike("name", f"%{search_query}%").execute()
        
        if search_response.data:
            search_results = search_response.data
    
    return render_template(
        "study_groups.html",
        user_groups=user_groups,
        search_results=search_results
    )


@study_groups_bp.route("/create_study_group", methods=["POST"])
@login_required
def create_study_group():
    """Create a new study group."""
    db = current_app.db
    
    group_name = request.form.get("group_name", "").strip()
    group_description = request.form.get("group_description", "").strip()
    
    if not group_name:
        flash("Group name is required.", "error")
        return redirect(url_for("study_groups.study_groups"))
    
    # Insert into study_groups
    insert_group = db.insert("study_groups", {
        "name": group_name,
        "description": group_description,
        "admin_user_id": current_user.id
    })
    
    if not insert_group:
        flash("Failed to create group", "error")
        return redirect(url_for("study_groups.study_groups"))
    
    new_group_id = insert_group["id"]
    
    # Insert the user into group_members (role = admin)
    db.insert("group_members", {
        "study_group_id": new_group_id,
        "user_id": current_user.id,
        "role": "admin"
    })
    
    # Create a group_chatroom with unique room_key
    room_key = secrets.token_hex(8)
    db.insert("group_chatrooms", {
        "study_group_id": new_group_id,
        "room_key": room_key
    })
    
    flash(f"Study group '{group_name}' created successfully!", "success")
    return redirect(url_for("study_groups.study_groups"))


@study_groups_bp.route("/join_study_group", methods=["POST"])
@login_required
def join_study_group():
    """Join an existing study group."""
    db = current_app.db
    
    group_id = request.form.get("group_id", type=str)
    if not group_id:
        flash("Invalid group ID.", "error")
        return redirect(url_for("study_groups.study_groups"))
    
    # Check if user is already in the group
    try:
        membership_check = db.client.table("group_members").select("id").eq("study_group_id", group_id).eq("user_id", current_user.id).maybe_single().execute()
        if membership_check and membership_check.data:
            flash("You're already a member of this group.", "info")
            return redirect(url_for("study_groups.study_groups"))
    except Exception as e:
        logger.error(f"Error checking membership: {str(e)}")
        # Continue to join if check fails
    
    # Insert user as a member
    db.insert("group_members", {
        "study_group_id": group_id,
        "user_id": current_user.id,
        "role": "member"
    })
    
    flash("Successfully joined the study group!", "success")
    return redirect(url_for("study_groups.study_groups"))


@study_groups_bp.route("/leave_study_group/<group_id>", methods=["POST"])
@login_required
def leave_study_group(group_id):
    """Leave a study group."""
    db = current_app.db
    
    # Check if user is the admin
    group = db.select_one("study_groups", "id", group_id)
    if group and group.get("admin_user_id") == current_user.id:
        flash("Admins cannot leave their own group. Transfer ownership or delete the group.", "error")
        return redirect(url_for("study_groups.study_groups"))
    
    # Delete membership
    memberships = db.client.table("group_members").select("id").eq("study_group_id", group_id).eq("user_id", current_user.id).execute()
    
    if memberships.data:
        membership_id = memberships.data[0]["id"]
        db.delete("group_members", "id", membership_id)
        flash("Left the study group successfully.", "success")
    else:
        flash("You are not a member of this group.", "error")
    
    return redirect(url_for("study_groups.study_groups"))


@study_groups_bp.route("/delete_study_group/<group_id>", methods=["POST"])
@login_required
def delete_study_group(group_id):
    """Delete a study group (admin only)."""
    db = current_app.db
    
    # Check if user is the admin
    group = db.select_one("study_groups", "id", group_id)
    if not group or group.get("admin_user_id") != current_user.id:
        flash("Only the group admin can delete the group.", "error")
        return redirect(url_for("study_groups.study_groups"))
    
    # Delete group (cascades will handle members, chatroom, messages)
    db.delete("study_groups", "id", group_id)
    flash("Study group deleted successfully.", "success")
    
    return redirect(url_for("study_groups.study_groups"))
