
from flask import Flask, render_template, request, send_file, redirect, Response
from PIL import Image
import os
import uuid
from datetime import datetime
import psycopg2
import csv

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# Create emails table if it doesn't exist
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id SERIAL PRIMARY KEY,
                timestamp TEXT,
                ip TEXT,
                email TEXT
            )
        """)
        conn.commit()

user_limits = {}

@app.route("/", methods=["GET", "POST"])
def index():
    client_ip = request.remote_addr
    today = datetime.now().strftime('%Y-%m-%d')
    user_data = user_limits.get(client_ip, {'date': today, 'count': 0, 'email_provided': False})

    if user_data['date'] != today:
        user_data = {'date': today, 'count': 0, 'email_provided': False}

    if request.method == "POST":
        user_data['count'] += 1

        if user_data['count'] > 4 and not user_data.get('email_provided'):
            user_limits[client_ip] = user_data
            return redirect("/signup")

        if user_data['count'] > 20:
            return "Daily limit reached. Try again tomorrow."

        file = request.files.get("file")
        target_format = request.form.get("format", "jpg").lower()
        valid_formats = ["jpg", "png", "webp", "pdf", "tiff"]

        if target_format not in valid_formats:
            return f"Unsupported format: {target_format}"

        target_format_pillow = {
            "jpg": "JPEG",
            "pdf": "PDF",
            "tiff": "TIFF"
        }.get(target_format, target_format.upper())

        if file:
            img = Image.open(file.stream).convert("RGB")
            filename = f"{uuid.uuid4()}.{target_format}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            img.save(filepath, format=target_format_pillow)
            user_limits[client_ip] = user_data
            return send_file(filepath, as_attachment=True)

    user_limits[client_ip] = user_data
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    client_ip = request.remote_addr
    if request.method == "POST":
        email = request.form.get("email")
        timestamp = datetime.now().isoformat()
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO emails (timestamp, ip, email) VALUES (%s, %s, %s)",
                    (timestamp, client_ip, email)
                )
                conn.commit()
        user_data = user_limits.get(client_ip, {'date': datetime.now().strftime('%Y-%m-%d'), 'count': 0})
        user_data['email_provided'] = True
        user_limits[client_ip] = user_data
        return redirect("/")
    return render_template("signup.html")

@app.route("/emails")
def emails():
    admin_key = request.args.get("admin")
    if admin_key != "Myboy-abc-jkl-13":
        return "Unauthorized", 403

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT timestamp, ip, email FROM emails ORDER BY id DESC")
            rows = cur.fetchall()

    output = "timestamp,ip,email\n" + "\n".join([",".join(row) for row in rows])
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=emails.csv"})
