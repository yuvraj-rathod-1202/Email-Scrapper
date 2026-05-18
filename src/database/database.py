import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "classified_emails.json")

load_dotenv(os.path.join(BASE_DIR, ".env"))

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "insIIT")

if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]


def get_collection(category: str):
    return db[category]


def insert_email(email: dict) -> bool:
    category = email.get("category")
    if not category:
        return False

    collection = get_collection(category)

    existing = collection.find_one({"message_id": email.get("message_id")})
    if existing:
        return False

    collection.insert_one(email)
    return True


def get_all(category: str) -> list:
    return list(get_collection(category).find({}, {"_id": 0}))


def get_by_from(category: str, from_email: str) -> list:
    return list(get_collection(category).find({"from_email": from_email}, {"_id": 0}))


def delete_by_message_id(category: str, message_id: str) -> bool:
    result = get_collection(category).delete_one({"message_id": message_id})
    return result.deleted_count > 0


def run_database():
    if not os.path.exists(INPUT_FILE):
        return

    with open(INPUT_FILE, "r") as f:
        emails = json.load(f)

    if not emails:
        return

    for email in emails:
        insert_email(email)


if __name__ == "__main__":
    run_database()