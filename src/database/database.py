import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "classified_emails.json")

# ✅ load .env FIRST before anything else
load_dotenv(os.path.join(BASE_DIR, ".env"))

# ✅ verify it's being read
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "insIIT")

if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env")

print(f"Connecting to: {MONGO_URI[:30]}...")  # print first 30 chars to verify

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]


def get_collection(category: str):
    return db[category]


def insert_email(email: dict) -> bool:
    category = email.get("category")
    if not category:
        print(f"No category found — skipping")
        return False

    collection = get_collection(category)

    existing = collection.find_one({"message_id": email.get("message_id")})
    if existing:
        print(f"Duplicate skipped: {email.get('title')}")
        return False

    collection.insert_one(email)
    print(f"Inserted [{category}]: {email.get('title')}")
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
        print("classified_emails.json not found.")
        return

    with open(INPUT_FILE, "r") as f:
        emails = json.load(f)

    if not emails:
        print("No emails to insert.")
        return

    inserted = 0
    skipped = 0

    for email in emails:
        success = insert_email(email)
        if success:
            inserted += 1
        else:
            skipped += 1

    print(f"\n✅ Inserted: {inserted} | ⏭️ Skipped: {skipped}")


if __name__ == "__main__":
    run_database()