
from flask import Flask, request, render_template, redirect, url_for
import csv
import os
from datetime import datetime

app = Flask(__name__)

DATA_FILE = 'emails.csv'
ADMIN_KEY = 'Myboy-abc-jkl-13'  # Updated admin key

# Ensure the CSV file exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['email', 'ip', 'date'])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form.get('email')
        ip = request.remote_addr
        date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        if email:
            with open(DATA_FILE, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([email, ip, date])
        return redirect(url_for('index'))
    return '''
        <form method="post">
            Email: <input type="email" name="email" required>
            <input type="submit" value="Submit">
        </form>
    '''

@app.route('/emails')
def get_emails():
    if request.args.get('admin') != ADMIN_KEY:
        return 'Unauthorized', 403
    with open(DATA_FILE, newline='') as file:
        reader = csv.reader(file)
        rows = list(reader)
    return '<br>'.join([', '.join(row) for row in rows])

if __name__ == '__main__':
    app.run(debug=True)
