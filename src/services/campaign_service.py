import logging
import random
import smtplib
import time

from config import Settings
from domain.models import CampaignSummary, SendResult
from domain.validators import validate_email, validate_required_files
from services.attachment_resolver import AttachmentResolver
from services.email_builder import EmailBuilder
from services.excel_reader import ExcelReader
from services.gmail_client import GmailClient
from services.logger_service import setup_logger
from services.report_generator import ReportGenerator
from services.template_renderer import TemplateRenderer
from ui.cli import ConsoleNotifier
from ui.notifier import BaseNotifier


class CampaignService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.excel_reader = ExcelReader()
        self.template_renderer = TemplateRenderer()
        self.attachment_resolver = AttachmentResolver()
        self.email_builder = EmailBuilder()
        self.gmail_client = GmailClient()
        self.report_generator = ReportGenerator()

    def run(self, notifier: BaseNotifier | None = None) -> CampaignSummary | None:
        notifier = notifier or ConsoleNotifier()
        results: list[SendResult] = []
        sent_count = 0
        failed_count = 0
        setup_logger(self.settings.log_file)

        try:
            validate_required_files(self.settings)
            recipients = self.excel_reader.load_recipients(self.settings.excel_file)
            template = self.template_renderer.load_template(self.settings.html_template)
        except (FileNotFoundError, ValueError) as error:
            notifier.show_error(str(error))
            return None

        total_recipients = len(recipients)
        notifier.show_startup(self.settings, len(recipients))

        try:
            with self.gmail_client.create_connection(self.settings) as server:
                for recipient in recipients:
                    try:
                        validate_email(recipient.email)

                        html_body = self.template_renderer.build_html_body(
                            template,
                            recipient.name,
                            recipient.message,
                        )
                        plain_text_body = self.template_renderer.build_plain_text_body(
                            recipient.name,
                            recipient.message,
                        )
                        attachment_path = self.attachment_resolver.resolve(
                            recipient.attachment_path,
                            self.settings.default_attachment,
                            self.settings.base_dir,
                        )
                        message = self.email_builder.build_message(
                            sender_email=self.settings.sender_email,
                            recipient=recipient,
                            plain_text_body=plain_text_body,
                            html_body=html_body,
                            attachment_path=attachment_path,
                        )

                        self.gmail_client.send_message(
                            server,
                            self.settings.sender_email,
                            recipient.email,
                            message.as_string(),
                        )
                        notifier.show_success(f"[{recipient.row_number}] Enviado a {recipient.name}")
                        results.append(SendResult(email=recipient.email, status="Enviado"))
                        sent_count += 1
                        notifier.show_progress(
                            processed=len(results),
                            total=total_recipients,
                            sent=sent_count,
                            failed=failed_count,
                            current_recipient=recipient.email,
                        )

                        time.sleep(
                            random.uniform(
                                self.settings.delay_min_seconds,
                                self.settings.delay_max_seconds,
                            )
                        )
                    except Exception as error:
                        logging.error("Error con %s: %s", recipient.email, error)
                        notifier.show_error(f"Error con {recipient.email}: {error}")
                        results.append(SendResult(email=recipient.email, status=f"Error: {error}"))
                        failed_count += 1
                        notifier.show_progress(
                            processed=len(results),
                            total=total_recipients,
                            sent=sent_count,
                            failed=failed_count,
                            current_recipient=recipient.email,
                        )
        except smtplib.SMTPAuthenticationError:
            notifier.show_error("Error de autenticacion. Revisa el correo y la contrasena configurados.")
        except Exception as error:
            notifier.show_error(f"Error de conexion: {error}")

        self.report_generator.save(results, self.settings.report_file)
        summary = self._build_summary(results)
        notifier.show_summary(summary, self.settings.report_file)
        return summary

    def _build_summary(self, results: list[SendResult]) -> CampaignSummary:
        sent = sum(1 for result in results if result.status == "Enviado")
        failed = len(results) - sent
        return CampaignSummary(total=len(results), sent=sent, failed=failed)
