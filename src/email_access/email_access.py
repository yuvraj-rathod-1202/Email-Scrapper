import os.path
import json
import base64
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")


def get_credentials():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8000)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds


def scrape_emails(service):
    results = (
        service.users()
        .messages()
        .list(
            userId="me",
            labelIds=["INBOX", "UNREAD"],
            maxResults=10
        )
        .execute()
    )
    messages = results.get("messages", [])
    if not messages:
        return

    existing = []
    saved_ids = set()
    if os.path.exists("messages.json"):
        with open("messages.json", "r") as m:
            existing = json.load(m)
        saved_ids = {email["id"] for email in existing}

    dump = []
    for message in messages:

        if message["id"] in saved_ids:
            continue

        temp = {}
        temp.update({"id": message["id"]})

        full_message = (
            service.users()
            .messages()
            .get(userId="me", id=message["id"])
            .execute()
        )
        payload = full_message["payload"]
        headers = payload["headers"]

        if "parts" in payload:
            body = ""
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    data = part["body"].get("data")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode("utf-8")
                        break
        else:
            data = payload["body"].get("data")
            body = base64.urlsafe_b64decode(data).decode("utf-8") if data else ""

        message_folder = os.path.join("attachments", message["id"])
        os.makedirs(message_folder, exist_ok=True)
        if "parts" in payload:
            for part in payload["parts"]:
                filename = part.get("filename")
                part_body = part.get("body")
                if not filename:
                    continue
                att_id = part_body.get("attachmentId")
                if att_id:
                    attachment = (
                        service.users()
                        .messages()
                        .attachments()
                        .get(userId="me", messageId=message["id"], id=att_id)
                        .execute()
                    )
                    data = attachment.get("data")
                else:
                    data = part_body.get("data")
                if not data:
                    continue
                file_data = base64.urlsafe_b64decode(data)
                file_path = os.path.join(message_folder, filename)
                with open(file_path, "wb") as f:
                    f.write(file_data)

        temp.update({"BODY": body})
        for head in headers:
            if head.get("name") == "Delivered-To":
                temp.update({"TO": head.get("value")})
            elif head.get("name") == "From":
                temp.update({"FROM": head.get("value")})
            elif head.get("name") == "Subject":
                temp.update({"SUBJECT": head.get("value")})

        dump.append(temp)

    if dump:
        existing.extend(dump)
        with open("messages.json", "w") as m:
            json.dump(existing, m, indent=2)


def main():
    creds = get_credentials()

    try:
        service = build("gmail", "v1", credentials=creds)

        while True:
            scrape_emails(service)
            time.sleep(300)

    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()