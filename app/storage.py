import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "safelink_data.json"

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def default_data():
    return {
        "users": [
            {"id": 1, "email": "user@example.com", "password": "User@123", "role": "user"},
            {"id": 2, "email": "admin@rescue.local", "password": "Admin@123", "role": "community"}
        ],
        "families": [
            {"id": 1, "family_id": "FAM-1001", "family_name": "Demo Family"}
        ],
        "members": [
            {
                "id": 1, "family_id": "FAM-1001", "name": "Arun Kumar",
                "age": 28, "gender": "Male", "phone": "9876543210",
                "relation": "Son", "address": "Madurai"
            },
            {
                "id": 2, "family_id": "FAM-1001", "name": "Priya Kumar",
                "age": 24, "gender": "Female", "phone": "9876543211",
                "relation": "Daughter", "address": "Madurai"
            },
            {
                "id": 3, "family_id": "FAM-1001", "name": "Ravi Kumar",
                "age": 55, "gender": "Male", "phone": "9876543212",
                "relation": "Father", "address": "Madurai"
            }
        ],
        "teams": [
            {"id": 1, "team_name": "Team A"},
            {"id": 2, "team_name": "Team B"},
            {"id": 3, "team_name": "Team C"},
            {"id": 4, "team_name": "Team D"}
        ],
        "rescued_people": [],
        "movement_history": [],
        "volunteers": []
    }

def initialize_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        save_data(default_data())

def load_data():
    initialize_data()
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp = DATA_FILE.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    temp.replace(DATA_FILE)

def next_id(items):
    return max([int(x.get("id", 0)) for x in items] + [0]) + 1

def find_by_id(items, item_id):
    for item in items:
        if str(item.get("id")) == str(item_id):
            return item
    return None
