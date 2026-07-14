from pathlib import Path
import re

from config import Settings


REQUIRED_COLUMNS = {"correo", "nombre", "mensaje"}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_required_files(settings: Settings) -> None:
    missing_files: list[str] = []

    if not settings.excel_file.exists():
        missing_files.append(str(settings.excel_file))

    if not settings.html_template.exists():
        missing_files.append(str(settings.html_template))

    if missing_files:
        missing_text = "\n".join(missing_files)
        raise FileNotFoundError(f"Faltan archivos requeridos:\n{missing_text}")


def validate_credentials(settings: Settings) -> None:
    if not settings.sender_email or not settings.sender_password:
        raise ValueError(
            "Faltan credenciales. Revisa CORREO_PROPIO_DE_PRUEVA y CONTRASENA_GOOGLE_PROPIA en el archivo .env."
        )


def validate_email(email: str) -> None:
    if not EMAIL_PATTERN.match(email):
        raise ValueError("Correo invalido")


def validate_attachment_path(path: Path | None) -> None:
    if path and not path.exists():
        raise FileNotFoundError(f"No existe el adjunto indicado: {path}")


def validate_output_directory(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if not output_dir.is_dir():
        raise NotADirectoryError(f"La ruta de salida no es una carpeta valida: {output_dir}")
