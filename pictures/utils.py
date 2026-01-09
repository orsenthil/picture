"""
Utility functions for the pictures app
"""
import html


def sanitize_html_entities(text):
    """
    Sanitize HTML entities in text by decoding them to their actual characters.
    
    Uses Python's standard library html.unescape() to properly decode all HTML entities
    like &nbsp; to space, &amp; to &, &lt; to <, &gt; to >, etc.
    
    Also normalizes non-breaking spaces (U+00A0) to regular spaces for consistency.
    
    Args:
        text: String that may contain HTML entities
        
    Returns:
        String with HTML entities decoded to their actual characters
    """
    if not text:
        return text
    
    # Use standard library html.unescape() to decode all HTML entities
    # This properly handles &nbsp;, &amp;, &lt;, &gt;, &quot;, &#1234;, etc.
    sanitized = html.unescape(text)
    
    # Normalize non-breaking spaces (U+00A0) to regular spaces
    # html.unescape converts &nbsp; to \xa0 (non-breaking space), convert to regular space
    sanitized = sanitized.replace('\xa0', ' ')
    
    return sanitized

