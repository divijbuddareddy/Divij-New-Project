import re
import html
from typing import Dict, Any, Union

def sanitize_untrusted_text(text: str) -> str:
    """
    Sanitizes external data (emails, Slack messages, commit messages, PR descriptions)
    to neutralize prompt injection attempts and wraps them in strict XML boundaries.
    """
    if not text:
        return ""
    
    # Escape dangerous HTML / XML syntax
    escaped = html.escape(text)

    # Detect common prompt injection attack patterns and neutralize them
    patterns_to_neutralize = [
        r"(?i)ignore\s+(all\s+)?previous\s+instructions",
        r"(?i)system\s*:\s*you\s+are",
        r"(?i)disregard\s+all\s+prior\s+rules",
        r"(?i)new\s+system\s+prompt",
        r"(?i)override\s+permission",
        r"(?i)execute\s+action\s+without\s+approval",
        r"(?i)delete\s+all\s+records"
    ]
    
    sanitized = escaped
    for pattern in patterns_to_neutralize:
        sanitized = re.sub(pattern, "[FLAGGED_UNTRUSTED_DIRECTIVE_NEUTRALIZED]", sanitized)
    
    return f"<untrusted_external_content>\n{sanitized}\n</untrusted_external_content>"

def wrap_evidence_for_prompt(evidence_list: list) -> str:
    """
    Formats a list of evidence items into safe, structured text with explicit provenance and untrusted boundaries.
    """
    output = []
    for item in evidence_list:
        src = item.get("source", "unknown")
        actor = item.get("actor", "unknown")
        action = item.get("action", "unknown")
        ts = item.get("event_timestamp", "")
        summary = sanitize_untrusted_text(item.get("content_summary") or item.get("title") or "")
        
        output.append(
            f"EVIDENCE [{item.get('id', 'N/A')}] Source: {src} | Actor: {actor} | Action: {action} | Time: {ts}\n"
            f"Content: {summary}"
        )
    return "\n\n".join(output)
