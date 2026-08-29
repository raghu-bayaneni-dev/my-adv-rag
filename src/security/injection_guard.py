import re
from typing import List


class PromptInjectionGuard:
    """
    Detects adversarial prompt injection attempts and system prompt override attacks.
    """
    def __init__(self):
        self.injection_patterns: List[re.Pattern] = [
            re.compile(r'ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions', re.IGNORECASE),
            re.compile(r'disregard\s+(?:all\s+)?(?:previous|prior|guardrails)', re.IGNORECASE),
            re.compile(r'system\s+override', re.IGNORECASE),
            re.compile(r'developer\s+mode\s+output', re.IGNORECASE),
            re.compile(r'reveal\s+(?:all\s+)?(?:system|internal)\s+(?:prompts|keys|passwords)', re.IGNORECASE),
            re.compile(r'you\s+are\s+now\s+(?:unfiltered|dan|unconstrained)', re.IGNORECASE),
        ]

    def detect_injection(self, text: str) -> bool:
        """
        Returns True if prompt injection pattern is detected.
        """
        for pattern in self.injection_patterns:
            if pattern.search(text):
                return True
        return False
