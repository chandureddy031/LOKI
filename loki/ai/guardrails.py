"""AI guardrails for safety."""

import re

from ..security.leak_prevention import LeakPrevention


class AIGuardrails:
    """Prevents prompt injection and abuse while allowing natural conversation."""

    INJECTION_PATTERNS = [
        r"ignore\s+(?:all\s+)?(?:previous|above|prior)\s+(?:instructions?|prompts?)",
        r"you\s+are\s+now\s+(?:a|an)\s+\w+",
        r"pretend\s+(?:you\s+are|to\s+be)",
        r"act\s+as\s+if",
        r"disregard\s+(?:all\s+)?(?:previous|your)\s+instructions?",
        r"new\s+instructions?:",
        r"system\s*:\s*",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"\[INST\]",
        r"<<SYS>>",
        r"jailbreak",
        r" DAN\b",
    ]

    DANGEROUS_TOPICS = [
        r"(?:how\s+to\s+)?(?:hack\s+into|compromise|breach)\s+(?:a\s+)?(?:system|server|network|database)",
        r"(?:create|write|build)\s+(?:a\s+)?(?:virus|malware|ransomware|trojan|worm)",
        r"(?:steal|exfiltrate)\s+(?:data|credentials|passwords|tokens)",
        r"(?:sql|ldap|os\s+command)\s+injection",
        r"(?:ddos|denial\s+of\s+service)\s+attack",
        r"(?:brute\s+force|credential\s+stuffing)\s+(?:password|login)",
        r"(?:bypass|disable)\s+(?:security|authentication|firewall|2fa)",
        r"(?:create|set\s+up)\s+(?:a\s+)?(?:phishing|scam)\s+(?:site|page|campaign)",
    ]

    TRAINING_PATTERNS = [
        r"what\s+(?:data|files|code)\s+(?:were|was)\s+you\s+trained\s+on",
        r"show\s+(?:me\s+)?(?:your|the)\s+(?:training|context|data|prompt)",
        r"what\s+(?:is|are)\s+your\s+(?:instructions?|system\s*prompt)",
        r"reveal\s+(?:your|the)\s+(?:instructions?|training|context)",
        r"tell\s+me\s+(?:about|your)\s+training",
        r"what\s+(?:model|ai)\s+(?:are|is)\s+you",
        r"repeat\s+(?:your|the)\s+(?:system|initial)\s+(?:prompt|instructions?)",
    ]

    @classmethod
    def validate_input(cls, user_input: str) -> tuple[bool, str]:
        """Check user input for injection attempts."""
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                return False, "Potential prompt injection detected"

        for pattern in cls.DANGEROUS_TOPICS:
            if re.search(pattern, user_input, re.IGNORECASE):
                return False, "This topic is not supported"

        for pattern in cls.TRAINING_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                return False, "I cannot reveal training details"

        return True, ""

    @classmethod
    def validate_output(cls, ai_output: str) -> str:
        """Filter AI output for safety."""
        output = re.sub(r"```(?:bash|sh|shell|powershell|cmd).*?```", "```[CODE BLOCK REMOVED]```", ai_output, flags=re.DOTALL)

        training_leak_patterns = [
            r"I\s+(?:was|were)\s+trained\s+on",
            r"my\s+(?:training|context)\s+(?:data|includes?|contains?)",
            r"(?:my|the)\s+(?:context|prompt)\s+(?:includes?|contains?|has)",
        ]

        for pattern in training_leak_patterns:
            output = re.sub(pattern, "[FILTERED]", output, flags=re.IGNORECASE)

        output = LeakPrevention.sanitize(output)
        return output
