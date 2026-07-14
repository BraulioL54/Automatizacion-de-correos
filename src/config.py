from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    env_file: Path
    data_dir: Path
    assets_dir: Path
    outputs_dir: Path
    pdfs_dir: Path
    excel_file: Path
    html_template: Path
    default_attachment: Path
    report_file: Path
    log_file: Path
    smtp_server: str
    smtp_port: int
    sender_email: str
    sender_password: str
    delay_min_seconds: float
    delay_max_seconds: float


def load_settings() -> Settings:
    base_dir = Path(__file__).resolve().parent
    env_file = base_dir.parent / ".env"
    load_dotenv(dotenv_path=env_file, override=True)
    data_dir = base_dir / "data"
    assets_dir = base_dir / "assets"
    outputs_dir = base_dir / "outputs"
    pdfs_dir = base_dir / "pdfs"

    sender_password = os.getenv("CONTRASENA_GOOGLE_PROPIA") or os.getenv("CONTRASEÑA_GOOGLE_PROPIA", "")

    return Settings(
        base_dir=base_dir,
        env_file=env_file,
        data_dir=data_dir,
        assets_dir=assets_dir,
        outputs_dir=outputs_dir,
        pdfs_dir=pdfs_dir,
        excel_file=data_dir / "clientes.xlsx",
        html_template=assets_dir / "plantilla.html",
        default_attachment=pdfs_dir / "archivo.pdf",
        report_file=outputs_dir / "reporte_envios.xlsx",
        log_file=outputs_dir / "envio_correos.log",
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        sender_email=os.getenv("CORREO_PROPIO_DE_PRUEVA", ""),
        sender_password=sender_password,
        delay_min_seconds=1.0,
        delay_max_seconds=3.0,
    )


def create_run_label() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def build_runtime_settings(
    settings: Settings,
    excel_file: Path | None = None,
    html_template: Path | None = None,
    outputs_dir: Path | None = None,
    run_label: str | None = None,
) -> Settings:
    target_outputs_dir = outputs_dir or settings.outputs_dir
    timestamp = run_label or create_run_label()

    return replace(
        settings,
        excel_file=excel_file or settings.excel_file,
        html_template=html_template or settings.html_template,
        outputs_dir=target_outputs_dir,
        report_file=target_outputs_dir / f"reporte_envios_{timestamp}.xlsx",
        log_file=target_outputs_dir / f"envio_correos_{timestamp}.log",
    )
