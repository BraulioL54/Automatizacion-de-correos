from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EmailRecipient:
    row_number: int
    name: str
    email: str
    message: str
    subject: str
    attachment_path: Path | None


@dataclass(frozen=True)
class SendResult:
    email: str
    status: str


@dataclass(frozen=True)
class CampaignSummary:
    total: int
    sent: int
    failed: int


@dataclass(frozen=True)
class ValidationIssue:
    level: str
    message: str


@dataclass(frozen=True)
class PreflightResult:
    ready: bool
    recipient_count: int
    issues: list[ValidationIssue]
