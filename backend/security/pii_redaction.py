"""
PII Detection and Redaction Module

Provides field-level PII detection and redaction at ingestion to prevent
sensitive data from being stored in the database.

Thesis Claim: Privacy-by-Design with local redaction/hashing of sensitive fields
"""

import re
import hashlib
import os
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class PIIType(Enum):
    """Types of PII that can be detected."""
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    EMAIL = "email"
    PHONE = "phone"
    PASSWORD = "password"
    API_KEY = "api_key"
    IP_ADDRESS = "ip_address"
    MAC_ADDRESS = "mac_address"
    DATE_OF_BIRTH = "dob"
    ACCOUNT_NUMBER = "account_number"
    CUSTOM = "custom"


@dataclass
class PIIDetectionResult:
    """Result of PII detection in a field."""
    pii_type: PIIType
    field_name: str
    original_value: str
    redacted_value: str
    confidence: float  # 0.0 - 1.0


class PIIDetector:
    """
    Detects PII patterns in text fields using regex patterns.
    """

    # Regex patterns for PII detection
    PATTERNS = {
        PIIType.SSN: [
            r'\b\d{3}-\d{2}-\d{4}\b',
            r'\b\d{9}\b',  # SSN without dashes
        ],
        PIIType.CREDIT_CARD: [
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            r'\b\d{13,19}\b',  # Card number range
        ],
        PIIType.EMAIL: [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        ],
        PIIType.PHONE: [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',
            r'\b\+1\d{10}\b',
        ],
        PIIType.PASSWORD: [
            r'password["\s:=]+\S+',
            r'passwd["\s:=]+\S+',
            r'pwd["\s:=]+\S+',
        ],
        PIIType.API_KEY: [
            r'api[_-]?key["\s:=]+["\']?[\w-]{20,}["\']?',
            r'token["\s:=]+["\']?[\w-]{20,}["\']?',
            r'bearer[\s]+[\w.-]+',
        ],
        PIIType.IP_ADDRESS: [
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',  # IPv6
        ],
        PIIType.MAC_ADDRESS: [
            r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b',
        ],
        PIIType.ACCOUNT_NUMBER: [
            r'\b\d{8,17}\b',  # Generic account number
        ],
    }

    # Fields that should be checked for PII
    DEFAULT_CHECK_FIELDS = [
        "description",
        "details",
        "content",
        "message",
        "user_input",
        "clipboard_content",
        "url",
        "command",
    ]

    def __init__(self, check_fields: Optional[List[str]] = None):
        self.check_fields = check_fields or self.DEFAULT_CHECK_FIELDS
        self.compiled_patterns: Dict[PIIType, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        for pii_type, patterns in self.PATTERNS.items():
            self.compiled_patterns[pii_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def detect(self, field_name: str, value: str) -> List[PIIDetectionResult]:
        """
        Detect PII in a field value.

        Args:
            field_name: Name of the field
            value: Value to check

        Returns:
            List of detected PII items
        """
        if not value or not isinstance(value, str):
            return []

        results = []

        # Skip if field is not in check list
        field_lower = field_name.lower()
        should_check = any(
            field_lower == f.lower() or field_lower.endswith(f.lower())
            for f in self.check_fields
        )

        if not should_check:
            # Still check for password/API key patterns in any field
            if "password" in field_lower or "key" in field_lower or "token" in field_lower:
                should_check = True

        if not should_check:
            return results

        # Check each PII type
        for pii_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(value)
                for match in matches:
                    redacted = self._redact_value(pii_type, match)
                    results.append(PIIDetectionResult(
                        pii_type=pii_type,
                        field_name=field_name,
                        original_value=match,
                        redacted_value=redacted,
                        confidence=0.95
                    ))

        return results

    def _redact_value(self, pii_type: PIIType, value: str) -> str:
        """Redact a specific PII value based on its type."""
        if pii_type == PIIType.SSN:
            # Keep last 4: XXX-XX-1234
            if len(value) >= 4:
                return "*" * (len(value) - 4) + value[-4:]
            return "*" * len(value)

        elif pii_type == PIIType.CREDIT_CARD:
            # Keep last 4: ****-****-****-1234
            if len(value) >= 4:
                return "*" * (len(value) - 4) + value[-4:]
            return "*" * len(value)

        elif pii_type == PIIType.EMAIL:
            # Partial email: a***@example.com
            parts = value.split("@")
            if len(parts) == 2:
                name = parts[0]
                domain = parts[1]
                if len(name) > 1:
                    return f"{name[0]}***@{domain}"
            return "***@***"

        elif pii_type == PIIType.PHONE:
            # Keep last 4: ***-***-1234
            digits = re.sub(r'\D', '', value)
            if len(digits) >= 4:
                return f"***-***-{digits[-4:]}"
            return "***-***-****"

        elif pii_type in [PIIType.PASSWORD, PIIType.API_KEY]:
            # Completely redact passwords and keys
            return "[REDACTED]"

        elif pii_type == PIIType.IP_ADDRESS:
            # Partial IP: 192.168.*.*
            parts = value.split(".")
            if len(parts) >= 4:
                return f"{parts[0]}.{parts[1]}.*.*"
            return "*.*.*.*"

        elif pii_type == PIIType.MAC_ADDRESS:
            # Partial MAC: 00:11:**:**:**:**
            parts = value.replace("-", ":").split(":")
            if len(parts) >= 6:
                return f"{parts[0]}:{parts[1]}:**:**:**:**"
            return "**:**:**:**:**:**"

        else:
            # Default: hash the value
            return f"[HASH:{self._hash_value(value)[:8]}]"

    def _hash_value(self, value: str) -> str:
        """Create SHA-256 hash of value."""
        return hashlib.sha256(value.encode()).hexdigest()


class PIIRedactor:
    """
    Redacts PII from data structures before storage.
    """

    def __init__(self, detector: Optional[PIIDetector] = None):
        self.detector = detector or PIIDetector()

    def redact(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[PIIDetectionResult]]:
        """
        Redact PII from a data dictionary.

        Args:
            data: Input data dictionary

        Returns:
            Tuple of (redacted_data, detection_results)
        """
        redacted = {}
        all_results = []

        for field_name, value in data.items():
            if isinstance(value, str):
                # Detect PII
                detections = self.detector.detect(field_name, value)

                if detections:
                    # Redact the value
                    redacted_value = value
                    for detection in detections:
                        redacted_value = redacted_value.replace(
                            detection.original_value,
                            detection.redacted_value
                        )
                    redacted[field_name] = redacted_value
                    all_results.extend(detections)
                else:
                    redacted[field_name] = value

            elif isinstance(value, dict):
                # Recursively process nested dicts
                redacted_nested, nested_results = self.redact(value)
                redacted[field_name] = redacted_nested
                all_results.extend(nested_results)

            elif isinstance(value, list):
                # Process list items
                redacted_list = []
                for item in value:
                    if isinstance(item, dict):
                        redacted_item, item_results = self.redact(item)
                        redacted_list.append(redacted_item)
                        all_results.extend(item_results)
                    else:
                        redacted_list.append(item)
                redacted[field_name] = redacted_list

            else:
                # Keep non-string values as-is
                redacted[field_name] = value

        return redacted, all_results

    def redact_log_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact a log entry before storage.

        This is the main entry point for the ingestion pipeline.
        """
        redacted, detections = self.redact(log_entry)

        # Add metadata about redaction
        if detections:
            redacted["_pii_redacted"] = True
            redacted["_pii_count"] = len(detections)
            redacted["_pii_types"] = list(set(d.pii_type.value for d in detections))

        return redacted


# Global instance for use in ingestion pipeline
_pii_redactor = PIIRedactor()


def redact_log(log_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to redact PII from a log entry.

    Use this at the ingestion endpoint to ensure no PII is stored.
    """
    return _pii_redactor.redact_log_entry(log_entry)


def configure_pii_redaction(enabled: bool = True, check_fields: Optional[List[str]] = None):
    """
    Configure PII redaction settings.

    Args:
        enabled: Whether PII redaction is enabled
        check_fields: Custom list of fields to check for PII
    """
    global _pii_redactor

    if enabled:
        detector = PIIDetector(check_fields=check_fields)
        _pii_redactor = PIIRedactor(detector)
    else:
        # Create a no-op redactor
        _pii_redactor = PIIRedactor(PIIDetector(check_fields=[]))
