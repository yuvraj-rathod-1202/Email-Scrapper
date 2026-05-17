import json
import os
import re
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "pre_classified.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "parsed_emails.json")


def remove_html(text: str) -> str:
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ")


def remove_urls(text: str) -> str:
    return re.sub(r'http\S+|www\S+', '', text)


def remove_extra_whitespace(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def remove_special_characters(text: str) -> str:
    return text.encode("ascii", "ignore").decode("ascii")


def clean_body(body: str) -> str:
    body = remove_html(body)
    body = remove_urls(body)
    body = remove_special_characters(body)
    body = remove_extra_whitespace(body)
    return body


def parse_email(email: dict) -> dict:
    return {
        "id": email.get("id", ""),
        "FROM": email.get("FROM", "").strip(),
        "TO": email.get("TO", "").strip(),
        "SUBJECT": email.get("SUBJECT", "").strip(),
        "BODY": clean_body(email.get("BODY", ""))
    }


def run_parser():
    if not os.path.exists(INPUT_FILE):
        return

    with open(INPUT_FILE, "r") as f:
        categorized = json.load(f)

    if not categorized:
        return
    
    parsed_categorized = {}
    for category, emails in categorized.items():
        parsed_categorized[category] = [parse_email(email) for email in emails]

    with open(OUTPUT_FILE, "w") as f:
        json.dump(parsed_categorized, f, indent=2)

if __name__ == "__main__":
    run_parser()