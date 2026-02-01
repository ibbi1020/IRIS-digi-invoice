"""
Invoice ref number utilities.

Implements the suggest-next algorithm from PRD section 9.3:
- If prior ref has trailing digits: increment by 1, preserve leading zeros
- If no trailing digits: no suggestion
"""

import re


def suggest_next_ref_no(last_ref_no: str) -> str | None:
    """
    Suggest the next invoiceRefNo based on the last submitted one.

    Algorithm:
    - If ref has trailing digits: increment trailing integer by 1, preserve leading zeros width
    - If no trailing digits: return None (no suggestion)

    Examples:
        "1005" → "1006"
        "INV-0009" → "INV-0010"
        "INV-A" → None (no suggestion)
        "SALE-099" → "SALE-100"

    Args:
        last_ref_no: The last successfully submitted invoiceRefNo

    Returns:
        Suggested next invoiceRefNo, or None if no suggestion possible
    """
    if not last_ref_no:
        return None

    # Match trailing digits
    match = re.search(r"(\d+)$", last_ref_no)
    if not match:
        return None

    # Extract components
    prefix = last_ref_no[: match.start()]
    number_str = match.group(1)

    # Increment the number
    original_width = len(number_str)
    new_number = int(number_str) + 1
    new_number_str = str(new_number)

    # Preserve leading zeros width if new number fits
    if len(new_number_str) <= original_width:
        new_number_str = new_number_str.zfill(original_width)

    return prefix + new_number_str


def validate_ref_no_format(ref_no: str) -> bool:
    """
    Validate invoiceRefNo format.

    Basic validation:
    - Not empty
    - Max 50 characters
    - Alphanumeric with common separators allowed

    Args:
        ref_no: The invoiceRefNo to validate

    Returns:
        True if valid, False otherwise
    """
    if not ref_no or len(ref_no) > 50:
        return False

    # Allow alphanumeric, hyphens, underscores, slashes
    pattern = r"^[A-Za-z0-9\-_/]+$"
    return bool(re.match(pattern, ref_no))
