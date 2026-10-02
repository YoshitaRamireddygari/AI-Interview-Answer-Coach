import re
from typing import Optional


class CategoryDetector:
    """
    Service for detecting or standardizing interview question categories.
    Supported categories: 'behavioral', 'technical', 'system-design', 'situational', 'general'.
    """

    BEHAVIORAL_KEYWORDS = [
        "tell me about a time", "describe a situation", "conflict", "disagreement", 
        "team", "leadership", "prioritize", "failure", "mistake", "handle", "managed", 
        "challenge", "deadline", "pressure", "difficult", "worked with", "colleague", 
        "feedback", "accomplishment", "proud", "overcome"
    ]

    SYSTEM_DESIGN_KEYWORDS = [
        "scale", "sharding", "throughput", "load balancer", "distributed", 
        "replication", "partitioning", "high availability", "failover", "queue", 
        "message broker", "kafka", "rabbitmq"
    ]

    TECHNICAL_KEYWORDS = [
        "code", "sql", "database", "api", "architecture", "algorithm", "function", 
        "bug", "refactor", "git", "python", "javascript", "java", "cpp", "index", 
        "cache", "latency", "optimize", "query", "interface", "system", "design", 
        "microservice", "memory", "profiling", "orm", "endpoint", "rest", "graphql", 
        "schema", "table", "joins", "concurrency", "thread", "async", "locks"
    ]

    SITUATIONAL_KEYWORDS = [
        "what would you do if", "how would you handle if", "suppose", "imagine", 
        "hypothetically", "if a client"
    ]

    VALID_CATEGORIES = {"behavioral", "technical", "system-design", "situational", "general"}

    @classmethod
    def detect_category(cls, question: str, category: Optional[str] = None) -> str:
        """
        Detects or standardizes interview category based on explicit input or question keywords.
        """
        if category:
            clean_cat = category.strip().lower()
            if clean_cat in cls.VALID_CATEGORIES:
                return clean_cat
            if clean_cat not in ["auto", "none", "", "null", "general"]:
                return clean_cat

        if not question or not question.strip():
            return "general"

        q_lower = question.lower()

        # Check behavioral patterns
        for kw in cls.BEHAVIORAL_KEYWORDS:
            if kw in q_lower:
                return "behavioral"

        # Check system design patterns
        for kw in cls.SYSTEM_DESIGN_KEYWORDS:
            if kw in q_lower:
                return "system-design"

        # Check technical patterns
        for kw in cls.TECHNICAL_KEYWORDS:
            if kw in q_lower:
                return "technical"

        # Check situational patterns
        for kw in cls.SITUATIONAL_KEYWORDS:
            if kw in q_lower:
                return "situational"

        return "general"
