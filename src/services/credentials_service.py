from pathlib import Path

from dotenv import dotenv_values, set_key


class CredentialsService:
    def __init__(self, env_file: Path) -> None:
        self.env_file = env_file

    def load_credentials(self) -> tuple[str, str]:
        values = dotenv_values(self.env_file)
        email = str(values.get("CORREO_PROPIO_DE_PRUEVA", "") or "")
        password = str(
            values.get("CONTRASENA_GOOGLE_PROPIA", "")
            or values.get("CONTRASEÑA_GOOGLE_PROPIA", "")
            or ""
        )
        return email, password

    def save_credentials(self, email: str, password: str) -> None:
        self.env_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.env_file.exists():
            self.env_file.touch()

        set_key(str(self.env_file), "CORREO_PROPIO_DE_PRUEVA", email)
        set_key(str(self.env_file), "CONTRASENA_GOOGLE_PROPIA", password)
