# email_service.py
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.recipient_email = settings.RECIPIENT_EMAIL

    async def send_contact_email(self, name: str, email: str, subject: str, message: str) -> bool:
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = self.recipient_email
            msg['Subject'] = f"New Contact Form: {subject}"

            body = (
                f"New contact form submission from Manosay website:\n\n"
                f"Name: {name}\n"
                f"Email: {email}\n"
                f"Subject: {subject}\n\n"
                f"Message:\n{message}\n\n"
                f"---\nThis email was sent from the Manosay contact form."
            )
            msg.attach(MIMEText(body, "plain"))

            # Use STARTTLS for port 587
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_server,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                start_tls=(self.smtp_port == 587),
                use_tls=(self.smtp_port == 465),
                timeout=30
            )

            return True

        except Exception as e:
            logger.exception("Error sending email")
            raise
