"""
SubmissionAttempt model - audit log for invoice submission attempts.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.invoice import Invoice


class SubmissionOutcome(str, enum.Enum):
    """Outcome of a submission attempt."""

    SUCCESS = "success"
    VALIDATION_ERROR = "validation_error"
    AUTH_ERROR = "auth_error"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


class SubmissionAttempt(Base):
    """
    Audit log for invoice submission attempts.
    
    Records metadata about each attempt to submit an invoice to FBR.
    This is append-only and used for audit reporting.
    """

    __tablename__ = "submission_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Invoice relationship
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Attempt tracking
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sequential attempt number for this invoice",
    )
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # Request details
    endpoint: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="FBR endpoint URL used",
    )
    
    # Response details
    http_status: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="HTTP status code (null if timeout/network error)",
    )
    outcome: Mapped[SubmissionOutcome] = mapped_column(
        Enum(SubmissionOutcome),
        nullable=False,
    )
    
    # Diagnostic information
    diagnostic_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Unique ID for support reference",
    )
    response_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="Sanitized response summary (no sensitive data)",
    )
    response_time_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Response time in milliseconds",
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(back_populates="attempts")

    def __repr__(self) -> str:
        return f"<SubmissionAttempt(invoice_id={self.invoice_id}, attempt={self.attempt_number}, outcome={self.outcome.value})>"
