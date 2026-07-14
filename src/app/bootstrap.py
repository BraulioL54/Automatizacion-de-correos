from config import load_settings
from services.logger_service import setup_logger
from ui.gui import launch_gui


def bootstrap_application() -> None:
    settings = load_settings()
    setup_logger(settings.log_file)
    launch_gui(settings)
