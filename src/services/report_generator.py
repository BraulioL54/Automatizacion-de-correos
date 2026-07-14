from pathlib import Path

import pandas as pd

from domain.models import SendResult


class ReportGenerator:
    def save(self, results: list[SendResult], report_file: Path) -> None:
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_data = [{"correo": result.email, "estado": result.status} for result in results]
        pd.DataFrame(report_data).to_excel(report_file, index=False)
