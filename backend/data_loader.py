import json
import os

def get_users_data():
    file_path = os.path.join(os.path.dirname(__file__), 'users_data.json')
    with open(file_path, 'r') as f:
        return json.load(f)
    
users_data = get_users_data()