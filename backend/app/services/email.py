"""Transactional email delivery for account recovery."""
import logging
import smtplib
from email.message import EmailMessage
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_password_reset_email(recipient: str, token: str) -> None:
    settings = get_settings()
    if not all([settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_from_email]):
        raise RuntimeError("Password reset email is unavailable because SMTP is not configured")
    reset_url = f"{settings.frontend_origin.rstrip('/')}/reset-password?token={token}"
    message = EmailMessage()
    message["Subject"] = "Reset your AgriSense password"
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    message.set_content(
        f"A password reset was requested for your AgriSense account.\n\n"
        f"Open this link within 30 minutes to choose a new password:\n{reset_url}\n\n"
        "If you did not request this, you can safely ignore this email."
    )
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        logger.error("Password reset email delivery failed: %s", exc)
        raise RuntimeError("Password reset email could not be delivered") from exc
