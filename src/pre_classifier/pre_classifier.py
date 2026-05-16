import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "messages.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "pre_classified.json")

SENDER_CATEGORIES = {
    "bvpuvar@iitgn.ac.in": "lost&found",
    "acad.exp@iitgn.ac.in": "acadexp",
    "medical@iitgn.ac.in": "medical",
    "welfare.secretary@iitgn.ac.in": "Welfcounc",
    "technical.secretary@iitgn.ac.in": "Techcounc",
    "cds@iitgn.ac.in": "CDS",
    "sports.secretary@iitgn.ac.in": "sportscounc",
    "pdc.secretary@iitgn.ac.in": "PDC",
}

SUBJECT_CATEGORIES = {
    "mess_menu": ["mess menu"]
}


def extract_email(email_from: str) -> str:
    match = re.search(r'[\w\.-]+@[\w\.-]+', email_from)
    return match.group(0).lower() if match else ""


def get_category_from_sender(email_from: str) -> str | None:
    email_address = extract_email(email_from)
    return SENDER_CATEGORIES.get(email_address)


def get_category_from_subject(subject: str) -> str | None:
    subject_lower = subject.lower()
    for category, keywords in SUBJECT_CATEGORIES.items():
        if any(keyword.lower() in subject_lower for keyword in keywords):
            return category
    return None


def run_pre_classifier():
    if not os.path.exists(INPUT_FILE):
        return

    with open(INPUT_FILE, "r") as f:
        emails = json.load(f)

    if not emails:
        return

    all_categories = set(SENDER_CATEGORIES.values()) | set(SUBJECT_CATEGORIES.keys())
    categorized = {category: [] for category in all_categories}

    dropped = 0
    for email in emails:
        category = get_category_from_sender(email.get("FROM", ""))

        if category is None:
            category = get_category_from_subject(email.get("SUBJECT", ""))

        if category is None:
            dropped += 1
            continue

        categorized[category].append(email)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(categorized, f, indent=2)

if __name__ == "__main__":
    run_pre_classifier()