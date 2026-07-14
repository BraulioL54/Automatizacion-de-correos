from pathlib import Path
from typing import Protocol

from config import Settings
from domain.models import CampaignSummary


class BaseNotifier(Protocol):
    def show_startup(self, settings: Settings, recipient_count: int) -> None:
        ...

    def show_progress(
        self,
        processed: int,
        total: int,
        sent: int,
        failed: int,
        current_recipient: str,
    ) -> None:
        ...

    def show_success(self, message: str) -> None:
        ...

    def show_error(self, message: str) -> None:
        ...

    def show_summary(self, summary: CampaignSummary, report_file: Path) -> None:
        ...
