"""
Flashcards route with AI-powered generation from PDFs.
"""

import logging
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from services.pdf_processor import extract_text_from_pdf
from services.ai_assistant import generate_flashcards

logger = logging.getLogger(__name__)
flashcards_bp = Blueprint("flashcards", __name__)


@flashcards_bp.route("/flashcards", methods=["GET", "POST"])
@login_required
def flashcards():
    """Generate and display flashcards from study materials."""
    
    if request.method == "POST":
        # Check if file was uploaded
        if "pdf_file" not in request.files:
            flash("No file uploaded", "error")
            return redirect(url_for("flashcards.flashcards"))
        
        file = request.files["pdf_file"]
        if file.filename == "":
            flash("No file selected", "error")
            return redirect(url_for("flashcards.flashcards"))
        
        if not file.filename.endswith(".pdf"):
            flash("Only PDF files are supported", "error")
            return redirect(url_for("flashcards.flashcards"))
        
        # Save and process PDF
        user_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(user_folder, filename)
        file.save(filepath)
        
        try:
            # Extract text from PDF
            pdf_text = extract_text_from_pdf(filepath)
            
            # Generate flashcards using AI
            flashcards_list = generate_flashcards(pdf_text)
            
            # Clean up PDF
            os.remove(filepath)
            
            if flashcards_list:
                return render_template(
                    "flashcards.html",
                    flashcards=flashcards_list,
                    has_flashcards=True
                )
            else:
                flash("Failed to generate flashcards. Please try again.", "error")
                return redirect(url_for("flashcards.flashcards"))
        
        except Exception as e:
            logger.error(f"Error generating flashcards: {str(e)}")
            flash(f"Error processing PDF: {str(e)}", "error")
            
            # Clean up on error
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return redirect(url_for("flashcards.flashcards"))
    
    # GET request - show upload form
    return render_template("flashcards.html", has_flashcards=False)


@flashcards_bp.route("/upload-notes", methods=["POST"])
@login_required
def upload_notes():
    """Upload notes and generate flashcards."""
    try:
        logger.info(f"Upload notes request received. Files: {request.files.keys()}")
        logger.info(f"Form data: {request.form.keys()}")
        
        # Check if file was uploaded
        if "notes_file" not in request.files:
            logger.error("No file in request")
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files["notes_file"]
        set_name = request.form.get("set_name", "Untitled Set").strip()
        
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.endswith(".pdf"):
            return jsonify({"error": "Only PDF files are supported"}), 400
        
        # Save and process PDF
        user_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(user_folder, filename)
        file.save(filepath)
        
        try:
            # Extract text from PDF
            logger.info(f"Extracting text from PDF: {filepath}")
            pdf_text = extract_text_from_pdf(filepath)
            logger.info(f"Extracted {len(pdf_text)} characters from PDF")
            
            # Generate flashcards using AI
            logger.info("Generating flashcards with AI...")
            flashcards_list = generate_flashcards(pdf_text)
            logger.info(f"Generated {len(flashcards_list) if flashcards_list else 0} flashcards")
            
            # Clean up PDF
            os.remove(filepath)
            logger.info("Cleaned up PDF file")
            
            if flashcards_list:
                # Store flashcards in database
                db = current_app.db
                logger.info(f"Storing {len(flashcards_list)} flashcards in database")
                
                # Create flashcard set
                flashcard_set = db.insert("flashcard_sets", {
                    "user_id": current_user.id,
                    "name": set_name
                })
                logger.info(f"Created flashcard set: {flashcard_set}")
                
                if not flashcard_set:
                    logger.error("Failed to create flashcard set")
                    return jsonify({"error": "Failed to create flashcard set"}), 500
                
                set_id = flashcard_set["id"]
                
                # Save individual flashcards
                for i, card in enumerate(flashcards_list):
                    logger.info(f"Saving flashcard {i+1}/{len(flashcards_list)}")
                    result = db.insert("flashcards", {
                        "set_id": set_id,
                        "question": card.get("question", ""),
                        "answer": card.get("answer", "")
                    })
                    if not result:
                        logger.error(f"Failed to save flashcard {i+1}")
                
                logger.info(f"Successfully saved all flashcards for set {set_id}")
                
                return jsonify({
                    "message": f"Successfully generated {len(flashcards_list)} flashcards!",
                    "set_name": set_name,
                    "set_id": set_id,
                    "count": len(flashcards_list)
                })
            else:
                return jsonify({"error": "Failed to generate flashcards"}), 500
        
        except Exception as e:
            logger.error(f"Error generating flashcards: {str(e)}")
            # Clean up on error
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({"error": f"Error processing PDF: {str(e)}"}), 500
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@flashcards_bp.route("/flashcard-sets")
@login_required  
def flashcard_sets():
    """Get list of saved flashcard sets for current user."""
    db = current_app.db
    
    # Get user's flashcard sets
    sets_data = db.select_where("flashcard_sets", "user_id", current_user.id)
    
    sets = []
    if sets_data:
        for set_item in sets_data:
            # Count flashcards in this set
            cards = db.select_where("flashcards", "set_id", set_item["id"])
            card_count = len(cards) if cards else 0
            
            sets.append({
                "set_id": set_item["id"],
                "name": set_item["name"],
                "count": card_count,
                "created_at": set_item.get("created_at", "")
            })
    
    return jsonify({"sets": sets})


@flashcards_bp.route("/practice/<set_id>", methods=["GET"])
@login_required
def practice(set_id):
    """Practice page for a specific flashcard set."""
    db = current_app.db
    
    # Get flashcard set
    flashcard_set = db.select_one("flashcard_sets", "id", set_id)
    
    if not flashcard_set or flashcard_set["user_id"] != current_user.id:
        flash("Flashcard set not found", "error")
        return redirect(url_for("flashcards.flashcards"))
    
    # Get flashcards in this set
    cards = db.select_where("flashcards", "set_id", set_id)
    
    flashcards_list = []
    if cards:
        for card in cards:
            flashcards_list.append({
                "id": card["id"],
                "question": card["question"],
                "answer": card["answer"]
            })
    
    return render_template(
        "practice.html",
        flashcards=flashcards_list,
        set_name=flashcard_set["name"],
        set_id=set_id
    )
