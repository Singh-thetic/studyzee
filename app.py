from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = "supersecretkey"  # Required for flash messages
CORS(app)  # Enable CORS

# Supabase client setup
SUPABASE_URL = "https://mmtdthmtsasvthysqwrx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1tdGR0aG10c2FzdnRoeXNxd3J4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk2NDYzMTQsImV4cCI6MjA1NTIyMjMxNH0.uxTcUuR2xAs2gQjbA0bqwsRyOVArXY6qD99eo2os9wU"

# Initialize Supabase Client
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def home():
    return render_template("login.html")  # Renders the login page

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        flash("Email and password are required", "error")
        return redirect(url_for("home"))

    try:
        # Sign in the user with Supabase
        response = supabase_client.auth.sign_in_with_password({"email": email, "password": password})

        if response.user:
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password", "error")
            return redirect(url_for("home"))
    except Exception as e:
        flash(str(e), "error")
        return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    math_content = """"""
    return render_template("dashboard.html", math_content)  # Renders the dashboard page after login

@app.route("/signup", methods=["POST"])
def signup():
    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        flash("Email and password are required", "error")
        return redirect(url_for("home"))

    try:
        # Sign up the user with Supabase
        response = supabase_client.auth.sign_up({"email": email, "password": password})

        if response.user:
            flash("User created successfully! Please log in.", "success")
            return redirect(url_for("home"))
        else:
            flash("Failed to create user", "error")
            return redirect(url_for("home"))
    except Exception as e:
        flash(str(e), "error")
        return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
