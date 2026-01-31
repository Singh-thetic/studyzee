"""
Dashboard route for displaying user's courses, assignments, and tasks.
"""

import logging
from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
from datetime import datetime, date

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    """Main dashboard view."""
    from flask import request
    db = current_app.db
    
    # Get filter month from request (default to current month)
    filter_month = request.args.get("month", "current")
    
    # Get user's enrolled courses
    user_courses_data = db.select_where("user_courses", "user_id", current_user.id)
    courses = []
    
    if user_courses_data:
        course_ids = [uc["course_id"] for uc in user_courses_data]
        for course_id in course_ids:
            course_data = db.select_one("courses", "id", course_id)
            if course_data:
                courses.append(course_data)
    
    # Get upcoming assignments with month filter
    assigned_work = db.select_where("assigned_work", "user_id", current_user.id)
    upcoming_assignments = []
    
    # Get current date for filtering
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    if assigned_work:
        
        for work in assigned_work:
            if work.get("status") != "completed" and work.get("due_date"):
                try:
                    due_date = work["due_date"]
                    if isinstance(due_date, str):
                        due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
                    
                    # Apply month filter
                    should_include = False
                    if filter_month == "all":
                        should_include = due_date >= today
                    elif filter_month == "current":
                        should_include = (due_date.month == current_month and 
                                        due_date.year == current_year and 
                                        due_date >= today)
                    else:
                        # Specific month (format: YYYY-MM)
                        try:
                            filter_year, filter_mon = map(int, filter_month.split("-"))
                            should_include = (due_date.month == filter_mon and 
                                            due_date.year == filter_year)
                        except:
                            should_include = due_date >= today
                    
                    if should_include:
                        # Get work template name
                        template = db.select_one("work_templates", "id", work["work_template_id"])
                        work["name"] = template["name"] if template else "Untitled"
                        
                        # Get course info
                        course = db.select_one("courses", "id", work["course_id"])
                        work["course"] = course if course else {}
                        
                        upcoming_assignments.append(work)
                except Exception as e:
                    logger.warning(f"Error processing assignment: {str(e)}")
                    continue
    
    # Sort by due date
    upcoming_assignments.sort(key=lambda x: x.get("due_date", "9999-12-31"))
    
    # Get study groups
    group_memberships = db.select_where("group_members", "user_id", current_user.id)
    study_groups = []
    
    if group_memberships:
        for membership in group_memberships[:5]:  # Limit to 5 most recent
            group_data = db.select_one("study_groups", "id", membership["study_group_id"])
            if group_data:
                # Get chatroom info
                chatroom = db.select_one("group_chatrooms", "study_group_id", group_data["id"])
                group_data["room_key"] = chatroom["room_key"] if chatroom else None
                study_groups.append(group_data)
    
    # Format tasks for the template (name, due_date, completed, id, type)
    tasks = []
    for assignment in upcoming_assignments[:5]:
        task_name = assignment.get("name", "Untitled")
        due_date = assignment.get("due_date", "TBD")
        completed = assignment.get("status") == "completed"
        task_id = assignment.get("id")
        task_type = "assignment"
        tasks.append((task_name, due_date, completed, task_id, task_type))
    
    return render_template(
        "dashboard.html",
        courses=courses,
        upcoming_assignments=upcoming_assignments,
        study_groups=study_groups,
        tasks=tasks,
        user=current_user,
        filter_month=filter_month,
        current_date=today
    )
