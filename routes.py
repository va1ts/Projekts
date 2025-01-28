from flask import render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from config import users, fan_assignments
from data_fetch import fetch_room_data
from gpio_control import activate_fan, deactivate_fan

@app.route('/')
def home():
    return redirect(url_for('login'))  # Redirect to the login page initially

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        
        # Store the user in the in-memory database
        users[username] = hashed_password
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and check_password_hash(users[username], password):
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials, please try again.")
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    room_data = fetch_room_data()

    # Sort rooms alphabetically by their name
    room_data.sort(key=lambda room: room['roomGroupName'])

    # Remove rooms that already have a fan assigned
    available_rooms = [room for room in room_data if not any(fan['room'] == room['roomGroupName'] for fan in fan_assignments)]

    # Add fan functionality
    if request.method == 'POST':
        room_name = request.form['room']
        
        # Check if the room already has a fan assigned
        if any(fan['room'] == room_name for fan in fan_assignments):
            message = "Fan is already assigned to this room."
            return render_template('dashboard.html', rooms=room_data, fan_assignments=fan_assignments, message=message)

        # Add fan with default OFF status
        fan_assignments.append({'room': room_name, 'status': 'OFF'})

        # Recheck CO2 levels and update fan status immediately after adding the fan
        for fan in fan_assignments:
            for room in room_data:
                if room["roomGroupName"] == fan['room']:
                    # CO2 level check to update fan status
                    if room.get("co2", 0) > 1000:
                        fan['status'] = 'ON'
                        activate_fan()
                    else:
                        fan['status'] = 'OFF'
                        deactivate_fan()

        return render_template('dashboard.html', rooms=room_data, fan_assignments=fan_assignments)

    # Check CO2 levels and update fan statuses based on the latest CO2 data
    for fan in fan_assignments:
        for room in room_data:
            if room["roomGroupName"] == fan['room']:
                # CO2 level check to update fan status
                if room.get("co2", 0) > 1000:
                    fan['status'] = 'ON'
                    activate_fan()
                else:
                    fan['status'] = 'OFF'
                    deactivate_fan()

    return render_template('dashboard.html', rooms=available_rooms, fan_assignments=fan_assignments, message=None)
