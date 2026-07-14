from pathlib import Path


class AttachmentResolver:
    def resolve(self, recipient_attachment: Path | None, default_attachment: Path, base_dir: Path) -> Path | None:
        if recipient_attachment:
            candidate = recipient_attachment
            if not candidate.is_absolute():
                candidate = base_dir / candidate
            if candidate.exists():
                return candidate

        if default_attachment.exists():
            return default_attachment

        return None
