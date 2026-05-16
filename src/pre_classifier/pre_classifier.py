import json
import os
import re

ALLOWED_DOMAINS = ["iitgn.ac.in"]

SPAM_KEYWORDS = [
    "unsubscribe", "click here", "buy now", "limited offer",
    "congratulations you won", "free gift", "act now", "discount",
    "sale", "offer expires", "winner", "claim your", "100% free",
    "cash prize", "earn money", "work from home", "lottery"
]

PROMOTION_KEYWORDS = [
    "newsletter", "subscription", "promotional", "advertisement",
    "sponsored", "marketing", "deals", "coupon", "promo"
]


def is_allowed_sender(email_from: str) -> bool:
    if not email_from:
        return False
    match = re.search(r'[\w\.-]+@[\w\.-]+', email_from)
    if not match:
        return False
    domain = match.group(0).lower().split("@")[-1]
    return domain in ALLOWED_DOMAINS


def has_subject(subject: str) -> bool:
    return bool(subject and subject.strip())


def is_spam(subject: str, body: str) -> bool:
    text = (subject + " " + body).lower()
    return any(keyword in text for keyword in SPAM_KEYWORDS)


def is_promotion(subject: str, body: str) -> bool:
    text = (subject + " " + body).lower()
    return any(keyword in text for keyword in PROMOTION_KEYWORDS)


def filter_email(email: dict) -> bool:
    email_from = email.get("FROM", "")
    subject = email.get("SUBJECT", "")
    body = email.get("BODY", "")

    if not is_allowed_sender(email_from):
        return False
    if not has_subject(subject):
        return False
    if is_spam(subject, body):
        return False
    if is_promotion(subject, body):
        return False
    return True


def run_pre_classifier():
    if not os.path.exists("messages.json"):
        return

    with open("messages.json", "r") as f:
        emails = json.load(f)

    passed = [email for email in emails if filter_email(email)]

    with open("pre_classified.json", "w") as f:
        json.dump(passed, f, indent=2)


if __name__ == "__main__":
    run_pre_classifier()