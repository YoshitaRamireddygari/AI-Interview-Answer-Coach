import re
import html
from typing import Optional, List

def sanitize_text_input(text: str) -> str:
    """
    Sanitizes raw user text inputs:
    - Escapes HTML/script tags to prevent XSS.
    - Strips control characters and zero-width spaces often used in prompt injection bypasses.
    - Preserves standard punctuation, spaces, and line breaks.
    """
    if not text:
        return ""
    
    # 1. Unify newlines
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # 2. Strip dangerous control characters (0x00-0x08, 0x0B-0x0C, 0x0E-0x1F, zero-width spaces)
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\u200B-\u200D\uFEFF]", "", cleaned)
    
    # 3. Escape HTML entities
    escaped = html.escape(cleaned)
    
    return escaped.strip()


def detect_prompt_injection_attempt(text: str) -> bool:
    """
    Detects known prompt injection patterns attempting to override system evaluation rules.
    """
    if not text:
        return False
        
    patterns = [
        r"ignore (all )?(previous|system) instructions",
        r"disregard (all )?(prior|previous) prompts",
        r"system override",
        r"give me (a )?(score|rating) (of )?10",
        r"assign (a )?max(imum)? score",
        r"you are now a",
        r"bypass evaluation"
    ]
    
    text_lower = text.lower()
    return any(re.search(pat, text_lower) for pat in patterns)
