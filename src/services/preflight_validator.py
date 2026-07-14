from config import Settings
from domain.models import PreflightResult, ValidationIssue
from domain.validators import (
    validate_credentials,
    validate_email,
    validate_output_directory,
    validate_required_files,
)
from services.attachment_resolver import AttachmentResolver
from services.excel_reader import ExcelReader


class PreflightValidator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.excel_reader = ExcelReader()
        self.attachment_resolver = AttachmentResolver()

    def validate(self) -> PreflightResult:
        issues: list[ValidationIssue] = []
        recipients_count = 0

        try:
            validate_required_files(self.settings)
            issues.append(ValidationIssue(level="info", message="Archivos principales encontrados correctamente."))
        except (FileNotFoundError, ValueError) as error:
            issues.append(ValidationIssue(level="error", message=str(error)))
            return PreflightResult(ready=False, recipient_count=0, issues=issues)

        try:
            validate_credentials(self.settings)
            issues.append(ValidationIssue(level="info", message="Credenciales detectadas en el archivo .env."))
        except ValueError as error:
            issues.append(ValidationIssue(level="error", message=str(error)))

        try:
            validate_output_directory(self.settings.outputs_dir)
            issues.append(
                ValidationIssue(
                    level="info",
                    message=f"Carpeta de salida lista para usarse: {self.settings.outputs_dir}.",
                )
            )
        except Exception as error:
            issues.append(ValidationIssue(level="error", message=f"No se pudo preparar la carpeta de salida: {error}"))

        try:
            recipients = self.excel_reader.load_recipients(self.settings.excel_file)
            recipients_count = len(recipients)
            issues.append(
                ValidationIssue(
                    level="info",
                    message=f"Excel cargado correctamente. Destinatarios detectados: {recipients_count}.",
                )
            )
        except Exception as error:
            issues.append(ValidationIssue(level="error", message=f"No se pudo leer el Excel: {error}"))
            return PreflightResult(ready=False, recipient_count=0, issues=issues)

        if recipients_count == 0:
            issues.append(ValidationIssue(level="warning", message="El Excel no contiene destinatarios para procesar."))

        for recipient in recipients:
            try:
                validate_email(recipient.email)
            except ValueError as error:
                issues.append(
                    ValidationIssue(
                        level="error",
                        message=f"Fila {recipient.row_number}: correo invalido ({recipient.email}). {error}",
                    )
                )

            if recipient.attachment_path:
                resolved_attachment = self.attachment_resolver.resolve(
                    recipient.attachment_path,
                    self.settings.default_attachment,
                    self.settings.base_dir,
                )
                if resolved_attachment is None:
                    issues.append(
                        ValidationIssue(
                            level="error",
                            message=(
                                f"Fila {recipient.row_number}: no se encontro el adjunto "
                                f"'{recipient.attachment_path}' ni existe un adjunto por defecto."
                            ),
                        )
                    )

        default_attachment_exists = self.settings.default_attachment.exists()
        if default_attachment_exists:
            issues.append(
                ValidationIssue(
                    level="info",
                    message=f"Adjunto por defecto disponible: {self.settings.default_attachment.name}.",
                )
            )
        else:
            issues.append(
                ValidationIssue(
                    level="warning",
                    message=(
                        "No se encontro adjunto por defecto. Solo se enviaran archivos cuando el Excel "
                        "incluya una ruta valida por destinatario."
                    ),
                )
            )

        has_errors = any(issue.level == "error" for issue in issues)
        ready = not has_errors and recipients_count > 0

        if ready:
            issues.append(
                ValidationIssue(
                    level="info",
                    message="Validacion completada. El sistema esta listo para enviar correos.",
                )
            )
        else:
            issues.append(
                ValidationIssue(
                    level="warning",
                    message="Validacion completada con observaciones. Corrige los errores antes de enviar.",
                )
            )

        return PreflightResult(ready=ready, recipient_count=recipients_count, issues=issues)
