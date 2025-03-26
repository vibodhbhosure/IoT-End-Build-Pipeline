import json
import os

DB_FILE = "compiled_firmwares.json"

def load_firmware_db():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_firmware_entry(entry):
    db = load_firmware_db()
    db.append(entry)
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def get_firmware_options():
    db = load_firmware_db()
    return sorted([
        (f"{entry['label']} → {entry['hash']} ({entry['board']}, {entry['date']})", entry["hex_path"])
        for entry in db
    ])