import os
import json

def load_json(file, default):
    if not os.path.exists(file):
        return default
    if os.path.getsize(file) == 0:
        return default
    with open(file, 'r') as f:
        return json.load(f)

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)
