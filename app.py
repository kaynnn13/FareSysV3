"""
Malolos FareWatch - Bayesian Tricycle Fare Deviation Monitoring System
Flask Application Controller
College Thesis / Research Prototype
Research Setting: Xentro Mall Terminal Hub, Malolos City, Bulacan, Philippines
"""

import os
import uuid
from functools import wraps
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_from_directory, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from database import get_db, init_db, DB_FILE, sync_routes_to_json
from bayesian_model import calculate_bayesian_likelihood, DEFAULT_PRIOR

app = Flask(__name__)
app.config["SECRET_KEY"] = "malolos-farewatch-thesis-security-key-2026-v1"
app.config["DATABASE"] = DB_FILE
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024  # 30 MB file size limit for evidence photo/video & ID

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
PRIVATE_ID_FOLDER = os.path.join(BASE_DIR, "private_uploads", "ids")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PRIVATE_ID_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PRIVATE_ID_FOLDER"] = PRIVATE_ID_FOLDER

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
VIDEO_EXTENSIONS = {"mp4", "webm", "mov"}
ALLOWED_EVIDENCE_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
ALLOWED_ID_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_EXTENSIONS = ALLOWED_EVIDENCE_EXTENSIONS

def db():
    return get_db(app.config.get("DATABASE", DB_FILE))

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EVIDENCE_EXTENSIONS

def allowed_id_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_ID_EXTENSIONS

@app.template_filter("is_video")
def is_video_filter(filename):
    if not filename:
        return False
    return filename.rsplit(".", 1)[-1].lower() in VIDEO_EXTENSIONS

# ==============================================================================
# OFFICIAL MALOLOS TERMINAL DESTINATIONS CATALOG (MTPFRB Blg. 2024-02)
# Individual destinations for clean, concise selection instead of long multi-slash route names
# ==============================================================================

OFFICIAL_DESTINATIONS = [
    # 1.0 km (Regular ₱15.00, Special ₱30.00)
    {"name": "San Jose", "distance_km": 1.0, "route_keyword": "San Jose", "bracket": "1.0 km"},
    {"name": "San Felipe", "distance_km": 1.0, "route_keyword": "San Felipe", "bracket": "1.0 km"},
    {"name": "Felisicima", "distance_km": 1.0, "route_keyword": "Felisicima", "bracket": "1.0 km"},
    # 1.5 km (Regular ₱17.50, Special ₱35.00)
    {"name": "Sumapang Matanda (Kanto)", "distance_km": 1.5, "route_keyword": "Sumapang Mtda.", "bracket": "1.5 km"},
    {"name": "Guinhawa Crossing", "distance_km": 1.5, "route_keyword": "Guinhawa Crossing", "bracket": "1.5 km"},
    {"name": "Guinhawa Loob", "distance_km": 1.5, "route_keyword": "Guinhawa Loob", "bracket": "1.5 km"},
    {"name": "Golden Grains", "distance_km": 1.5, "route_keyword": "Golden Grains", "bracket": "1.5 km"},
    # 2.0 km (Regular ₱20.00, Special ₱40.00)
    {"name": "Catmon", "distance_km": 2.0, "route_keyword": "Catmon", "bracket": "2.0 km"},
    {"name": "Liang", "distance_km": 2.0, "route_keyword": "Liang", "bracket": "2.0 km"},
    {"name": "Capitol View Park", "distance_km": 2.0, "route_keyword": "Capitol View Park", "bracket": "2.0 km"},
    {"name": "Alido Subdivision", "distance_km": 2.0, "route_keyword": "Alido Subd.", "bracket": "2.0 km"},
    {"name": "Bulihan (Kanto)", "distance_km": 2.0, "route_keyword": "Bulihan", "bracket": "2.0 km"},
    # 2.5 km (Regular ₱22.50, Special ₱45.00)
    {"name": "Diversion Road", "distance_km": 2.5, "route_keyword": "Diversion", "bracket": "2.5 km"},
    {"name": "Maunlad Kanto", "distance_km": 2.5, "route_keyword": "Maunlad Kanto", "bracket": "2.5 km"},
    {"name": "Sumapang Matanda Gitna", "distance_km": 2.5, "route_keyword": "Sumapang Mtda. Gitna", "bracket": "2.5 km"},
    {"name": "San Gabriel", "distance_km": 2.5, "route_keyword": "San Gabriel", "bracket": "2.5 km"},
    # 3.0 km (Regular ₱25.00, Special ₱50.00)
    {"name": "Bayan (Malolos Proper)", "distance_km": 3.0, "route_keyword": "Bayan (Malolos Proper)", "bracket": "3.0 km"},
    {"name": "Robinsons Place Malolos", "distance_km": 3.0, "route_keyword": "Robinsons", "bracket": "3.0 km"},
    {"name": "New City Hall", "distance_km": 3.0, "route_keyword": "New City Hall", "bracket": "3.0 km"},
    {"name": "South Supermarket", "distance_km": 3.0, "route_keyword": "South Supermarket", "bracket": "3.0 km"},
    {"name": "Centro Escolar University (CEU)", "distance_km": 3.0, "route_keyword": "CEU", "bracket": "3.0 km"},
    # 3.5 km (Regular ₱27.50, Special ₱55.00)
    {"name": "Pinagbakahan", "distance_km": 3.5, "route_keyword": "Pinagbakahan", "bracket": "3.5 km"},
    {"name": "Menzyville", "distance_km": 3.5, "route_keyword": "Menzyville", "bracket": "3.5 km"},
    {"name": "Menzyland Loob", "distance_km": 3.5, "route_keyword": "Menzyland Loob", "bracket": "3.5 km"},
    {"name": "Maunlad 7-Eleven", "distance_km": 3.5, "route_keyword": "Maunlad 7/11", "bracket": "3.5 km"},
    {"name": "Sumapang Bata Bungad", "distance_km": 3.5, "route_keyword": "Sumapang Bata Bungad", "bracket": "3.5 km"},
    # 4.0 km (Regular ₱30.00, Special ₱60.00)
    {"name": "Sumapang Bata Gitna", "distance_km": 4.0, "route_keyword": "Sumapang Bata Gitna", "bracket": "4.0 km"},
    {"name": "Dakila Loob", "distance_km": 4.0, "route_keyword": "Dakila Loob", "bracket": "4.0 km"},
    {"name": "Bungahan Bungad", "distance_km": 4.0, "route_keyword": "Bungahan Bungad", "bracket": "4.0 km"},
    {"name": "Lugam Kanto", "distance_km": 4.0, "route_keyword": "Lugam Kanto", "bracket": "4.0 km"},
    {"name": "Grand Town Phase 1", "distance_km": 4.0, "route_keyword": "Grand Town Phase 1", "bracket": "4.0 km"},
    # 4.5 km (Regular ₱32.50, Special ₱65.00)
    {"name": "Ligas", "distance_km": 4.5, "route_keyword": "Ligas", "bracket": "4.5 km"}
]

def get_destinations_catalog(routes):
    destinations = []
    for d in OFFICIAL_DESTINATIONS:
        matched = None
        for r in routes:
            if d["route_keyword"] in r["name"] or abs(float(r["distance_km"]) - d["distance_km"]) < 0.1:
                matched = r
                break
        if matched:
            destinations.append({
                "name": d["name"],
                "distance_km": float(d["distance_km"]),
                "bracket": d.get("bracket", f"{d['distance_km']} km"),
                "route_id": matched["id"],
                "official_fare": float(matched["official_fare"]),
                "special_fare": float(matched["special_fare"]),
                "discounted_fare": float(matched["discounted_fare"])
            })
    return destinations


# ==============================================================================
# AUTHENTICATION & ACCESS CONTROL DECORATORS
# ==============================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Administrator login is required.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Access denied: You do not have administrator privileges.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
# PUBLIC ROUTES
# ==============================================================================

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("login.html")

        conn = db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password. Please try again.", "danger")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not password or not confirm_password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if len(username) < 3:
            flash("Username must be at least 3 characters long.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html")

        conn = db()
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            conn.close()
            flash("Username is already taken. Please choose another.", "danger")
            return render_template("register.html")

        # Create new commuter account
        hashed_pwd = generate_password_hash(password)
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'commuter')",
            (username, hashed_pwd)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        # Log user in directly upon registration
        session.clear()
        session["user_id"] = user_id
        session["username"] = username
        session["role"] = "commuter"
        flash("Your account has been created successfully. Welcome to Malolos FareWatch!", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been securely logged out.", "info")
    return redirect(url_for("index"))

# ==============================================================================
# COMMUTER & MONITORING CORE ROUTES
# ==============================================================================

@app.route("/dashboard")
@login_required
def dashboard():
    conn = db()
    uid = session["user_id"]

    my_reports_count = conn.execute(
        "SELECT COUNT(*) AS count FROM fare_reports WHERE user_id = ?", (uid,)
    ).fetchone()["count"]

    community_reports_count = conn.execute(
        "SELECT COUNT(*) AS count FROM fare_reports"
    ).fetchone()["count"]

    verified_count = conn.execute(
        "SELECT COUNT(*) AS count FROM fare_reports WHERE verification_status = 'Verified'"
    ).fetchone()["count"]

    deviations_count = conn.execute(
        "SELECT COUNT(*) AS count FROM fare_reports WHERE fare_difference > 0"
    ).fetchone()["count"]

    recent_reports = conn.execute("""
        SELECT fr.*, rt.name AS route_name, rt.official_fare, u.username
        FROM fare_reports fr
        JOIN routes rt ON fr.route_id = rt.id
        JOIN users u ON fr.user_id = u.id
        ORDER BY fr.created_at DESC
        LIMIT 6
    """).fetchall()

    conn.close()

    stats = {
        "my_reports": my_reports_count,
        "community_reports": community_reports_count,
        "verified": verified_count,
        "deviations": deviations_count
    }

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        stats=stats,
        recent_reports=recent_reports
    )

@app.route("/fare-matrix")
@login_required
def fare_matrix():
    conn = db()
    routes = conn.execute("SELECT * FROM routes ORDER BY name ASC").fetchall()
    conn.close()
    return render_template("fare_matrix.html", active_page="fare_matrix", routes=routes)

@app.route("/report", methods=["GET", "POST"])
@login_required
def report_fare():
    conn = db()
    routes = conn.execute("SELECT * FROM routes WHERE active = 1 ORDER BY distance_km ASC, name ASC").fetchall()
    destinations = get_destinations_catalog(routes)

    if request.method == "POST":
        try:
            origin_choice = request.form.get("origin_choice", "").strip() or "Xentro Mall Terminal Hub"
            origin = request.form.get("origin_custom", "").strip() if origin_choice == "custom" else origin_choice
            if not origin:
                origin = "Xentro Mall Terminal Hub"

            destination_choice = request.form.get("destination_choice", "").strip()
            destination = request.form.get("destination_custom", "").strip() if destination_choice == "custom" else destination_choice
            if not destination:
                destination = destination_choice or "Destination Point B"

            route_id = int(request.form.get("route_id", 0))
            reported_fare = float(request.form.get("reported_fare", 0.0))
            trip_type = request.form.get("trip_type", "regular").strip()
            if trip_type not in ["regular", "special", "special_round_trip"]:
                trip_type = "regular"

            try:
                passenger_count = int(request.form.get("passenger_count", 1))
                if passenger_count < 1:
                    passenger_count = 1
            except (ValueError, TypeError):
                passenger_count = 1

            distance_km = float(request.form.get("distance_km")) if request.form.get("distance_km") else None
            travel_time_min = int(request.form.get("travel_time_min")) if request.form.get("travel_time_min") else None
            body_number = request.form.get("body_number", "").strip() or None

            # Timing fields and 24-hour verification restriction
            occurred_at_raw = request.form.get("occurred_at", "").strip()
            occurred_dt = None
            if occurred_at_raw:
                for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                    try:
                        occurred_dt = datetime.strptime(occurred_at_raw, fmt)
                        break
                    except ValueError:
                        pass

            if not occurred_dt:
                flash("Please provide a valid date and time when the trip occurred.", "danger")
                conn.close()
                return render_template("report_fare.html", active_page="report_fare", routes=routes, destinations=destinations)

            now = datetime.now()
            # Enforce: trip must have occurred within the last 24 hours
            if occurred_dt < now - timedelta(hours=24):
                flash("Submission restricted: Reports can only be submitted for trips that occurred within the last 24 hours.", "danger")
                conn.close()
                return render_template("report_fare.html", active_page="report_fare", routes=routes, destinations=destinations)

            # Disallow future trip times (with 5-minute buffer for slight clock skew)
            if occurred_dt > now + timedelta(minutes=5):
                flash("Invalid trip time: Trip occurrence date and time cannot be in the future.", "danger")
                conn.close()
                return render_template("report_fare.html", active_page="report_fare", routes=routes, destinations=destinations)

            occurred_at = occurred_dt.strftime("%Y-%m-%d %H:%M:%S")

            route = None
            if route_id > 0:
                route = conn.execute("SELECT * FROM routes WHERE id = ? AND active = 1", (route_id,)).fetchone()

            if not route:
                if distance_km:
                    closest = conn.execute("SELECT * FROM routes WHERE active = 1 ORDER BY ABS(distance_km - ?) ASC LIMIT 1", (distance_km,)).fetchone()
                    route = closest
                    route_id = closest["id"] if closest else 1
                else:
                    first_r = conn.execute("SELECT * FROM routes WHERE active = 1 LIMIT 1").fetchone()
                    route = first_r
                    route_id = first_r["id"] if first_r else 1

            if reported_fare <= 0:
                flash("Reported fare must be a positive amount.", "danger")
                conn.close()
                return render_template("report_fare.html", active_page="report_fare", routes=routes, destinations=destinations)

            # Determine Official Baseline based on Trip Type & Passenger Count
            if destination_choice == "custom" and distance_km and distance_km > 0:
                # Official tariff formula: ₱15 for 1st km, +₱5/succeeding km
                if distance_km <= 1.0:
                    regular_fare = 15.00
                else:
                    regular_fare = round(15.00 + (distance_km - 1.0) * 5.00, 2)
                special_fare = round(regular_fare * 2.0, 2)
            else:
                regular_fare = float(route["official_fare"])
                special_fare = float(route["special_fare"]) if ("special_fare" in route.keys() and route["special_fare"] > 0) else round(regular_fare * 2.0, 2)

            if trip_type == "special":
                expected_fare = round(special_fare, 2)
            elif trip_type == "special_round_trip":
                expected_fare = round(special_fare * 2.0, 2)
            else:  # regular
                expected_fare = round(regular_fare * passenger_count, 2)

            fare_diff = round(reported_fare - expected_fare, 2)

            # File upload handling for Fare Evidence Photo / Video
            photo_filename = None
            if "fare_photo" in request.files:
                file = request.files["fare_photo"]
                if file and file.filename != "":
                    if not allowed_file(file.filename):
                        flash("Invalid format for fare evidence. Allowed formats: PNG, JPG, JPEG, WEBP, MP4, WEBM, MOV.", "danger")
                        conn.close()
                        return render_template("report_fare.html", active_page="report_fare", routes=routes, destinations=destinations)

                    ext = file.filename.rsplit(".", 1)[1].lower()
                    prefix = "evidence_video" if ext in VIDEO_EXTENSIONS else "evidence"
                    unique_name = f"{prefix}_{uuid.uuid4().hex}_{int(datetime.now().timestamp())}.{ext}"
                    filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
                    file.save(filepath)
                    photo_filename = unique_name

            # Commuter Valid ID Upload (required + admin-only confidential privacy)
            id_filename = None
            id_file = request.files.get("id_photo")
            if not id_file or id_file.filename == "":
                flash("A valid ID upload is required before submitting a fare report.", "danger")
                conn.close()
                return render_template("report_fare.html", active_page="report_fare", routes=routes, destinations=destinations)

            if not allowed_id_file(id_file.filename):
                flash("Invalid image format for commuter ID. Allowed formats: PNG, JPG, JPEG, WEBP.", "danger")
                conn.close()
                return render_template("report_fare.html", active_page="report_fare", routes=routes, destinations=destinations)

            # Keep IDs small and separate from the public static evidence directory.
            id_file.stream.seek(0, os.SEEK_END)
            id_size = id_file.stream.tell()
            id_file.stream.seek(0)
            if id_size > 5 * 1024 * 1024:
                flash("The valid ID file must be 5 MB or smaller.", "danger")
                conn.close()
                return render_template("report_fare.html", active_page="report_fare", routes=routes, destinations=destinations)

            id_ext = id_file.filename.rsplit(".", 1)[1].lower()
            unique_id_name = f"id_confidential_{uuid.uuid4().hex}_{int(datetime.now().timestamp())}.{id_ext}"
            id_filepath = os.path.join(app.config["PRIVATE_ID_FOLDER"], unique_id_name)
            id_file.save(id_filepath)
            id_filename = unique_id_name

            # Compute Bayesian Model Probability against the calculated trip expected baseline
            has_photo = bool(photo_filename)
            bayesian_res = calculate_bayesian_likelihood(reported_fare, expected_fare, has_photo=has_photo)
            posterior = bayesian_res["posterior"]

            cursor = conn.execute("""
                INSERT INTO fare_reports (
                    user_id, route_id, origin, destination, trip_type, passenger_count,
                    reported_fare, expected_fare, fare_difference, distance_km,
                    travel_time_min, body_number, photo_filename, id_filename, verification_status,
                    posterior_probability, occurred_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
            """, (
                session["user_id"], route_id, origin, destination, trip_type, passenger_count,
                reported_fare, expected_fare, fare_diff, distance_km, travel_time_min,
                body_number, photo_filename, id_filename, posterior, occurred_at
            ))
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()

            flash("Your fare report has been submitted successfully! Review the Bayesian estimation below.", "success")
            return redirect(url_for("report_details", report_id=new_id))

        except Exception as e:
            flash(f"Error submitting report: {str(e)}", "danger")

    conn.close()
    return render_template("report_fare.html", active_page="report_fare", routes=routes, destinations=destinations)

@app.route("/fare-reports")
@login_required
def fare_reports():
    route_id = request.args.get("route", "").strip()
    date_range = request.args.get("date_range", "").strip()
    likelihood = request.args.get("likelihood", "").strip()
    trip_type = request.args.get("trip_type", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 6

    conn = db()
    routes = conn.execute("SELECT * FROM routes WHERE active = 1 ORDER BY name ASC").fetchall()

    query = """
        SELECT fr.*, rt.name AS route_name, rt.official_fare, rt.special_fare
        FROM fare_reports fr
        JOIN routes rt ON fr.route_id = rt.id
        WHERE 1 = 1
    """
    params = []

    if route_id:
        query += " AND fr.route_id = ?"
        params.append(route_id)

    if trip_type in ["regular", "special", "special_round_trip"]:
        query += " AND fr.trip_type = ?"
        params.append(trip_type)

    if date_range == "today":
        query += " AND date(fr.created_at) = date('now', 'localtime')"
    elif date_range == "week":
        query += " AND date(fr.created_at) >= date('now', '-7 days', 'localtime')"
    elif date_range == "month":
        query += " AND date(fr.created_at) >= date('now', '-30 days', 'localtime')"

    if likelihood == "low":
        query += " AND fr.posterior_probability < 0.40"
    elif likelihood == "medium":
        query += " AND fr.posterior_probability >= 0.40 AND fr.posterior_probability < 0.70"
    elif likelihood == "high":
        query += " AND fr.posterior_probability >= 0.70"

    # Count total matching for pagination
    count_query = f"SELECT COUNT(*) AS total FROM ({query})"
    total_count = conn.execute(count_query, params).fetchone()["total"]

    # Add sorting and pagination limits
    query += " ORDER BY fr.created_at DESC LIMIT ? OFFSET ?"
    offset = (page - 1) * per_page
    params.extend([per_page, offset])

    reports = conn.execute(query, params).fetchall()
    conn.close()

    total_pages = max(1, (total_count + per_page - 1) // per_page)
    start_idx = 0 if total_count == 0 else offset + 1
    end_idx = min(offset + per_page, total_count)

    pagination = {
        "page": page,
        "per_page": per_page,
        "total_count": total_count,
        "total_pages": total_pages,
        "start_idx": start_idx,
        "end_idx": end_idx,
        "has_prev": page > 1,
        "has_next": page < total_pages
    }

    return render_template(
        "fare_reports.html",
        active_page="fare_reports",
        reports=reports,
        routes=routes,
        pagination=pagination,
        current_route=route_id,
        current_date=date_range,
        current_likelihood=likelihood,
        current_trip_type=trip_type
    )

@app.route("/my-reports")
@login_required
def my_reports():
    conn = db()
    uid = session["user_id"]
    reports = conn.execute("""
        SELECT fr.*, rt.name AS route_name, rt.official_fare, rt.special_fare
        FROM fare_reports fr
        JOIN routes rt ON fr.route_id = rt.id
        WHERE fr.user_id = ?
        ORDER BY fr.created_at DESC
    """, (uid,)).fetchall()
    conn.close()
    return render_template("my_reports.html", active_page="my_reports", reports=reports)

@app.route("/reports/<int:report_id>")
@login_required
def report_details(report_id):
    conn = db()
    report = conn.execute("""
        SELECT fr.*, rt.name AS route_name, rt.official_fare, rt.special_fare, rt.discounted_fare, u.username
        FROM fare_reports fr
        JOIN routes rt ON fr.route_id = rt.id
        JOIN users u ON fr.user_id = u.id
        WHERE fr.id = ?
    """, (report_id,)).fetchone()

    if not report:
        conn.close()
        flash("The requested fare report was not found.", "danger")
        return redirect(url_for("fare_reports"))

    # Authorization check for private chat and confidential commuter ID:
    # Only accessible to administrators and the specific reporter (owner)
    current_uid = session.get("user_id")
    current_role = session.get("role")
    is_admin = (current_role == "admin")
    is_owner = (current_uid == report["user_id"])
    can_view_chat = is_admin or is_owner
    can_view_id = is_admin

    messages = []
    if can_view_chat:
        messages = conn.execute("""
            SELECT m.*, u.username, u.role
            FROM report_messages m
            JOIN users u ON m.user_id = u.id
            WHERE m.report_id = ?
            ORDER BY m.created_at ASC
        """, (report_id,)).fetchall()

    conn.close()

    expected_fare = report["expected_fare"] if (report["expected_fare"] and report["expected_fare"] > 0) else report["official_fare"]

    # Re-calculate complete Bayesian metrics for display
    has_photo = bool(report["photo_filename"])
    calc = calculate_bayesian_likelihood(
        report["reported_fare"],
        expected_fare,
        has_photo=has_photo
    )

    return render_template(
        "report_details.html",
        active_page="fare_reports",
        report=report,
        calc=calc,
        messages=messages,
        can_view_chat=can_view_chat,
        can_view_id=can_view_id,
        is_admin=is_admin,
        is_owner=is_owner
    )

@app.route("/reports/<int:report_id>/messages", methods=["POST"])
@login_required
def post_report_message(report_id):
    conn = db()
    report = conn.execute("SELECT user_id FROM fare_reports WHERE id = ?", (report_id,)).fetchone()

    if not report:
        conn.close()
        flash("The requested fare report was not found.", "danger")
        return redirect(url_for("fare_reports"))

    # Authorization check: only admin or the specific reporter
    current_uid = session.get("user_id")
    current_role = session.get("role")
    if current_role != "admin" and current_uid != report["user_id"]:
        conn.close()
        flash("Access denied: You are not authorized to participate in this inquiry thread.", "danger")
        return redirect(url_for("report_details", report_id=report_id))

    content = request.form.get("message", "").strip()
    if not content:
        conn.close()
        flash("Message cannot be empty.", "warning")
        return redirect(url_for("report_details", report_id=report_id) + "#chat-section")

    conn.execute("""
        INSERT INTO report_messages (report_id, user_id, message)
        VALUES (?, ?, ?)
    """, (report_id, current_uid, content))
    conn.commit()
    conn.close()

    flash("Your inquiry message has been sent.", "success")
    return redirect(url_for("report_details", report_id=report_id) + "#chat-section")

@app.route("/profile")
@login_required
def profile():
    conn = db()
    uid = session["user_id"]
    user = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    user_report_count = conn.execute(
        "SELECT COUNT(*) AS count FROM fare_reports WHERE user_id = ?", (uid,)
    ).fetchone()["count"]
    conn.close()
    return render_template(
        "profile.html",
        active_page="profile",
        user=user,
        user_report_count=user_report_count
    )

@app.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_password or not new_password or not confirm_password:
        flash("All password fields are required.", "danger")
        return redirect(url_for("profile"))

    if new_password != confirm_password:
        flash("New passwords do not match.", "danger")
        return redirect(url_for("profile"))

    if len(new_password) < 6:
        flash("New password must be at least 6 characters long.", "danger")
        return redirect(url_for("profile"))

    conn = db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    if not check_password_hash(user["password_hash"], current_password):
        conn.close()
        flash("Your current password is incorrect.", "danger")
        return redirect(url_for("profile"))

    new_hash = generate_password_hash(new_password)
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, session["user_id"]))
    conn.commit()
    conn.close()

    flash("Password updated successfully.", "success")
    return redirect(url_for("profile"))

# ==============================================================================
# ADMINISTRATOR CONTROLS & MONITORING
# ==============================================================================

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = db()

    user_count = conn.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'commuter'").fetchone()["count"]
    route_count = conn.execute("SELECT COUNT(*) AS count FROM routes WHERE active = 1").fetchone()["count"]
    report_count = conn.execute("SELECT COUNT(*) AS count FROM fare_reports").fetchone()["count"]
    deviations_count = conn.execute("SELECT COUNT(*) AS count FROM fare_reports WHERE fare_difference > 0").fetchone()["count"]

    stats = {
        "users": user_count,
        "routes": route_count,
        "reports": report_count,
        "deviations": deviations_count
    }

    # Route summary with average likelihood and average reported fare
    # Sorted by highest average likelihood first as specified
    route_summary = conn.execute("""
        SELECT 
            rt.id,
            rt.name,
            rt.official_fare,
            COUNT(fr.id) AS report_count,
            COALESCE(AVG(fr.reported_fare), 0) AS avg_reported,
            COALESCE(AVG(fr.posterior_probability), 0) AS avg_prob
        FROM routes rt
        LEFT JOIN fare_reports fr ON rt.id = fr.route_id
        WHERE rt.active = 1
        GROUP BY rt.id
        ORDER BY avg_prob DESC, report_count DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        active_page="admin_dashboard",
        stats=stats,
        route_summary=route_summary
    )

@app.route("/admin/reports")
@admin_required
def admin_reports():
    conn = db()
    reports = conn.execute("""
        SELECT fr.*, rt.name AS route_name, rt.official_fare, rt.special_fare, u.username
        FROM fare_reports fr
        JOIN routes rt ON fr.route_id = rt.id
        JOIN users u ON fr.user_id = u.id
        ORDER BY fr.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("admin_reports.html", active_page="admin_reports", reports=reports)

@app.route("/admin/reports/<int:report_id>/status", methods=["POST"])
@admin_required
def update_report_status(report_id):
    status = request.form.get("status")
    if status not in {"Pending", "Verified", "Rejected"}:
        flash("Invalid status value.", "danger")
        return redirect(url_for("admin_reports"))

    conn = db()
    conn.execute("UPDATE fare_reports SET verification_status = ? WHERE id = ?", (status, report_id))
    conn.commit()
    conn.close()

    flash(f"Report #{report_id} status updated to {status}.", "success")
    return redirect(url_for("admin_reports"))

@app.route("/admin/routes")
@admin_required
def admin_routes():
    conn = db()
    routes = conn.execute("""
        SELECT rt.*, COUNT(fr.id) AS report_count
        FROM routes rt
        LEFT JOIN fare_reports fr ON rt.id = fr.route_id
        GROUP BY rt.id
        ORDER BY rt.active DESC, rt.name ASC
    """).fetchall()
    conn.close()
    return render_template("admin_routes.html", active_page="admin_routes", routes=routes)

@app.route("/admin/routes/add", methods=["POST"])
@admin_required
def add_route():
    name = request.form.get("name", "").strip()
    official_fare = request.form.get("official_fare", "")
    distance_km = request.form.get("distance_km", "1.0")
    special_fare = request.form.get("special_fare", "")

    try:
        fare = float(official_fare)
        dist = float(distance_km) if distance_km else 1.0
        if not name or fare <= 0:
            raise ValueError()

        spec = float(special_fare) if special_fare else round(fare * 2.0, 2)
        disc = round(fare * 0.80, 2)

        conn = db()
        existing = conn.execute("SELECT id FROM routes WHERE name = ?", (name,)).fetchone()
        if existing:
            conn.close()
            flash("A route with this name already exists.", "danger")
            return redirect(url_for("admin_routes"))

        conn.execute("""
            INSERT INTO routes (name, distance_km, official_fare, special_fare, discounted_fare, active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (name, dist, fare, spec, disc))
        conn.commit()
        conn.close()

        # Automatically update physical fare_matrix.json file
        sync_routes_to_json(app.config.get("DATABASE", DB_FILE))

        flash(f"Route '{name}' successfully configured at ₱{fare:.2f} and saved to fare_matrix.json.", "success")
    except ValueError:
        flash("Please provide a valid route name and positive official fare amount.", "danger")

    return redirect(url_for("admin_routes"))

@app.route("/admin/routes/<int:route_id>/edit", methods=["POST"])
@admin_required
def edit_route(route_id):
    name = request.form.get("name", "").strip()
    official_fare = request.form.get("official_fare", "")
    special_fare = request.form.get("special_fare", "")
    distance_km = request.form.get("distance_km", "")

    try:
        fare = float(official_fare)
        if not name or fare <= 0:
            raise ValueError()

        conn = db()
        route = conn.execute("SELECT * FROM routes WHERE id = ?", (route_id,)).fetchone()
        if not route:
            conn.close()
            flash("Route not found.", "danger")
            return redirect(url_for("admin_routes"))

        dist = float(distance_km) if distance_km else float(route["distance_km"] or 1.0)
        spec = float(special_fare) if special_fare else round(fare * 2.0, 2)
        disc = round(fare * 0.80, 2)

        conn.execute("""
            UPDATE routes 
            SET name = ?, official_fare = ?, special_fare = ?, discounted_fare = ?, distance_km = ?
            WHERE id = ?
        """, (name, fare, spec, disc, dist, route_id))
        conn.commit()
        conn.close()

        # Automatically update physical fare_matrix.json file
        sync_routes_to_json(app.config.get("DATABASE", DB_FILE))

        flash(f"Route '{name}' updated to ₱{fare:.2f} and saved to fare_matrix.json.", "success")
    except ValueError:
        flash("Invalid fare value entered.", "danger")

    return redirect(url_for("admin_routes"))

@app.route("/admin/routes/<int:route_id>/toggle", methods=["POST"])
@admin_required
def toggle_route(route_id):
    conn = db()
    route = conn.execute("SELECT active, name FROM routes WHERE id = ?", (route_id,)).fetchone()
    if route:
        new_status = 0 if route["active"] == 1 else 1
        conn.execute("UPDATE routes SET active = ? WHERE id = ?", (new_status, route_id))
        conn.commit()
        status_label = "activated" if new_status == 1 else "deactivated"
        sync_routes_to_json(app.config.get("DATABASE", DB_FILE))
        flash(f"Route '{route['name']}' has been {status_label} and saved to fare_matrix.json.", "info")
    conn.close()
    return redirect(url_for("admin_routes"))


# ==============================================================================
# STATIC & CONTROLLED FILE SERVING
# ==============================================================================

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """Serve commuter-submitted photo/video evidence.
    Evidence is intentionally viewable to authenticated commuters/admins.
    """
    safe_name = secure_filename(filename)
    return send_from_directory(app.config["UPLOAD_FOLDER"], safe_name)

@app.route("/admin/private-id/<path:filename>")
@admin_required
def admin_private_id(filename):
    """Serve a commuter's valid ID ONLY to authenticated administrators.
    This file is stored outside Flask's static directory so other commuters
    cannot access it through /static/... or the public evidence endpoint.
    """
    safe_name = secure_filename(filename)
    return send_from_directory(app.config["PRIVATE_ID_FOLDER"], safe_name, as_attachment=False)

@app.route("/api/bayesian")
def api_bayesian():
    """Public helper API for live Bayesian calculation testing."""
    try:
        reported = float(request.args.get("reported", 20.0))
        official = float(request.args.get("official", 20.0))
        has_photo = request.args.get("photo", "0") in ("1", "true", "True")
        result = calculate_bayesian_likelihood(reported, official, has_photo=has_photo)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    init_db()
    print("Malolos FareWatch application started at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
