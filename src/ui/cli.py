from pathlib import Path

from config import Settings
from domain.models import CampaignSummary
from ui.notifier import BaseNotifier


class ConsoleNotifier(BaseNotifier):
    def show_startup(self, settings: Settings, recipient_count: int) -> None:
        print("Iniciando automatizacion de correos...")
        print(f"Excel: {settings.excel_file}")
        print(f"Plantilla: {settings.html_template}")
        print(f"Destinatarios detectados: {recipient_count}")

    def show_progress(
        self,
        processed: int,
        total: int,
        sent: int,
        failed: int,
        current_recipient: str,
    ) -> None:
        print(
            f"Progreso: {processed}/{total} | Enviados: {sent} | Errores: {failed} | Actual: {current_recipient}"
        )

    def show_success(self, message: str) -> None:
        print(message)

    def show_error(self, message: str) -> None:
        print(message)

    def show_summary(self, summary: CampaignSummary, report_file: Path) -> None:
        print("")
        print("Proceso finalizado.")
        print(f"Total procesados: {summary.total}")
        print(f"Enviados: {summary.sent}")
        print(f"Con error: {summary.failed}")
        print(f"Reporte generado: {report_file}")
