import os

# GPIO Setup
FAN_PIN = 18

# Flask configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')

# Example user database (in-memory, for simplicity)
users = {}

# Change fan_assignments to be a list instead of a dictionary
fan_assignments = []
