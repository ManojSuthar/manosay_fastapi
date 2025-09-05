# routes/leads.py
from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel, EmailStr
from typing import Optional
from db import get_database
import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

router = APIRouter(prefix="/api", tags=["leads"])
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")

# Pydantic model for incoming lead


class LeadIn(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    platform: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    message: Optional[str] = None

# Helper: send notification email (runs in background)


async def _send_lead_email(lead: dict):
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587) or 587)
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", SMTP_USERNAME)

    if not SMTP_USERNAME or not SMTP_PASSWORD or not RECIPIENT_EMAIL:
        logger.info("SMTP not configured; skipping lead email send")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USERNAME
        msg["To"] = RECIPIENT_EMAIL
        msg["Subject"] = f"New Quote Request from {lead.get('name')}"

        body = (
            f"New lead received from ManoSay website:\n\n"
            f"Name: {lead.get('name')}\n"
            f"Email: {lead.get('email')}\n"
            f"Company: {lead.get('company')}\n"
            f"Platform: {lead.get('platform')}\n"
            f"Budget: {lead.get('budget')}\n"
            f"Timeline: {lead.get('timeline')}\n\n"
            f"Message:\n{lead.get('message')}\n\n"
            f"Received at: {lead.get('created_at')}\n"
        )
        msg.attach(MIMEText(body, "plain"))

        await aiosmtplib.send(
            msg,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD,
            start_tls=(SMTP_PORT == 587),
            timeout=30,
        )
        logger.info("Lead email sent to %s", RECIPIENT_EMAIL)
    except Exception as e:
        logger.exception("Failed to send lead email: %s", e)


@router.get("/request-quote", response_class=HTMLResponse)
async def get_request_quote(request: Request):
    return templates.TemplateResponse("request_quote.html", {"request": request})

# API endpoint to accept leads


@router.post("/request-quote")
async def request_quote(payload: LeadIn, background_tasks: BackgroundTasks, request: Request):
    db = get_database()
    leads = db["leads"]

    lead_doc = {
        "name": payload.name.strip(),
        "email": payload.email,
        "company": (payload.company or "").strip(),
        "platform": payload.platform or "",
        "budget": payload.budget or "",
        "timeline": payload.timeline or "",
        "message": (payload.message or "").strip(),
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "created_at": datetime.utcnow(),
        "status": "new"
    }

    # insert to MongoDB (Motor async)
    res = await leads.insert_one(lead_doc)
    lead_id = str(res.inserted_id)

    # schedule email notification (non-blocking)
    background_tasks.add_task(_send_lead_email, {**lead_doc, "id": lead_id})

    return JSONResponse(status_code=201, content={"success": True, "message": "Lead received", "lead_id": lead_id})
