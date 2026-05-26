import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "classified_emails.json")

load_dotenv(os.path.join(BASE_DIR, ".env"))

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB", "insIIT")]


def insert_lost_found(email: dict) -> int:
    collection = db["lost&found"]
    items = email.get("items", [])
    inserted = 0

    for item in items:
        existing = collection.find_one({
            "message_id": item.get("message_id"),
            "item": item.get("item")
        })
        if existing:
            continue
        collection.insert_one(item)
        inserted += 1

    return inserted


def insert_medical(email: dict) -> int:
    inserted = 0

    unavail_col = db["medical_unavailability"]
    for entry in email.get("unavailability", []):
        entry["message_id"] = email.get("message_id")
        entry["from_email"] = email.get("from_email")
        existing = unavail_col.find_one({
            "message_id": email.get("message_id"),
            "doctor_name": entry.get("doctor_name"),
            "unavailable_date": entry.get("unavailable_date"),
            "unavailable_start_time": entry.get("unavailable_start_time")
        })
        if existing:
            continue
        unavail_col.insert_one(entry)
        inserted += 1

    timings_col = db["medical_timings"]
    for entry in email.get("updated_timings", []):
        entry["message_id"] = email.get("message_id")
        entry["from_email"] = email.get("from_email")
        existing = timings_col.find_one({
            "message_id": email.get("message_id"),
            "doctor_name": entry.get("doctor_name"),
            "date": entry.get("date"),
            "updated_start_time": entry.get("updated_start_time")
        })
        if existing:
            continue
        timings_col.insert_one(entry)
        inserted += 1

    return inserted


def insert_default(email: dict) -> int:
    category = email.get("category")
    if not category:
        return 0

    collection = db[category]
    existing = collection.find_one({"message_id": email.get("message_id")})
    if existing:
        return 0

    collection.insert_one(email)
    return 1


def run_database():
    if not os.path.exists(INPUT_FILE):
        return

    with open(INPUT_FILE, "r") as f:
        emails = json.load(f)

    if not emails:
        return

    inserted = 0
    for email in emails:
        category = email.get("category")
        if category == "lost&found":
            inserted += insert_lost_found(email)
        elif category == "medical":
            inserted += insert_medical(email)
        else:
            inserted += insert_default(email)

if __name__ == "__main__":
    run_database()