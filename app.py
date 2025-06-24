from flask import Flask, render_template, request, send_file, redirect
from PIL import Image
import os
import uuid
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Simple in-memory counter to simulate user limits (reset daily)
user_limits = {}

@app.route("/", methods=["GET", "POST"])
def index():
    client_ip = request.remote_addr
    today = datetime.now().strftime('%Y-%m-%d')
    user_data = user_limits.get(client_ip, {'date': today, 'count': 0, 'email_required': False})

    if user_data['date'] != today:
        user_data = {'date': today, 'count': 0, 'email_required': False}

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

        if target_format == "jpg":
            target_format_pillow = "JPEG"
        elif target_format == "pdf":
            target_format_pillow = "PDF"
        elif target_format == "tiff":
            target_format_pillow = "TIFF"
        else:
            target_format_pillow = target_format.upper()

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
        user_data = user_limits.get(client_ip, {'date': datetime.now().strftime('%Y-%m-%d'), 'count': 0})
        user_data['email_provided'] = True
        user_limits[client_ip] = user_data
        return redirect("/")
    return render_template("signup.html")