import re
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeDocument:
    """
    Represents a knowledge document or passage retrieved from a knowledge provider.
    """
    document_id: str
    title: str
    content: str
    source: str
    score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseKnowledgeProvider(ABC):
    """
    Abstract interface for technical knowledge providers.
    Decouples the verification layer from the underlying knowledge store.
    Allows switching between in-memory/rule providers and vector-search RAG providers
    without making any changes to the rest of the application.
    """

    @abstractmethod
    def query_knowledge(self, query: str, top_k: int = 3) -> List[KnowledgeDocument]:
        """
        Retrieves relevant knowledge documents matching the query string.
        """
        pass


class SimpleKnowledgeProvider(BaseKnowledgeProvider):
    """
    Current lightweight implementation: In-memory curated knowledge base.
    Uses structured domain knowledge specifications and text matching.
    Provides fast, deterministic lookup without requiring a heavy vector database server.
    """

    DEFAULT_KNOWLEDGE_BASE = [
        KnowledgeDocument(
            document_id="doc_http_spec",
            title="HTTP Application Layer Protocol",
            content="HTTP (Hypertext Transfer Protocol) is an application-layer network protocol for transmitting hypermedia documents. It is not a programming language.",
            source="RFC 9110 HTTP Semantics",
            metadata={"category": "networking", "type": "protocol"}
        ),
        KnowledgeDocument(
            document_id="doc_html_spec",
            title="HTML Markup Language Standard",
            content="HTML (Hypertext Markup Language) is a standard declarative markup language used to structure web documents. It is not a programming language.",
            source="W3C HTML5 Specification",
            metadata={"category": "frontend", "type": "markup"}
        ),
        KnowledgeDocument(
            document_id="doc_java_js",
            title="Java vs JavaScript Runtime Disambiguation",
            content="Java is a compiled, statically-typed object-oriented language running on the JVM. JavaScript is a dynamic, interpreted scripting language running on V8/SpiderMonkey runtimes. They are completely distinct languages.",
            source="ECMA-262 & Oracle Java Specs",
            metadata={"category": "languages", "type": "runtime"}
        ),
        KnowledgeDocument(
            document_id="doc_rest_arch",
            title="REST Architectural Style",
            content="REST (Representational State Transfer) is an architectural style for designing networked applications and APIs. It relies on stateless HTTP communication.",
            source="Fielding Dissertation on API Architecture",
            metadata={"category": "architecture", "type": "design_pattern"}
        ),
        KnowledgeDocument(
            document_id="doc_nosql_acid",
            title="NoSQL BASE vs ACID Consistency",
            content="NoSQL databases typically follow the BASE model (Basically Available, Soft-state, Eventual consistency) rather than strict RDBMS ACID guarantees by default.",
            source="Distributed Systems Database Theory",
            metadata={"category": "databases", "type": "consistency"}
        )
    ]

    def __init__(self, documents: Optional[List[KnowledgeDocument]] = None):
        self.documents = documents or list(self.DEFAULT_KNOWLEDGE_BASE)

    def query_knowledge(self, query: str, top_k: int = 3) -> List[KnowledgeDocument]:
        """
        Performs keyword and token similarity match against the in-memory knowledge store.
        """
        query_terms = set(re.findall(r"\w+", query.lower()))
        if not query_terms:
            return []

        results: List[KnowledgeDocument] = []
        for doc in self.documents:
            doc_text = f"{doc.title} {doc.content}".lower()
            doc_terms = set(re.findall(r"\w+", doc_text))
            
            # Calculate Jaccard similarity score
            intersection = query_terms.intersection(doc_terms)
            if intersection:
                score = len(intersection) / len(query_terms)
                results.append(
                    KnowledgeDocument(
                        document_id=doc.document_id,
                        title=doc.title,
                        content=doc.content,
                        source=doc.source,
                        score=round(score, 2),
                        metadata=doc.metadata
                    )
                )

        # Sort by relevance score descending
        results.sort(key=lambda d: d.score, reverse=True)
        return results[:top_k]


class VectorKnowledgeProvider(BaseKnowledgeProvider):
    """
    Future RAG Knowledge Provider Slot.
    Outlines the integration vector database (ChromaDB / FAISS / Qdrant) architecture.
    When instantiated, performs semantic dense vector search using embeddings.
    """

    def __init__(self, vector_db_client: Any = None, embedding_model: Any = None):
        self.client = vector_db_client
        self.embedding_model = embedding_model
        logger.info("VectorKnowledgeProvider initialized as RAG extension slot.")

    def query_knowledge(self, query: str, top_k: int = 3) -> List[KnowledgeDocument]:
        """
        Future RAG Query Implementation:
        1. Generate dense vector embedding for query string via embedding_model.
        2. Execute vector similarity search (cosine distance) against vector_db_client.
        3. Convert retrieved chunk embeddings & metadata into KnowledgeDocument objects.
        """
        if self.client is None:
            logger.warning("VectorKnowledgeProvider client not attached. Falling back to empty RAG result.")
            return []
        
        # Placeholder for vector database retrieval logic
        return []
