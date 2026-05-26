import time
import sys
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.email_access.email_access import get_credentials, scrape_emails
from src.pre_classifier.pre_classifier import run_pre_classifier
from src.parser.parser import run_parser
from src.classifier.classifier import run_classifier
from src.database.database import run_database

EMAIL_ACCESS_DIR  = os.path.join(ROOT_DIR, "src", "email_access")
PRE_CLASSIFIER_DIR = os.path.join(ROOT_DIR, "src", "pre_classifier")
PARSER_DIR        = os.path.join(ROOT_DIR, "src", "parser")
CLASSIFIER_DIR    = os.path.join(ROOT_DIR, "src", "classifier")
DATABASE_DIR      = os.path.join(ROOT_DIR, "src", "database")

MESSAGES_FILE        = os.path.join(EMAIL_ACCESS_DIR,   "messages.json")
PRE_CLASSIFIED_FILE  = os.path.join(PRE_CLASSIFIER_DIR, "pre_classified.json")  
PARSED_FILE          = os.path.join(PARSER_DIR,         "parsed_emails.json")
CLASSIFIED_FILE      = os.path.join(CLASSIFIER_DIR,     "classified_emails.json")


def copy_file(src: str, dst: str):
    import shutil
    if os.path.exists(src):
        shutil.copy2(src, dst)


def run_pipeline():
    try:
        creds = get_credentials()
        service = build("gmail", "v1", credentials=creds)
        scrape_emails(service)
        copy_file(
            MESSAGES_FILE,
            os.path.join(PRE_CLASSIFIER_DIR, "messages.json")
        )
        run_pre_classifier()
        copy_file(
            PRE_CLASSIFIED_FILE,
            os.path.join(PARSER_DIR, "pre_classified.json")
        )
        run_parser()

        copy_file(
            PARSED_FILE,
            os.path.join(CLASSIFIER_DIR, "parsed_emails.json")
        )
        run_classifier()

        copy_file(
            CLASSIFIED_FILE,
            os.path.join(DATABASE_DIR, "classified_emails.json")
        )
        run_database()

    except HttpError as e:
        print(f"\n Gmail API error: {e}")
    except Exception as e:
        import traceback
        traceback.print_exc()


if __name__ == "__main__":

    while True:
        run_pipeline()
        time.sleep(300)