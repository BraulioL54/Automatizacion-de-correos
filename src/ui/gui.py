from pathlib import Path
import threading
import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, messagebox, scrolledtext, ttk

from config import Settings, build_runtime_settings, create_run_label, load_settings
from domain.models import CampaignSummary, PreflightResult
from services.campaign_service import CampaignService
from services.credentials_service import CredentialsService
from services.preflight_validator import PreflightValidator
from ui.notifier import BaseNotifier


class GuiNotifier(BaseNotifier):
    def __init__(self, app: "EmailSenderGUI") -> None:
        self.app = app

    def show_startup(self, settings: Settings, recipient_count: int) -> None:
        self.app.prepare_progress(recipient_count)
        self.app.append_log("Preparando envio...")
        self.app.append_log(f"Excel cargado: {settings.excel_file.name}")
        self.app.append_log(f"Plantilla cargada: {settings.html_template.name}")
        self.app.append_log(f"Carpeta de salida: {settings.outputs_dir}")
        self.app.append_log(f"Log de esta ejecucion: {settings.log_file.name}")
        self.app.append_log(f"Reporte de esta ejecucion: {settings.report_file.name}")
        self.app.append_log(f"Destinatarios detectados: {recipient_count}")

    def show_progress(
        self,
        processed: int,
        total: int,
        sent: int,
        failed: int,
        current_recipient: str,
    ) -> None:
        self.app.update_progress(processed, total, sent, failed, current_recipient)

    def show_success(self, message: str) -> None:
        self.app.append_log(message)

    def show_error(self, message: str) -> None:
        self.app.append_log(message)

    def show_summary(self, summary: CampaignSummary, report_file: Path) -> None:
        self.app.append_log("")
        self.app.append_log("Proceso finalizado.")
        self.app.append_log(f"Total procesados: {summary.total}")
        self.app.append_log(f"Enviados: {summary.sent}")
        self.app.append_log(f"Con error: {summary.failed}")
        self.app.append_log(f"Reporte generado: {report_file}")
        self.app.finish_run(summary)


class EmailSenderGUI:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.credentials_service = CredentialsService(settings.env_file)
        self.selected_excel_path = settings.excel_file
        self.selected_template_path = settings.html_template
        self.selected_output_dir = settings.outputs_dir
        self.current_run_label: str | None = None
        self.campaign_service = CampaignService(self._build_effective_settings())
        self.preflight_validator = PreflightValidator(self._build_effective_settings())
        self.root = tk.Tk()
        self.root.title("Automatizacion de Correos")
        self.root.geometry("760x520")
        self.root.minsize(680, 480)

        self.status_var = tk.StringVar(value="Valida los datos antes de iniciar el envio.")
        self.excel_path_var = tk.StringVar(value=str(self.selected_excel_path))
        self.template_path_var = tk.StringVar(value=str(self.selected_template_path))
        self.output_dir_var = tk.StringVar(value=str(self.selected_output_dir))
        self.report_file_var = tk.StringVar(value="Se generara al enviar")
        self.log_file_var = tk.StringVar(value="Se generara al enviar")
        self.gmail_email_var = tk.StringVar(value="")
        self.gmail_password_var = tk.StringVar(value="")
        self.progress_status_var = tk.StringVar(value="Progreso: 0%")
        self.progress_detail_var = tk.StringVar(value="0 de 0 procesados | 0 enviados | 0 errores")
        self.progress_value = tk.DoubleVar(value=0)
        self.show_password = False
        self.last_preflight_result: PreflightResult | None = None
        self.validation_button: ttk.Button
        self.send_button: ttk.Button
        self.progress_bar: ttk.Progressbar
        self.password_entry: ttk.Entry
        self.log_area: scrolledtext.ScrolledText

        self._build_layout()
        self._load_credentials_into_form()

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=20)
        container.pack(fill="both", expand=True)

        header = ttk.Label(
            container,
            text="Automatizacion de correos",
            font=("Segoe UI", 20, "bold"),
        )
        header.pack(anchor="w")

        subtitle = ttk.Label(
            container,
            text="Primer paso de la interfaz grafica: ejecutar envios y ver el estado desde una sola ventana.",
            wraplength=680,
        )
        subtitle.pack(anchor="w", pady=(6, 18))

        credentials_frame = ttk.LabelFrame(container, text="Credenciales de Gmail", padding=12)
        credentials_frame.pack(fill="x", pady=(0, 12))

        self._add_credential_row(
            credentials_frame,
            "Correo",
            self.gmail_email_var,
        )
        self._add_password_row(credentials_frame)

        credentials_actions = ttk.Frame(credentials_frame)
        credentials_actions.pack(fill="x", pady=(10, 0))

        ttk.Button(
            credentials_actions,
            text="Guardar credenciales",
            command=self.save_credentials,
        ).pack(side="left")

        info_frame = ttk.LabelFrame(container, text="Archivos del proceso", padding=12)
        info_frame.pack(fill="x")

        self._add_file_selector_row(
            info_frame,
            "Excel",
            self.excel_path_var,
            self.browse_excel_file,
            "Examinar Excel",
        )
        self._add_file_selector_row(
            info_frame,
            "Plantilla",
            self.template_path_var,
            self.browse_template_file,
            "Examinar HTML",
        )
        self._add_file_selector_row(
            info_frame,
            "Salida",
            self.output_dir_var,
            self.browse_output_directory,
            "Examinar carpeta",
        )
        self._add_dynamic_info_row(info_frame, "Reporte", self.report_file_var)
        self._add_dynamic_info_row(info_frame, "Log", self.log_file_var)

        actions_frame = ttk.Frame(container)
        actions_frame.pack(fill="x", pady=(16, 12))

        self.validation_button = ttk.Button(
            actions_frame,
            text="Validar datos",
            command=self.start_preflight_validation,
        )
        self.validation_button.pack(side="left")

        self.send_button = ttk.Button(
            actions_frame,
            text="Enviar correos",
            command=self.start_sending,
            state="disabled",
        )
        self.send_button.pack(side="left", padx=(10, 0))

        status_label = ttk.Label(
            actions_frame,
            textvariable=self.status_var,
        )
        status_label.pack(side="left", padx=(14, 0))

        progress_frame = ttk.LabelFrame(container, text="Progreso del envio", padding=12)
        progress_frame.pack(fill="x", pady=(0, 12))

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            mode="determinate",
            maximum=100,
            variable=self.progress_value,
        )
        self.progress_bar.pack(fill="x")

        ttk.Label(progress_frame, textvariable=self.progress_status_var).pack(anchor="w", pady=(8, 2))
        ttk.Label(progress_frame, textvariable=self.progress_detail_var).pack(anchor="w")

        log_frame = ttk.LabelFrame(container, text="Bitacora", padding=12)
        log_frame.pack(fill="both", expand=True)

        self.log_area = scrolledtext.ScrolledText(log_frame, wrap="word", height=16, state="disabled")
        self.log_area.pack(fill="both", expand=True)

        self.append_log("Interfaz lista. Primero presiona 'Validar datos'.")

    def _add_info_row(self, parent: ttk.LabelFrame, label: str, value: str) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)

        ttk.Label(row, text=f"{label}:", width=10).pack(side="left")
        ttk.Label(row, text=value).pack(side="left")

    def _add_credential_row(self, parent: ttk.LabelFrame, label: str, text_var: tk.StringVar) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)

        ttk.Label(row, text=f"{label}:", width=18).pack(side="left")
        ttk.Entry(row, textvariable=text_var).pack(side="left", fill="x", expand=True)

    def _add_password_row(self, parent: ttk.LabelFrame) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)

        ttk.Label(row, text="Contraseña app:", width=18).pack(side="left")
        self.password_entry = ttk.Entry(row, textvariable=self.gmail_password_var, show="*")
        self.password_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(row, text="Mostrar", command=self.toggle_password_visibility).pack(side="left")

    def _add_dynamic_info_row(self, parent: ttk.LabelFrame, label: str, text_var: tk.StringVar) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)

        ttk.Label(row, text=f"{label}:", width=10).pack(side="left")
        ttk.Label(row, textvariable=text_var).pack(side="left")

    def _add_file_selector_row(
        self,
        parent: ttk.LabelFrame,
        label: str,
        path_var: tk.StringVar,
        command: Callable[[], None],
        button_text: str,
    ) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)

        ttk.Label(row, text=f"{label}:", width=10).pack(side="left")

        entry = ttk.Entry(row, textvariable=path_var)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ttk.Button(row, text=button_text, command=command).pack(side="left")

    def _build_effective_settings(self) -> Settings:
        return build_runtime_settings(
            self.settings,
            excel_file=self.selected_excel_path,
            html_template=self.selected_template_path,
            outputs_dir=self.selected_output_dir,
            run_label=self.current_run_label,
        )

    def _refresh_runtime_services(self) -> None:
        effective_settings = self._build_effective_settings()
        self.campaign_service = CampaignService(effective_settings)
        self.preflight_validator = PreflightValidator(effective_settings)
        self.report_file_var.set(str(effective_settings.report_file))
        self.log_file_var.set(str(effective_settings.log_file))

    def _load_credentials_into_form(self) -> None:
        email, password = self.credentials_service.load_credentials()
        self.gmail_email_var.set(email)
        self.gmail_password_var.set(password)

    def _reload_settings_from_env(self) -> None:
        current_excel_path = self.selected_excel_path
        current_template_path = self.selected_template_path
        current_output_dir = self.selected_output_dir

        refreshed_settings = load_settings()
        self.settings = refreshed_settings
        self.credentials_service = CredentialsService(refreshed_settings.env_file)
        self.selected_excel_path = current_excel_path
        self.selected_template_path = current_template_path
        self.selected_output_dir = current_output_dir
        self._refresh_runtime_services()

    def toggle_password_visibility(self) -> None:
        self.show_password = not self.show_password
        self.password_entry.configure(show="" if self.show_password else "*")

    def save_credentials(self) -> None:
        email = self.gmail_email_var.get().strip()
        password = self.gmail_password_var.get().strip()

        if not email or not password:
            messagebox.showwarning(
                "Credenciales incompletas",
                "Debes capturar el correo de Gmail y la contraseña de aplicacion.",
            )
            return

        self.credentials_service.save_credentials(email, password)
        self._reload_settings_from_env()
        self._invalidate_preflight_state()
        self.append_log("Credenciales de Gmail guardadas correctamente en el archivo .env.")
        messagebox.showinfo(
            "Credenciales guardadas",
            "Las credenciales se guardaron correctamente. Vuelve a validar antes de enviar.",
        )

    def _invalidate_preflight_state(self) -> None:
        self.current_run_label = None
        self._refresh_runtime_services()
        self.last_preflight_result = None
        self.send_button.configure(state="disabled")
        self.status_var.set("Se detectaron cambios en los archivos. Vuelve a validar.")
        self.reset_progress()

    def browse_excel_file(self) -> None:
        selected_file = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")],
            initialdir=str(self.selected_excel_path.parent),
        )
        if not selected_file:
            return

        self.selected_excel_path = Path(selected_file)
        self.excel_path_var.set(str(self.selected_excel_path))
        self._refresh_runtime_services()
        self._invalidate_preflight_state()
        self.append_log(f"Nuevo archivo Excel seleccionado: {self.selected_excel_path}")

    def browse_template_file(self) -> None:
        selected_file = filedialog.askopenfilename(
            title="Seleccionar plantilla HTML",
            filetypes=[("Archivos HTML", "*.html;*.htm"), ("Todos los archivos", "*.*")],
            initialdir=str(self.selected_template_path.parent),
        )
        if not selected_file:
            return

        self.selected_template_path = Path(selected_file)
        self.template_path_var.set(str(self.selected_template_path))
        self._refresh_runtime_services()
        self._invalidate_preflight_state()
        self.append_log(f"Nueva plantilla seleccionada: {self.selected_template_path}")

    def browse_output_directory(self) -> None:
        selected_directory = filedialog.askdirectory(
            title="Seleccionar carpeta de salida",
            initialdir=str(self.selected_output_dir),
        )
        if not selected_directory:
            return

        self.selected_output_dir = Path(selected_directory)
        self.output_dir_var.set(str(self.selected_output_dir))
        self._invalidate_preflight_state()
        self.append_log(f"Nueva carpeta de salida seleccionada: {self.selected_output_dir}")

    def append_log(self, message: str) -> None:
        self.root.after(0, self._append_log_sync, message)

    def _append_log_sync(self, message: str) -> None:
        self.log_area.configure(state="normal")
        self.log_area.insert("end", f"{message}\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def reset_progress(self) -> None:
        self.progress_value.set(0)
        self.progress_status_var.set("Progreso: 0%")
        self.progress_detail_var.set("0 de 0 procesados | 0 enviados | 0 errores")

    def prepare_progress(self, total: int) -> None:
        self.root.after(0, self._prepare_progress_sync, total)

    def _prepare_progress_sync(self, total: int) -> None:
        self.progress_value.set(0)
        self.progress_status_var.set("Progreso: 0%")
        self.progress_detail_var.set(f"0 de {total} procesados | 0 enviados | 0 errores")

    def update_progress(
        self,
        processed: int,
        total: int,
        sent: int,
        failed: int,
        current_recipient: str,
    ) -> None:
        self.root.after(0, self._update_progress_sync, processed, total, sent, failed, current_recipient)

    def _update_progress_sync(
        self,
        processed: int,
        total: int,
        sent: int,
        failed: int,
        current_recipient: str,
    ) -> None:
        percentage = 0 if total == 0 else (processed / total) * 100
        self.progress_value.set(percentage)
        self.progress_status_var.set(f"Progreso: {percentage:.0f}%")
        self.progress_detail_var.set(
            f"{processed} de {total} procesados | {sent} enviados | {failed} errores | Actual: {current_recipient}"
        )

    def start_sending(self) -> None:
        if not self.last_preflight_result or not self.last_preflight_result.ready:
            messagebox.showwarning(
                "Validacion requerida",
                "Debes ejecutar una validacion correcta antes de enviar correos.",
            )
            return

        self.current_run_label = create_run_label()
        self._refresh_runtime_services()
        self.validation_button.configure(state="disabled")
        self.send_button.configure(state="disabled")
        self.status_var.set("Enviando correos...")
        self.reset_progress()
        self.append_log("")
        self.append_log("Inicio de ejecucion solicitado por el usuario.")

        worker = threading.Thread(target=self._run_campaign, daemon=True)
        worker.start()

    def _run_campaign(self) -> None:
        notifier = GuiNotifier(self)
        summary = self.campaign_service.run(notifier=notifier)
        if summary is None:
            self.root.after(0, self._reset_after_failure)

    def start_preflight_validation(self) -> None:
        self.current_run_label = None
        self._refresh_runtime_services()
        self.validation_button.configure(state="disabled")
        self.send_button.configure(state="disabled")
        self.status_var.set("Validando configuracion y datos...")
        self.append_log("")
        self.append_log("Iniciando validacion previa...")

        worker = threading.Thread(target=self._run_preflight_validation, daemon=True)
        worker.start()

    def _run_preflight_validation(self) -> None:
        result = self.preflight_validator.validate()
        self.root.after(0, self._finish_preflight_validation, result)

    def _finish_preflight_validation(self, result: PreflightResult) -> None:
        self.last_preflight_result = result

        for issue in result.issues:
            prefix = {
                "info": "[OK]",
                "warning": "[ADVERTENCIA]",
                "error": "[ERROR]",
            }.get(issue.level, "[INFO]")
            self.append_log(f"{prefix} {issue.message}")

        self.validation_button.configure(state="normal")

        if result.ready:
            self.send_button.configure(state="normal")
            self.status_var.set(f"Sistema listo. Destinatarios validados: {result.recipient_count}")
            messagebox.showinfo(
                "Validacion correcta",
                (
                    "La validacion previa finalizo correctamente.\n\n"
                    f"Destinatarios listos: {result.recipient_count}"
                ),
            )
            return

        self.send_button.configure(state="disabled")
        self.status_var.set("Corrige los errores detectados antes de enviar.")
        messagebox.showwarning(
            "Validacion incompleta",
            "Se encontraron errores o advertencias importantes. Revisa la bitacora antes de continuar.",
        )

    def _reset_after_failure(self) -> None:
        self.status_var.set("Se detecto un error antes del envio.")
        self.validation_button.configure(state="normal")
        if self.last_preflight_result and self.last_preflight_result.ready:
            self.send_button.configure(state="normal")
        else:
            self.send_button.configure(state="disabled")
        messagebox.showerror("Error", "No se pudo iniciar el proceso. Revisa la bitacora.")

    def finish_run(self, summary: CampaignSummary) -> None:
        self.root.after(0, self._finish_run_sync, summary)

    def _finish_run_sync(self, summary: CampaignSummary) -> None:
        self.validation_button.configure(state="normal")
        self.send_button.configure(state="normal")
        self.progress_value.set(100)
        self.progress_status_var.set("Progreso: 100%")
        self.progress_detail_var.set(
            f"{summary.total} de {summary.total} procesados | {summary.sent} enviados | {summary.failed} errores"
        )
        self.status_var.set(
            f"Finalizado. Enviados: {summary.sent} | Errores: {summary.failed}"
        )
        messagebox.showinfo(
            "Proceso finalizado",
            (
                f"Total procesados: {summary.total}\n"
                f"Enviados: {summary.sent}\n"
                f"Con error: {summary.failed}\n\n"
                f"Reporte: {self.campaign_service.settings.report_file}"
            ),
        )

    def run(self) -> None:
        self.root.mainloop()


def launch_gui(settings: Settings) -> None:
    app = EmailSenderGUI(settings)
    app.run()
