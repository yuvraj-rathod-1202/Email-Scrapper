import json
import os
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR,".env"))

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash"

INPUT_FILE = os.path.join(BASE_DIR, "parsed_emails.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "classified_emails.json")


class LostItem(BaseModel):
    item: Optional[str]
    description: Optional[str]
    location_found: Optional[str]
    contact: Optional[str]
    message_id: Optional[str]
    from_email: Optional[str]

class LostFoundSchema(BaseModel):
    category: Optional[str]
    items: list[LostItem]


class MedicalUnavailability(BaseModel):
    doctor_name: Optional[str]
    unavailable_date: Optional[str]
    unavailable_start_time: Optional[str]
    unavailable_end_time: Optional[str]

class MedicalUpdatedTiming(BaseModel):
    doctor_name: Optional[str]
    date: Optional[str]
    updated_start_time: Optional[str]
    updated_end_time: Optional[str]

class MedicalSchema(BaseModel):
    category: Optional[str]
    message_id: Optional[str]
    from_email: Optional[str]
    unavailability: list[MedicalUnavailability]
    updated_timings: list[MedicalUpdatedTiming]


class DefaultSchema(BaseModel):
    category: Optional[str]
    from_email: Optional[str]
    title: Optional[str]
    body: Optional[str]
    message_id: Optional[str]


def build_lost_found_prompt(email: dict) -> str:
    return f"""
You are an email parser for IIT Gandhinagar's campus platform.

Email:
FROM: {email.get("FROM", "")}
TO: {email.get("TO", "")}
SUBJECT: {email.get("SUBJECT", "")}
BODY: {email.get("BODY", "")}

Extract all lost/found items from this email.
For each item mentioned, create a separate entry in the "items" list with:
- "item": name of the lost/found item
- "description": brief description of the item
- "location_found": where it was found or where to collect it
- "contact": contact person or email to reach
- "message_id": use exactly → "{email.get("id", "")}"
- "from_email": sender's email address

Set "category" to exactly → "lost&found"
If a field is not found, set it to null.
"""


def build_medical_prompt(email: dict) -> str:
    return f"""
You are an email parser for IIT Gandhinagar's campus platform.

Email:
FROM: {email.get("FROM", "")}
TO: {email.get("TO", "")}
SUBJECT: {email.get("SUBJECT", "")}
BODY: {email.get("BODY", "")}

Extract medical schedule information from this email.

For "unavailability": list each doctor who is NOT available with:
- "doctor_name": name of the doctor
- "unavailable_date": date they are unavailable
- "unavailable_start_time": start time of unavailability
- "unavailable_end_time": end time of unavailability

For "updated_timings": list each doctor whose timings have changed with:
- "doctor_name": name of the doctor
- "date": date of updated timing
- "updated_start_time": new start time
- "updated_end_time": new end time

Set "category" to exactly → "medical"
Set "message_id" to exactly → "{email.get("id", "")}"
Set "from_email" to sender's email address.
If a field is not found, set it to null.
"""


def build_default_prompt(email: dict, category: str) -> str:
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
    try:
        if category == "lost&found":
            response = client.models.generate_content(
                model=MODEL,
                contents=build_lost_found_prompt(email),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=LostFoundSchema
                )
            )
        elif category == "medical":
            response = client.models.generate_content(
                model=MODEL,
                contents=build_medical_prompt(email),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=MedicalSchema
                )
            )
        else:
            response = client.models.generate_content(
                model=MODEL,
                contents=build_default_prompt(email, category),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=DefaultSchema
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