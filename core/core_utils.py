"""
Utility functions for the application
"""

import os
import secrets
from typing import Optional
from fastapi import UploadFile, HTTPException
from pathlib import Path
import shutil
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from core.config import settings, UPLOAD_DIRS

async def save_uploaded_file(file: UploadFile, subdirectory: str) -> str:
    """
    Save uploaded file to disk and return the URL path
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Validate file type
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
        )
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    random_filename = secrets.token_urlsafe(16) + file_ext
    
    # Ensure upload directory exists
    upload_dir = UPLOAD_DIRS.get(subdirectory, settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, random_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return URL path
    return f"/static/uploads/{subdirectory}/{random_filename}"

async def delete_file(file_url: str) -> bool:
    """
    Delete file from disk
    """
    if not file_url:
        return False
    
    try:
        # Convert URL to file path
        if file_url.startswith("/static/uploads/"):
            file_path = file_url[1:]  # Remove leading slash
            file_path = os.path.join(settings.UPLOAD_DIR, *file_url.split("/")[3:])
        else:
            file_path = file_url
        
        # Delete file
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception:
        pass
    
    return False

def create_upload_dirs():
    """Create all upload directories if they don't exist"""
    for dir_path in UPLOAD_DIRS.values():
        os.makedirs(dir_path, exist_ok=True)
    
    # Also create the base upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

async def send_sms_via_twilio(to_phone: str, message: str) -> bool:
    """
    Send SMS via Twilio
    """
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
        # Twilio not configured
        print(f"Twilio not configured. Would send SMS to {to_phone}: {message}")
        return False
    
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        
        return True
        
    except TwilioRestException as e:
        print(f"Twilio error: {e}")
        return False
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False

def format_currency(amount: float) -> str:
    """Format currency amount"""
    return f"₹{amount:.2f}"

def format_datetime(dt) -> str:
    """Format datetime object"""
    if not dt:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_date(date_obj) -> str:
    """Format date object"""
    if not date_obj:
        return ""
    return date_obj.strftime("%Y-%m-%d")