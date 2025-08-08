"""Custom exceptions for verification domain (lightweight, no external deps)."""
from __future__ import annotations


class VerificationError(Exception):
    """Generic verification process error."""


class ValidationError(VerificationError):
    """Raised when metadata/session structure is invalid."""
