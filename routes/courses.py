"""
Course management routes - add, view, edit, delete courses.
"""

import logging
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from services.pdf_processor import extract_text_from_pdf, parse_course_sections
from services.ai_assistant import parse_course_info

logger = logging.getLogger(__name__)
courses_bp = Blueprint("courses", __name__)


def _parse_date(date_str):
    """Parse date string from AI response to YYYY-MM-DD format."""
    if not date_str or date_str == "[TBD]":
        return None
    try:
        # Try MM/DD/YY format
        from datetime import datetime
        if "/" in date_str:
            parts = date_str.split("/")
            if len(parts) == 3:
                month, day, year = parts
                if len(year) == 2:
                    year = "20" + year
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return None
    except:
        return None


def _parse_time(time_str):
    """Parse time string from AI response to HH:MM format."""
    if not time_str or time_str == "[TBD]":
        return None
    try:
        # Extract HH:MM from string
        import re
        match = re.search(r'(\d{1,2}):(\d{2})', time_str)
        if match:
            hour, minute = match.groups()
            return f"{hour.zfill(2)}:{minute}"
        return None
    except:
        return None


@courses_bp.route("/courses")
@login_required
def list_courses():
    """List all user's courses."""
    db = current_app.db
    
    # Get user's enrolled courses
    user_courses_data = db.select_where("user_courses", "user_id", current_user.id)
    courses = []
    
    if user_courses_data:
        for uc in user_courses_data:
            course_data = db.select_one("courses", "id", uc["course_id"])
            if course_data:
                courses.append(course_data)
    
    return render_template("course_data.html", courses=courses)


@courses_bp.route("/course/<course_id>", methods=["GET", "POST"])
@login_required
def course_page(course_id):
    """View and edit individual course page."""
    db = current_app.db
    
    if request.method == "POST":
        # Update course information
        section = request.form.get("section")
        professor_name = request.form.get("professor_name")
        professor_email = request.form.get("professor_email")
        class_schedule = request.form.getlist("class_schedule")
        
        # Update course
        course_update = {
            "section": section,
            "professor": professor_name,
            "professor_email": professor_email,
            "class_schedule": ",".join(class_schedule),
        }
        
        db.update("courses", "id", course_id, course_update)
        
        # Handle work/assignment updates
        work_data = {}
        for field_name, value in request.form.items():
            if field_name.startswith("work_") and "_" in field_name:
                parts = field_name.split("_", 2)
                if len(parts) >= 3:
                    work_id = parts[1]
                    field_type = parts[2]
                    
                    if work_id not in work_data:
                        work_data[work_id] = {"work_id": work_id}
                    
                    if field_type == "name":
                        work_data[work_id]["name"] = value if value not in ["TBD", "", None] else None
                    elif field_type == "weightage":
                        work_data[work_id]["weightage"] = float(value) if value not in ["TBD", "", None] else None
                    elif field_type == "marks_obtained":
                        work_data[work_id]["marks_obtained"] = float(value) if value not in ["TBD", "", None] else None
                    elif field_type == "due_date":
                        work_data[work_id]["due_date"] = value if value not in ["TBD", "", None] else None
                    elif field_type == "due_time":
                        work_data[work_id]["due_time"] = value if value not in ["TBD", "", None] else None
        
        # Update each assignment
        for work_id, work_fields in work_data.items():
            # Update work template
            db.update("work_templates", "id", work_id, {
                "name": work_fields.get("name"),
                "weightage": work_fields.get("weightage"),
                "due_date": work_fields.get("due_date"),
                "due_time": work_fields.get("due_time"),
            })
            
            # Update assigned work
            db.update("assigned_work", "work_template_id", work_id, {
                "marks_obtained": work_fields.get("marks_obtained"),
                "due_date": work_fields.get("due_date"),
                "due_time": work_fields.get("due_time"),
            })
        
        flash("Course updated successfully!", "success")
        return redirect(url_for("courses.course_page", course_id=course_id))
    
    # GET request - fetch course data
    course_data = db.select_one("courses", "id", course_id)
    if not course_data:
        flash("Course not found", "error")
        return redirect(url_for("dashboard.dashboard"))
    
    # Get assigned work
    assigned_work_data = db.select_where("assigned_work", "course_id", course_id)
    work_templates_data = db.select_where("work_templates", "course_id", course_id)
    
    # Combine work data
    combined_work = []
    for assigned in (assigned_work_data or []):
        template = next((t for t in (work_templates_data or []) if t["id"] == assigned["work_template_id"]), {})
        combined_work.append({
            "work_id": assigned["work_template_id"],
            "name": template.get("name", "Untitled"),
            "weightage": template.get("weightage", 0),
            "marks_obtained": assigned.get("marks_obtained"),
            "due_date": assigned.get("due_date") or template.get("due_date") or "TBD",
            "due_time": assigned.get("due_time") or template.get("due_time") or "TBD",
        })
    
    course_info = {
        "id": course_data["id"],
        "subject_id": course_data.get("subject_id", "N/A"),
        "course_code": course_data.get("course_code", "N/A"),
        "course_name": course_data.get("course_name", "N/A"),
        "section": course_data.get("section", "N/A"),
        "professor": {
            "name": course_data.get("professor", "Unknown"),
            "email": course_data.get("professor_email", "N/A"),
        },
        "class_schedule": (course_data.get("class_schedule") or "").split(","),
        "assigned_work": combined_work,
    }
    
    return render_template("course.html", course=course_info)


@courses_bp.route("/add_course", methods=["GET", "POST"])
@login_required
def add_course():
    """Add new course with AI-powered PDF parsing in 3 steps."""
    from flask import session
    db = current_app.db
    
    # Get current step
    step = int(request.args.get("step", request.form.get("step", 1)))
    
    if request.method == "GET":
        # Render appropriate step
        course_data = session.get("course_temp_data", {})
        assignments = session.get("course_temp_assignments", [])
        return render_template("add_course_ai.html", step=step, course_data=course_data, assignments=assignments)
    
    # POST handling
    if step == 1:
        # Step 1: Save basic course info and move to step 2
        course_data = {
            "subject_id": request.form.get("subject_id", "").strip().upper(),
            "course_code": request.form.get("course_code", "").strip(),
            "course_name": request.form.get("course_name", "").strip(),
            "section": request.form.get("section", "").strip(),
        }
        
        if not all([course_data["subject_id"], course_data["course_code"], course_data["course_name"]]):
            flash("Subject ID, course code, and course name are required", "error")
            return render_template("add_course_ai.html", step=1, course_data=course_data)
        
        session["course_temp_data"] = course_data
        return redirect(url_for("courses.add_course", step=2))
    
    elif step == 2:
        # Step 2: Process PDFs or skip to step 3
        course_data = session.get("course_temp_data", {})
        
        files = request.files.getlist("pdf_files")
        
        # If files uploaded, process with AI
        if files and files[0].filename:
            user_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], str(current_user.id))
            os.makedirs(user_folder, exist_ok=True)
            
            pdf_texts = []
            for file in files:
                if file and file.filename.endswith(".pdf"):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(user_folder, filename)
                    file.save(filepath)
                    
                    try:
                        text = extract_text_from_pdf(filepath)
                        pdf_texts.append(text)
                        os.remove(filepath)  # Clean up
                    except Exception as e:
                        logger.error(f"Error processing PDF: {str(e)}")
                        flash(f"Error processing {filename}", "error")
            
            if pdf_texts:
                try:
                    # Use AI to parse course info
                    ai_response = parse_course_info(pdf_texts)
                    course_info = parse_course_sections(ai_response)
                    
                    # Extract first section info (or merge if multiple)
                    if course_info:
                        first_section = list(course_info.values())[0]
                        
                        # Update course data with AI-extracted info
                        course_data["professor"] = first_section.get("instructor_name", "")
                        course_data["professor_email"] = first_section.get("instructor_email", "")
                        course_data["class_schedule"] = first_section.get("lecture_days", [])
                        
                        # Parse assignments from weightage table
                        assignments = []
                        weightage = first_section.get("weightage", {})
                        for name, details in weightage.items():
                            assignments.append({
                                "name": name,
                                "weight": details.get("weight", "").replace("%", "").strip(),
                                "due_date": _parse_date(details.get("due_date", "")),
                                "due_time": _parse_time(details.get("due_time", "")),
                            })
                        
                        session["course_temp_assignments"] = assignments
                        flash(f"✨ AI extracted {len(assignments)} assignment(s) from your PDFs!", "success")
                except Exception as e:
                    logger.error(f"AI parsing error: {str(e)}")
                    flash("AI couldn't parse the PDFs. You can still add details manually.", "warning")
        
        session["course_temp_data"] = course_data
        return redirect(url_for("courses.add_course", step=3))
    
    elif step == 3:
        # Step 3: Final confirmation and save to database
        course_data = session.get("course_temp_data", {})
        
        # Update with any manual edits
        course_data["professor"] = request.form.get("professor", "").strip()
        course_data["professor_email"] = request.form.get("professor_email", "").strip()
        course_data["class_schedule"] = ",".join(request.form.getlist("class_schedule"))
        
        # Check if course already exists
        existing = db.client.table("courses").select("id").eq("subject_id", course_data["subject_id"]).eq("course_code", int(course_data["course_code"])).eq("section", course_data["section"]).execute()
        
        if existing.data:
            course_id = existing.data[0]["id"]
        else:
            # Create new course
            new_course_data = {
                "subject_id": course_data["subject_id"],
                "course_code": int(course_data["course_code"]),
                "course_name": course_data["course_name"],
                "section": course_data["section"],
                "professor": course_data.get("professor"),
                "professor_email": course_data.get("professor_email"),
                "class_schedule": course_data.get("class_schedule"),
            }
            new_course = db.insert("courses", new_course_data)
            if not new_course:
                flash("Failed to create course", "error")
                return redirect(url_for("courses.add_course", step=3))
            course_id = new_course["id"]
        
        # Enroll user in course
        db.insert("user_courses", {
            "user_id": current_user.id,
            "course_id": course_id
        })
        
        # Create assignments if any
        assignments = session.get("course_temp_assignments", [])
        for idx in range(len(assignments)):
            name = request.form.get(f"assignment_{idx}_name")
            weight = request.form.get(f"assignment_{idx}_weight")
            due_date = request.form.get(f"assignment_{idx}_due_date")
            due_time = request.form.get(f"assignment_{idx}_due_time")
            
            if name:
                # Create work template
                template = db.insert("work_templates", {
                    "course_id": course_id,
                    "name": name,
                    "work_type": "assignment",
                    "weightage": float(weight) if weight else None,
                    "due_date": due_date if due_date else None,
                    "due_time": due_time if due_time else None,
                })
                
                if template:
                    # Create assigned work for user
                    db.insert("assigned_work", {
                        "user_id": current_user.id,
                        "work_template_id": template["id"],
                        "course_id": course_id,
                        "due_date": due_date if due_date else None,
                        "due_time": due_time if due_time else None,
                    })
        
        # Clear session data
        session.pop("course_temp_data", None)
        session.pop("course_temp_assignments", None)
        
        flash(f"Course {course_data['subject_id']} {course_data['course_code']} added successfully!", "success")
        return redirect(url_for("courses.course_page", course_id=course_id))
    
    return render_template("add_course_ai.html", step=1)


@courses_bp.route("/delete_course/<course_id>", methods=["POST"])
@login_required
def delete_course(course_id):
    """Remove course from user's enrollment."""
    db = current_app.db
    
    # Find and delete enrollment
    enrollments = db.client.table("user_courses").select("id").eq("user_id", current_user.id).eq("course_id", course_id).execute()
    
    if enrollments.data:
        enrollment_id = enrollments.data[0]["id"]
        db.delete("user_courses", "id", enrollment_id)
        flash("Course removed successfully!", "success")
    else:
        flash("Course not found in your enrollments", "error")
    
    return redirect(url_for("dashboard.dashboard"))
