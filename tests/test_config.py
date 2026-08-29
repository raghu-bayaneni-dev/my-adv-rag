import pytest
from src.config.settings import Settings
from src.models.document import Department, ChunkMetadata, DocumentChunk
from src.models.security import UserRole


def test_settings_defaults():
    """Verify settings initialize with constitutional defaults without requiring live keys."""
    settings = Settings()
    assert settings.chunk_size == 600
    assert settings.chunk_overlap == 120
    assert settings.data_dir == "data"
    assert settings.enable_pii_redaction is True
    assert settings.enable_prompt_injection_defense is True


def test_settings_custom_values(monkeypatch):
    """Verify settings load overrides from environment variables."""
    monkeypatch.setenv("CHUNK_SIZE", "800")
    monkeypatch.setenv("ENABLE_PII_REDACTION", "false")
    settings = Settings()
    assert settings.chunk_size == 800
    assert settings.enable_pii_redaction is False


def test_chunk_metadata_constitutional_validation():
    """Verify ChunkMetadata enforces mandatory fields per Principle III."""
    # Valid chunk metadata
    meta = ChunkMetadata(
        department_access=Department.ENGINEERING,
        source_file="architecture.md",
        page_number=1
    )
    assert meta.department_access == Department.ENGINEERING
    assert meta.source_file == "architecture.md"
    assert meta.page_number == 1

    # Missing department_access raises validation error
    with pytest.raises(Exception):
        ChunkMetadata(
            source_file="test.md",
            page_number=1
        )

    # Empty source_file raises validation error
    with pytest.raises(ValueError):
        ChunkMetadata(
            department_access=Department.PUBLIC,
            source_file="   ",
            page_number=1
        )

    # Page number < 1 raises validation error
    with pytest.raises(ValueError):
        ChunkMetadata(
            department_access=Department.FINANCE,
            source_file="budget.md",
            page_number=0
        )


def test_user_role_rbac_mapping():
    """Verify UserRole hierarchical access matrix."""
    assert UserRole.PUBLIC.allowed_departments() == [Department.PUBLIC]
    assert set(UserRole.FINANCE_MANAGER.allowed_departments()) == {Department.FINANCE, Department.PUBLIC}
    assert set(UserRole.ENGINEERING_LEAD.allowed_departments()) == {Department.ENGINEERING, Department.PUBLIC}
    assert set(UserRole.ADMIN.allowed_departments()) == {Department.ENGINEERING, Department.FINANCE, Department.PUBLIC}
