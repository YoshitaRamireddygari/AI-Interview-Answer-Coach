import re

def safe_log_snippet(text: str, max_length: int = 50) -> str:
    """
    Sanitizes and truncates user inputs or API text for privacy-safe logging.
    Prevents leaking long user answers or sensitive PII into log files.
    """
    if not text:
        return "<empty>"
    
    # Replace email addresses and potential API keys with masked placeholders
    sanitized = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL_MASKED]", text)
    sanitized = re.sub(r"AIzaSy[A-Za-z0-9_-]{33}", "[API_KEY_MASKED]", sanitized)
    
    cleaned = " ".join(sanitized.split())
    if len(cleaned) <= max_length:
        return cleaned
    
    return f"{cleaned[:max_length]}... (len={len(text)})"
