import json
import requests
from gpiozero import OutputDevice
from gpiozero.pins.mock import MockFactory
from gpiozero import Device
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

# Initialize database connection
def get_db_connection():
    conn = sqlite3.connect('testing.db')
    conn.row_factory = sqlite3.Row
    return conn

# Function to add a user
def add_user(username, password, email):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO users (username, password, email)
        VALUES (?, ?, ?)
        """, (username, password, email))
        conn.commit()
        conn.close()
        print(f"User {username} added successfully.")
    except Exception as e:
        print(f"Error adding user: {e}")

# Create the users table if it doesn't exist
def create_users_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        conn.close()
        print("Users table created successfully.")
    except Exception as e:
        print(f"Error creating users table: {e}")

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Use MockFactory for development purposes
Device.pin_factory = MockFactory()

@app.route('/')
def home():
    return redirect(url_for('login'))

fan = OutputDevice(18)

fan_assignments = []

def fetch_room_data(building_id="512"):
    url = "https://co2.mesh.lv/api/device/list"
    payload = {
        "buildingId": building_id,
        "captchaToken": None
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    }

    response = requests.post(url, json=payload, headers=headers)
    print(f"Response Status Code: {response.status_code}")

    if response.status_code == 200:
        try:
            return response.json()
        except ValueError as e:
            print(f"JSON decoding error: {e}")
            return []
    else:
        print(f"Request failed with status code {response.status_code}")
        return []

def activate_fan():
    fan.on()
    print("Fan activated.")

def deactivate_fan():
    fan.off()
    print("Fan deactivated.")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            hashed_password = generate_password_hash(password, method='sha256')
            add_user(username, hashed_password, email)
            return redirect(url_for('login'))
        except KeyError as e:
            return f"Missing form data: {e}", 400
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials, please try again."
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    room_data = fetch_room_data()
    room_data.sort(key=lambda room: room['roomGroupName'])
    available_rooms = [room for room in room_data if not any(fan['room'] == room['roomGroupName'] for fan in fan_assignments)]

    if request.method == 'POST':
        room_name = request.form.get('room')
        if not room_name:
            message = "Room selection is required."
            return render_template('dashboard.html', rooms=room_data, fan_assignments=fan_assignments, message=message)
        if any(fan['room'] == room_name for fan in fan_assignments):
            message = "Fan is already assigned to this room."
            return render_template('dashboard.html', rooms=room_data, fan_assignments=fan_assignments, message=message)

        fan_assignments.append({'room': room_name, 'status': 'OFF', 'manual': False})

    for fan in fan_assignments:
        for room in room_data:
            if room["roomGroupName"] == fan['room']:
                if 'manual' in fan and fan['manual']:
                    continue  # Skip manual overrides
                if room.get("co2", 0) > 1000:
                    fan['status'] = 'ON'
                    fan['co2_alert'] = True
                    activate_fan()
                else:
                    fan['status'] = 'OFF'
                    fan['co2_alert'] = False
                    deactivate_fan()

    return render_template('dashboard.html', rooms=available_rooms, fan_assignments=fan_assignments, message=None)

@app.route('/control_fan', methods=['POST'])
def control_fan():
    if 'user' not in session:
        return redirect(url_for('login'))

    room_name = request.form.get('room')
    new_status = request.form.get('status')

    if not room_name or not new_status:
        return "Room and status are required.", 400

    for fan in fan_assignments:
        if fan['room'] == room_name:
            fan['status'] = new_status.upper()
            fan['manual'] = True

        if new_status.upper() == 'ON':
            activate_fan()
        elif new_status.upper() == 'OFF':
            deactivate_fan()

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    create_users_table()
    app.run(debug=True, host='0.0.0.0', port=5001)