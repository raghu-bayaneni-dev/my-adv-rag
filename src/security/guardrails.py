import json
import logging
from typing import Optional
from src.config.settings import Settings
from src.models.security import GuardrailCategory, GuardrailResult
from src.security.pii_sanitizer import PIISanitizer
from src.security.injection_guard import PromptInjectionGuard

logger = logging.getLogger(__name__)

CHIPOTLE_CANNED_REFUSAL = (
    "I am an enterprise assistant dedicated solely to searching authorized corporate documentation. "
    "I cannot assist with general programming, casual conversation, or external topics."
)

PROMPT_INJECTION_REFUSAL = (
    "Security Policy Violation: System prompt overrides and instruction injections are blocked."
)

GUARDRAIL_CLASSIFIER_PROMPT = """You are a strict Enterprise Security Gatekeeper for a corporate document assistant.
Your task is to classify whether the user's query is an IN-SCOPE corporate document lookup or OUT-OF-SCOPE.

IN-SCOPE queries include:
- Inquiries about company architecture, engineering specs, policies, revenue, budgets, guidelines, SLA, or corporate info.
- Questions referencing internal systems, departments (Engineering, Finance, Public), or business workflows.

OUT-OF-SCOPE queries include:
- General programming / coding requests (e.g., "write a python function to sort a list", "debug this C++ code").
- Open-domain trivia / general knowledge (e.g., "what is the capital of France", "how far is the moon").
- Casual chit-chat, jokes, recipes, creative writing, or general life advice.

You MUST respond strictly with a valid JSON object matching this schema:
{
  "is_allowed": true/false,
  "category": "in_scope" or "out_of_scope" or "prompt_injection",
  "reasoning": "brief explanation"
}

USER QUERY TO EVALUATE:
"""


class SecurityGuardrailGate:
    """
    Two-tier black-box security gate:
    1. Regex PII sanitization + prompt injection pattern matching.
    2. Fast low-temperature LLM intent classification for corporate domain boundaries.
    """
    def __init__(self, settings: Settings, classifier_llm=None):
        self.settings = settings
        self.pii_sanitizer = PIISanitizer()
        self.injection_guard = PromptInjectionGuard()
        self.classifier_llm = classifier_llm

    def evaluate(self, raw_query: str) -> GuardrailResult:
        """
        Evaluates query and returns structured GuardrailResult.
        """
        cleaned_query = raw_query.strip()
        if not cleaned_query:
            return GuardrailResult(
                is_allowed=False,
                category=GuardrailCategory.OUT_OF_SCOPE,
                refusal_message=CHIPOTLE_CANNED_REFUSAL,
                sanitized_query="",
                reasoning="Empty query"
            )

        # 1. PII Sanitization
        sanitized_query = cleaned_query
        pii_found = False
        if self.settings.enable_pii_redaction:
            sanitized_query, pii_found = self.pii_sanitizer.sanitize(cleaned_query)

        # 2. Fast Prompt Injection Defense
        if self.settings.enable_prompt_injection_defense:
            if self.injection_guard.detect_injection(cleaned_query):
                logger.warning(f"Prompt injection attempt blocked: {cleaned_query[:60]}")
                return GuardrailResult(
                    is_allowed=False,
                    category=GuardrailCategory.PROMPT_INJECTION,
                    refusal_message=PROMPT_INJECTION_REFUSAL,
                    sanitized_query=sanitized_query,
                    reasoning="Prompt injection signature detected"
                )

        # 3. LLM Corporate Scope Classifier
        classification = self._classify_scope(sanitized_query)
        if not classification.get("is_allowed", True):
            category = GuardrailCategory(classification.get("category", "out_of_scope"))
            refusal = PROMPT_INJECTION_REFUSAL if category == GuardrailCategory.PROMPT_INJECTION else CHIPOTLE_CANNED_REFUSAL
            return GuardrailResult(
                is_allowed=False,
                category=category,
                refusal_message=refusal,
                sanitized_query=sanitized_query,
                reasoning=classification.get("reasoning", "Out of corporate scope")
            )

        return GuardrailResult(
            is_allowed=True,
            category=GuardrailCategory.PII_DETECTED if pii_found else GuardrailCategory.IN_SCOPE,
            refusal_message=None,
            sanitized_query=sanitized_query,
            reasoning="Valid in-scope corporate query"
        )

    def _classify_scope(self, query: str) -> dict:
        """Runs fast structured classification on user query."""
        # If mock/custom LLM service injected (e.g. in tests)
        if self.classifier_llm:
            try:
                res_str = self.classifier_llm.generate(f"classify guardrail: {query}")
                return json.loads(res_str)
            except Exception:
                pass

        # Check common heuristic indicators for rapid zero-cost classification
        lower_q = query.lower()
        coding_signals = ["write a python", "write a function", "write code", "sort a list", "write a script", "debug this"]
        trivia_signals = ["capital of", "who was the first president", "tell me a joke", "recipe for", "how far is the sun"]

        for sig in coding_signals + trivia_signals:
            if sig in lower_q:
                return {
                    "is_allowed": False,
                    "category": "out_of_scope",
                    "reasoning": "Detected general programming or open-domain trivia pattern"
                }

        # Attempt fast litellm call if keys configured
        api_key = (
            getattr(self.settings, "groq_api_key", None) 
            or os.getenv("GROQ_API_KEY") 
            or getattr(self.settings, "gemini_api_key", None) 
            or os.getenv("GEMINI_API_KEY") 
            or getattr(self.settings, "openai_api_key", None)
        )
        if api_key:
            try:
                from litellm import completion
                response = completion(
                    model=self.settings.guardrail_llm_model,
                    messages=[
                        {"role": "system", "content": "Respond strictly with valid JSON."},
                        {"role": "user", "content": GUARDRAIL_CLASSIFIER_PROMPT + query}
                    ],
                    temperature=0.0,
                    api_key=api_key
                )
                raw_json = response.choices[0].message.content.strip()
                # Clean json fences if returned
                if raw_json.startswith("```json"):
                    raw_json = raw_json[7:-3].strip()
                return json.loads(raw_json)
            except Exception as e:
                logger.warning(f"Fast LLM classifier call failed, defaulting to allow: {e}")

        return {"is_allowed": True, "category": "in_scope", "reasoning": "Default permit"}
