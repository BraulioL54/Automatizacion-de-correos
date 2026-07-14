from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from domain.models import EmailRecipient


class EmailBuilder:
    def build_message(
        self,
        sender_email: str,
        recipient: EmailRecipient,
        plain_text_body: str,
        html_body: str,
        attachment_path: Path | None,
    ) -> MIMEMultipart:
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient.email
        message["Subject"] = recipient.subject

        message.attach(MIMEText(plain_text_body, "plain", "utf-8"))
        message.attach(MIMEText(html_body, "html", "utf-8"))

        if attachment_path:
            with attachment_path.open("rb") as attachment_file:
                attachment_part = MIMEBase("application", "octet-stream")
                attachment_part.set_payload(attachment_file.read())
                encoders.encode_base64(attachment_part)
                attachment_part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{attachment_path.name}"',
                )
                message.attach(attachment_part)

        return message
