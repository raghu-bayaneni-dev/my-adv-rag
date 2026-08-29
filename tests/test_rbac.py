import pytest
from src.models.document import Department, ChunkMetadata, DocumentChunk
from src.models.security import UserRole
from src.retrieval.vector_store import VectorStoreService


def test_rbac_vector_store_isolation(test_settings, mock_embedding_service, sample_chunks):
    """
    Verify strict zero-leakage RBAC isolation at the vector store query level (SC-001).
    - Public user MUST NOT retrieve Finance or Engineering chunks.
    - Finance Manager MUST retrieve Finance and Public chunks only.
    - Engineering Lead MUST retrieve Engineering and Public chunks only.
    - Admin MUST retrieve all chunks.
    """
    vector_store = VectorStoreService(
        settings=test_settings,
        embedding_service=mock_embedding_service
    )
    # Add sample multi-department chunks
    vector_store.add_chunks(sample_chunks)

    # 1. Query as PUBLIC role for financial or engineering terms
    public_results = vector_store.search(
        query_text="revenue financial budget and payment retry",
        user_role=UserRole.PUBLIC,
        top_k=5
    )
    # Public should only retrieve Public chunks
    assert all(c.metadata.department_access == Department.PUBLIC for c in public_results)
    assert not any(c.metadata.department_access == Department.FINANCE for c in public_results)
    assert not any(c.metadata.department_access == Department.ENGINEERING for c in public_results)

    # 2. Query as FINANCE_MANAGER role
    finance_results = vector_store.search(
        query_text="revenue financial budget",
        user_role=UserRole.FINANCE_MANAGER,
        top_k=5
    )
    assert any(c.metadata.department_access == Department.FINANCE for c in finance_results)
    assert not any(c.metadata.department_access == Department.ENGINEERING for c in finance_results)

    # 3. Query as ENGINEERING_LEAD role
    eng_results = vector_store.search(
        query_text="payment service retry limit",
        user_role=UserRole.ENGINEERING_LEAD,
        top_k=5
    )
    assert any(c.metadata.department_access == Department.ENGINEERING for c in eng_results)
    assert not any(c.metadata.department_access == Department.FINANCE for c in eng_results)

    # 4. Query as ADMIN role
    admin_results = vector_store.search(
        query_text="enterprise overview revenue and payment service",
        user_role=UserRole.ADMIN,
        top_k=5
    )
    retrieved_depts = {c.metadata.department_access for c in admin_results}
    assert Department.ENGINEERING in retrieved_depts or Department.FINANCE in retrieved_depts
