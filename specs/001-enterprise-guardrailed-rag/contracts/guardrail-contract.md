# Interface Contract: Security Guardrails & Gatekeeper

**Component**: `src.security.guardrails` | **Type**: Python Security Service

---

## 1. Overview

The `SecurityGuardrailGate` intercepts raw user queries before vector search or LLM generation. It performs PII redaction, prompt injection filtering, and corporate domain scope classification.

---

## 2. Public API Interface

```python
class SecurityGuardrailGate:
    def __init__(self, config: Settings, classifier_llm: Optional[LLMService] = None):
        ...

    def evaluate(self, raw_query: str) -> GuardrailResult:
        """
        Evaluates query against security gates and corporate scope boundary.
        
        Args:
            raw_query: Raw user prompt string from chat interface.
            
        Returns:
            GuardrailResult with pass/fail decision, sanitized query text, and refusal text.
        """
        ...
```

---

## 3. Evaluation Rules & Responses

| Condition | Action | Resulting `category` | Response Text |
| :--- | :--- | :--- | :--- |
| **Out-of-Scope (Coding/General Knowledge/Chit-chat)** | Reject | `out_of_scope` | *"I am an enterprise assistant dedicated solely to searching authorized corporate documentation. I cannot assist with general programming, casual conversation, or external topics."* |
| **Prompt Injection Detected** | Block & Log | `prompt_injection` | *"Security Policy Violation: System prompt overrides and instruction injections are blocked."* |
| **Sensitive PII in Query** | Sanitize & Allow | `pii_detected` | Sanitized query string with `[REDACTED_SSN]` or `[REDACTED_CARD]` passed to retriever. |
| **Valid Corporate In-Scope Query** | Allow | `in_scope` | Raw/sanitized query forwarded to vector search. |
