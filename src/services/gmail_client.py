import logging
import smtplib

from config import Settings
from domain.validators import validate_credentials


class GmailClient:
    def create_connection(self, settings: Settings) -> smtplib.SMTP:
        validate_credentials(settings)

        server = smtplib.SMTP(settings.smtp_server, settings.smtp_port)
        server.starttls()
        server.login(settings.sender_email, settings.sender_password)
        return server

    def send_message(self, server: smtplib.SMTP, sender_email: str, recipient_email: str, raw_message: str) -> None:
        server.sendmail(sender_email, recipient_email, raw_message)
        logging.info("Correo enviado a %s", recipient_email)
