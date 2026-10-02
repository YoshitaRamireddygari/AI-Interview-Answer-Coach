import pytest
from app.services.knowledge_provider import (
    BaseKnowledgeProvider,
    SimpleKnowledgeProvider,
    VectorKnowledgeProvider,
    KnowledgeDocument
)
from app.services.technical_verifier import RuleBasedVerificationProvider
from app.schemas.technical_verification import ClaimVerificationStatus


def test_simple_knowledge_provider_query():
    """
    Test querying SimpleKnowledgeProvider for matching domain documentation documents.
    """
    provider = SimpleKnowledgeProvider()
    docs = provider.query_knowledge(query="HTTP programming language", top_k=2)

    assert len(docs) > 0
    assert docs[0].document_id == "doc_http_spec"
    assert "RFC 9110" in docs[0].source
    assert docs[0].score > 0.0


def test_vector_knowledge_provider_slot():
    """
    Test that VectorKnowledgeProvider can be instantiated as a RAG extension slot.
    """
    rag_provider = VectorKnowledgeProvider(vector_db_client=None)
    docs = rag_provider.query_knowledge(query="REST API architectural style", top_k=3)
    assert isinstance(docs, list)


def test_custom_knowledge_provider_injection():
    """
    Verify that RuleBasedVerificationProvider accepts custom KnowledgeProvider
    without breaking verification contracts or requiring rest of app to change.
    """
    class CustomMockKnowledgeProvider(BaseKnowledgeProvider):
        def query_knowledge(self, query: str, top_k: int = 3):
            return [
                KnowledgeDocument(
                    document_id="doc_custom",
                    title="Custom Mock Tech Spec",
                    content="Custom specification details",
                    source="ISO Custom Standard 9001"
                )
            ]

    custom_provider = RuleBasedVerificationProvider(knowledge_provider=CustomMockKnowledgeProvider())
    claims = custom_provider.verify_claims("API Question", "HTTP is a programming language.")

    assert len(claims) > 0
    assert claims[0].status == ClaimVerificationStatus.POTENTIAL_ISSUE
    assert claims[0].source_reference == "ISO Custom Standard 9001"
