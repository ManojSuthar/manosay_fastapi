import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # SMTP Configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

    # App Configuration
    APP_NAME = "Manosay Contact API"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"


settings = Settings()
