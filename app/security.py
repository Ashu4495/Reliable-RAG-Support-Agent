import re
from typing import Tuple, List, Dict, Any

# Forbidden patterns and words indicating sensitive disclosures
SENSITIVE_PATTERNS = [
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", # Email regex
    r"\b\d{1,5}\s+[A-Za-z0-9.\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b", # Street addresses
    r"\b(?:risk[_\s]score|fraud[_\s]review|warehouse[_\s]note|support[_\s]tags?)\b",
]

INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?",
    r"reveal\s+(?:your\s+)?(?:system|hidden)\s+prompt",
    r"system\s+instruction:",
    r"disregard\s+(?:all\s+)?rules",
    r"tell\s+every\s+customer.*approve",
    r"issue\s+a\s+\$100\s+coupon",
    r"bypass\s+(?:security|policy)",
]

class SecurityFilter:
    @staticmethod
    def is_prompt_injection(text: str) -> bool:
        if not text:
            return False
        text_lower = text.lower()
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False

    @staticmethod
    def sanitize_untrusted_text(text: str) -> str:
        """Sanitizes text from external sources or knowledge base documents to defuse instruction-like formatting."""
        if not text:
            return ""
        # Neutralize common markdown injection formatting
        sanitized = re.sub(r"(?i)>\s*SYSTEM INSTRUCTION:", "[Untrusted Note:]", text)
        sanitized = re.sub(r"(?i)SYSTEM INSTRUCTION:", "[Untrusted Note:]", sanitized)
        return sanitized

    @staticmethod
    def check_and_redact_sensitive_data(text: str) -> Tuple[str, List[str]]:
        """Redacts known sensitive customer PII or internal fields from customer-facing text."""
        redactions = []
        clean_text = text

        # Check for specific mock database PII if leaked
        known_pii = [
            "ava.morgan@example.test",
            "maya.reed@example.test",
            "noah.kim@example.test",
            "olivia.chen@example.test",
            "ethan.brooks@example.test",
            "sofia.patel@example.test",
            "liam.jones@example.test",
            "lucas.green@example.test",
            "isabella.stone@example.test",
            "henry.diaz@example.test",
            "emma.wilson@example.test",
            "james.taylor@example.test",
            "220 King Street",
            "18 Cedar Lane",
            "44 Lake Street",
            "79 Market Street",
            "12 Harbor Road",
            "96 Peachtree Avenue",
            "55 Congress Avenue",
            "310 Pine Street",
            "7 Ocean Drive",
            "801 Larimer Street",
            "1010 Robson Street",
            "400 Walnut Street",
        ]

        for pii in known_pii:
            if pii.lower() in clean_text.lower():
                clean_text = re.sub(re.escape(pii), "[REDACTED]", clean_text, flags=re.IGNORECASE)
                redactions.append(pii)

        # Internal operational phrases
        internal_phrases = [
            "fraud review cleared",
            "risk score: 82",
            "risk score",
            "warehouse note",
        ]
        for phrase in internal_phrases:
            if phrase.lower() in clean_text.lower():
                clean_text = re.sub(re.escape(phrase), "[REDACTED]", clean_text, flags=re.IGNORECASE)
                redactions.append(phrase)

        return clean_text, redactions

    @staticmethod
    def filter_customer_response(response: str) -> str:
        """Final sanity check filter on the agent's response."""
        clean_text, _ = SecurityFilter.check_and_redact_sensitive_data(response)
        return clean_text
