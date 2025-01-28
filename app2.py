from flask import Flask
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

from routes import *

if __name__ == '__main__':
    from werkzeug.security import generate_password_hash
    users['admin'] = generate_password_hash('123', method='sha256')
    app.run(debug=True, host='0.0.0.0', port=5001)
