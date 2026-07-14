from pathlib import Path


class TemplateRenderer:
    def load_template(self, template_file: Path) -> str:
        return template_file.read_text(encoding="utf-8")

    def build_html_body(self, template: str, recipient_name: str, message: str) -> str:
        formatted_message = message.replace("\n", "<br>")
        return template.format(nombre=recipient_name, mensaje=formatted_message)

    def build_plain_text_body(self, recipient_name: str, message: str) -> str:
        return f"Hola {recipient_name},\n\n{message}\n\nSaludos."
