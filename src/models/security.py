from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from src.models.document import Department


class UserRole(str, Enum):
    """
    Active user role context enforcing RBAC access matrix.
    """
    PUBLIC = "Public"
    FINANCE_MANAGER = "Finance-Manager"
    ENGINEERING_LEAD = "Engineering-Lead"
    ADMIN = "Admin"

    def allowed_departments(self) -> List[Department]:
        """
        Hierarchical department visibility matrix.
        - Admin: Engineering + Finance + Public
        - Finance-Manager: Finance + Public
        - Engineering-Lead: Engineering + Public
        - Public: Public only
        """
        if self == UserRole.ADMIN:
            return [Department.ENGINEERING, Department.FINANCE, Department.PUBLIC]
        elif self == UserRole.FINANCE_MANAGER:
            return [Department.FINANCE, Department.PUBLIC]
        elif self == UserRole.ENGINEERING_LEAD:
            return [Department.ENGINEERING, Department.PUBLIC]
        elif self == UserRole.PUBLIC:
            return [Department.PUBLIC]
        return [Department.PUBLIC]

    def allowed_department_strings(self) -> List[str]:
        """Returns string values for ChromaDB `$in` queries."""
        return [dept.value for dept in self.allowed_departments()]


class GuardrailCategory(str, Enum):
    """Classification categories for user queries."""
    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"
    PROMPT_INJECTION = "prompt_injection"
    PII_DETECTED = "pii_detected"


class GuardrailResult(BaseModel):
    """Result of black-box security gate inspection."""
    is_allowed: bool = Field(..., description="Whether query is permitted to proceed to vector search")
    category: GuardrailCategory = Field(..., description="Classification category")
    refusal_message: Optional[str] = Field(default=None, description="Canned refusal if rejected")
    sanitized_query: str = Field(..., description="Sanitized query text with PII redacted if applicable")
    reasoning: Optional[str] = Field(default=None, description="Internal classification rationale")
