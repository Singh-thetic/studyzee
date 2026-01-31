"""
Chat routes with WebSocket support for direct messaging and group chats.
"""

import logging
import json
import time
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)


# ============================================================================
# DIRECT MESSAGING ROUTES
# ============================================================================

@chat_bp.route("/chat/<friend_id>")
@login_required
def direct_chat(friend_id):
    """Direct chat with a friend."""
    db = current_app.db
    
    # Get friend info
    friend_data = db.select_one("users", "id", friend_id)
    if not friend_data:
        flash("User not found", "error")
        return redirect(url_for("dashboard.dashboard"))
    
    # Create unique room key for this chat (sorted IDs for consistency)
    user_ids = sorted([current_user.id, friend_id])
    room_key = f"dm_{user_ids[0]}_{user_ids[1]}"
    
    return render_template(
        "chat.html",
        friend={
            "id": friend_data["id"],
            "username": friend_data["username"],
            "full_name": friend_data["full_name"],
            "profile_picture": friend_data.get("profile_picture")
        },
        room_key=room_key,
        user_id=current_user.id
    )


@chat_bp.route("/chat_history/<friend_id>")
@login_required
def chat_history(friend_id):
    """Get chat history with a friend."""
    db = current_app.db
    
    # Fetch messages between current_user and friend
    messages_response = db.client.table("direct_messages").select("*").or_(
        f"and(sender_id.eq.{current_user.id},recipient_id.eq.{friend_id}),"
        f"and(sender_id.eq.{friend_id},recipient_id.eq.{current_user.id})"
    ).order("created_at").execute()
    
    messages = []
    if messages_response.data:
        for msg in messages_response.data:
            messages.append({
                "message": msg["message"],
                "sender_id": msg["sender_id"],
                "message_id": msg["id"],
                "created_at": msg.get("created_at", "")
            })
    
    return jsonify({"messages": messages})


# ============================================================================
# GROUP CHAT ROUTES
# ============================================================================

@chat_bp.route("/groupchat")
@login_required
def group_chat():
    """Group chat page."""
    db = current_app.db
    room_key = request.args.get("room_key")
    
    if not room_key:
        flash("Missing room key for group chat!", "error")
        return redirect(url_for("dashboard.dashboard"))
    
    # Check if this room_key exists in group_chatrooms
    room_response = db.client.table("group_chatrooms").select("*").eq("room_key", room_key).maybe_single().execute()
    
    if not room_response.data:
        flash("This group chat room does not exist!", "error")
        return redirect(url_for("dashboard.dashboard"))
    
    chatroom_data = room_response.data
    study_group_id = chatroom_data["study_group_id"]
    
    # Check if current_user is part of this group
    membership_response = db.client.table("group_members").select("id").eq("study_group_id", study_group_id).eq("user_id", current_user.id).maybe_single().execute()
    
    if not membership_response.data:
        flash("You are not a member of this study group!", "error")
        return redirect(url_for("dashboard.dashboard"))
    
    # Get group info
    group_response = db.select_one("study_groups", "id", study_group_id)
    group_name = group_response["name"] if group_response else "Study Group"
    
    # Get all members
    members_response = db.select_where("group_members", "study_group_id", study_group_id)
    user_ids = [m["user_id"] for m in (members_response or [])]
    
    users = {}
    for user_id in user_ids:
        user_data = db.select_one("users", "id", user_id)
        if user_data:
            users[user_id] = {
                "id": user_id,
                "username": user_data["username"],
                "profile_picture": user_data.get("profile_picture")
            }
    
    return render_template(
        "groupchat.html",
        room_key=room_key,
        user_id=current_user.id,
        group_name=group_name,
        group_icon=None,
        users_json=json.dumps(users)
    )


@chat_bp.route("/group_chat_history/<room_key>")
@login_required
def group_chat_history(room_key):
    """Get group chat message history."""
    db = current_app.db
    
    # Validate the group chat exists
    room_response = db.client.table("group_chatrooms").select("id, study_group_id").eq("room_key", room_key).maybe_single().execute()
    
    if not room_response.data:
        return jsonify({"messages": []})
    
    chatroom_id = room_response.data["id"]
    study_group_id = room_response.data["study_group_id"]
    
    # Ensure user is a member
    membership_response = db.client.table("group_members").select("id").eq("study_group_id", study_group_id).eq("user_id", current_user.id).maybe_single().execute()
    
    if not membership_response.data:
        return jsonify({"messages": []})
    
    # Fetch messages
    messages_response = db.client.table("group_messages").select("*").eq("chatroom_id", chatroom_id).order("created_at").execute()
    
    messages = []
    if messages_response.data:
        for msg in messages_response.data:
            messages.append({
                "message": msg["message"],
                "sender_id": msg["sender_id"],
                "message_id": msg["id"],
                "created_at": msg.get("created_at", "")
            })
    
    return jsonify({"messages": messages})


# ============================================================================
# WEBSOCKET EVENT HANDLERS
# ============================================================================

def register_socket_events(socketio):
    """Register WebSocket event handlers."""
    
    @socketio.on("join_room")
    def handle_join_room(data):
        """Handle user joining a chat room (direct or group)."""
        room_key = data.get("room_key")
        if room_key:
            join_room(room_key)
            logger.info(f"User {current_user.id} joined room: {room_key}")
    
    @socketio.on("leave_room")
    def handle_leave_room(data):
        """Handle user leaving a chat room."""
        room_key = data.get("room_key")
        if room_key:
            leave_room(room_key)
            logger.info(f"User {current_user.id} left room: {room_key}")
    
    @socketio.on("send_message")
    def handle_send_message(data):
        """Handle sending direct messages."""
        room_key = data.get("room_key")
        message = data.get("message")
        recipient_id = data.get("recipient_id")
        sender_id = current_user.id
        
        if not all([room_key, message, recipient_id]):
            return
        
        db = current_app.db
        
        # Insert message into direct_messages
        message_insert = db.insert("direct_messages", {
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "message": message
        })
        
        if message_insert:
            db_message_id = message_insert["id"]
            
            # Emit to room
            emit("receive_message", {
                "message": message,
                "sender_id": sender_id,
                "message_id": db_message_id,
                "created_at": message_insert.get("created_at", "")
            }, room=room_key, include_self=False)
            
            logger.info(f"Direct message sent in room {room_key}")
    
    @socketio.on("send_group_message")
    def handle_send_group_message(data):
        """Handle sending group messages."""
        room_key = data.get("room_key")
        message = data.get("message")
        sender_id = current_user.id
        
        if not all([room_key, message]):
            return
        
        db = current_app.db
        
        # Lookup chatroom by room_key
        chatroom_response = db.client.table("group_chatrooms").select("id").eq("room_key", room_key).maybe_single().execute()
        
        if not chatroom_response.data:
            logger.warning(f"Invalid group room key: {room_key}")
            return
        
        chatroom_id = chatroom_response.data["id"]
        
        # Insert into group_messages
        message_insert = db.insert("group_messages", {
            "chatroom_id": chatroom_id,
            "sender_id": sender_id,
            "message": message
        })
        
        if message_insert:
            db_message_id = message_insert["id"]
            
            # Emit to all in the room
            emit("receive_group_message", {
                "message": message,
                "sender_id": sender_id,
                "message_id": db_message_id,
                "created_at": message_insert.get("created_at", "")
            }, room=room_key, include_self=False)
            
            logger.info(f"Group message sent in room {room_key}")
    
    @socketio.on("typing")
    def handle_typing(data):
        """Handle typing indicator."""
        room_key = data.get("room_key")
        is_typing = data.get("is_typing", False)
        
        if room_key:
            emit("user_typing", {
                "user_id": current_user.id,
                "username": current_user.username,
                "is_typing": is_typing
            }, room=room_key, include_self=False)
    
    @socketio.on("mark_read")
    def handle_mark_read(data):
        """Mark messages as read."""
        message_ids = data.get("message_ids", [])
        
        if message_ids:
            db = current_app.db
            for msg_id in message_ids:
                db.update("direct_messages", "id", msg_id, {"read": True})
