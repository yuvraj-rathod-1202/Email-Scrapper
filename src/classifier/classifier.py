import json
import os
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "parsed_emails.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "classified_emails.json")


class EmailSchema(BaseModel):
    category: Optional[str]
    from_email: Optional[str]
    title: Optional[str]
    body: Optional[str]
    message_id: Optional[str]


def build_prompt(email: dict, category: str) -> str:
    return f"""
You are an email parser for IIT Gandhinagar's campus platform.

Email:
FROM: {email.get("FROM", "")}
TO: {email.get("TO", "")}
SUBJECT: {email.get("SUBJECT", "")}
BODY: {email.get("BODY", "")}

Fill the following fields:
- "category": use exactly this value → "{category}"
- "from_email": sender's email address
- "title": a clean concise title generated from the subject line
- "body": a 2-3 sentence summary of the email with all important details
- "message_id": use exactly this value → "{email.get("id", "")}"

If a field is not found, set it to null.
"""


def classify_email(email: dict, category: str) -> dict:
    prompt = build_prompt(email, category)

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EmailSchema
            )
        )
        return json.loads(response.text)

    except Exception as e:
        return {
            "category": category,
            "from_email": email.get("FROM", ""),
            "title": email.get("SUBJECT", ""),
            "body": None,
            "message_id": email.get("id", ""),
            "error": str(e)
        }


def run_classifier():
    if not os.path.exists(INPUT_FILE):
        return

    with open(INPUT_FILE, "r") as f:
        categorized = json.load(f)

    classified = []

    for category, emails in categorized.items():
        if not emails:
            continue
        for email in emails:
            result = classify_email(email, category)
            classified.append(result)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(classified, f, indent=2)

if __name__ == "__main__":
    run_classifier()