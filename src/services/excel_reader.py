from pathlib import Path

import pandas as pd

from domain.models import EmailRecipient
from domain.validators import REQUIRED_COLUMNS


class ExcelReader:
    def load_recipients(self, excel_file: Path) -> list[EmailRecipient]:
        data_frame = pd.read_excel(excel_file)
        missing_columns = REQUIRED_COLUMNS.difference(data_frame.columns)

        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"Faltan columnas obligatorias en el Excel: {missing}")

        recipients: list[EmailRecipient] = []

        for index, row in data_frame.iterrows():
            name = str(row["nombre"]).strip()
            email = str(row["correo"]).strip()
            message = str(row["mensaje"]).strip()
            subject_value = row.get("asunto", f"Hola {name}")
            subject = str(subject_value).strip() if pd.notna(subject_value) else f"Hola {name}"

            attachment_path = None
            attachment_value = row.get("archivo")
            if pd.notna(attachment_value):
                attachment_text = str(attachment_value).strip()
                if attachment_text:
                    attachment_path = Path(attachment_text)

            recipients.append(
                EmailRecipient(
                    row_number=index + 1,
                    name=name,
                    email=email,
                    message=message,
                    subject=subject,
                    attachment_path=attachment_path,
                )
            )

        return recipients
