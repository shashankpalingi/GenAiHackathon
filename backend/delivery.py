"""
Drishyamitra - Delivery Module
Handles automated photo sharing via Email (Gmail API) and WhatsApp.
Net-new module (no FileMind equivalent).
"""

import os
import base64
import mimetypes
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from config import (
    GMAIL_CREDENTIALS_FILE,
    GMAIL_TOKEN_FILE,
    GMAIL_SENDER,
    WHATSAPP_API_URL,
    WHATSAPP_API_TOKEN,
)


def send_email(recipient, subject, photo_paths, message_body=""):
    """
    Send photos via Gmail API.
    
    Args:
        recipient: Email address to send to
        subject: Email subject line
        photo_paths: List of photo file paths to attach
        message_body: Optional text message
    
    Returns:
        dict: {"status": "sent"|"failed", "error": str or None}
    """
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

        # Authenticate
        creds = None
        if os.path.exists(GMAIL_TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(GMAIL_CREDENTIALS_FILE):
                    return {"status": "failed", "error": "Gmail credentials file not found. Please configure OAuth."}
                flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(GMAIL_TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        service = build("gmail", "v1", credentials=creds)

        # Build email
        msg = MIMEMultipart()
        msg["to"] = recipient
        msg["from"] = GMAIL_SENDER or "me"
        msg["subject"] = subject or "Photos from Drishyamitra"

        # Text body
        body = message_body or "Here are your photos, shared via Drishyamitra AI Photo Manager."
        msg.attach(MIMEText(body, "plain"))

        # Attach photos
        for photo_path in photo_paths:
            if os.path.exists(photo_path):
                filename = os.path.basename(photo_path)
                mime_type = mimetypes.guess_type(photo_path)[0] or "image/jpeg"
                maintype, subtype = mime_type.split("/")

                with open(photo_path, "rb") as f:
                    img_data = f.read()

                image = MIMEImage(img_data, _subtype=subtype)
                image.add_header("Content-Disposition", "attachment", filename=filename)
                msg.attach(image)

        # Send
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        service.users().messages().send(
            userId="me",
            body={"raw": raw_message}
        ).execute()

        print(f"Delivery: Email sent to {recipient} with {len(photo_paths)} photo(s)")
        return {"status": "sent", "error": None}

    except Exception as e:
        print(f"Delivery: Email error: {e}")
        return {"status": "failed", "error": str(e)}


def send_whatsapp(recipient, photo_paths, message=""):
    """
    Send photos via WhatsApp Web API.
    
    Args:
        recipient: WhatsApp number or contact ID
        photo_paths: List of photo file paths to send
        message: Optional text message
    
    Returns:
        dict: {"status": "sent"|"failed", "error": str or None}
    """
    try:
        import requests

        if not WHATSAPP_API_URL or not WHATSAPP_API_TOKEN:
            return {"status": "failed", "error": "WhatsApp API not configured."}

        headers = {
            "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json"
        }

        # Send text message first
        if message:
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {"body": message or "Photos from Drishyamitra"}
            }
            requests.post(WHATSAPP_API_URL, json=payload, headers=headers)

        # Send each photo
        for photo_path in photo_paths:
            if not os.path.exists(photo_path):
                continue

            # Upload media first
            upload_url = WHATSAPP_API_URL.replace("/messages", "/media")
            with open(photo_path, "rb") as f:
                mime_type = mimetypes.guess_type(photo_path)[0] or "image/jpeg"
                files = {"file": (os.path.basename(photo_path), f, mime_type)}
                upload_headers = {"Authorization": f"Bearer {WHATSAPP_API_TOKEN}"}
                upload_resp = requests.post(upload_url, files=files, headers=upload_headers)

                if upload_resp.status_code == 200:
                    media_id = upload_resp.json().get("id")
                    # Send media message
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": recipient,
                        "type": "image",
                        "image": {"id": media_id}
                    }
                    requests.post(WHATSAPP_API_URL, json=payload, headers=headers)

        print(f"Delivery: WhatsApp message sent to {recipient} with {len(photo_paths)} photo(s)")
        return {"status": "sent", "error": None}

    except Exception as e:
        print(f"Delivery: WhatsApp error: {e}")
        return {"status": "failed", "error": str(e)}


def log_delivery(db_session, user_id, method, recipient, photo_ids, status="sent", error_msg=None):
    """
    Log a delivery record to the database.
    
    Args:
        db_session: SQLAlchemy session
        user_id: User ID
        method: "email" or "whatsapp"
        recipient: Recipient address
        photo_ids: List of photo IDs sent
        status: "sent", "pending", or "failed"
        error_msg: Error message if failed
    """
    try:
        from models import DeliveryHistory

        record = DeliveryHistory(
            user_id=user_id,
            method=method,
            recipient=recipient,
            photo_ids=photo_ids,
            status=status,
            error_message=error_msg,
            timestamp=datetime.utcnow()
        )
        db_session.add(record)
        db_session.commit()
        print(f"Delivery: Logged {method} delivery to {recipient} (status={status})")

    except Exception as e:
        print(f"Delivery: Logging error: {e}")
        db_session.rollback()
