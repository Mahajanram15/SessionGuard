"""
CrossTrace Phase 2: Telemetry Privacy & PII Schema Validator.

Guarantees:
1. Strictly rejects raw keystroke identities, key codes, and typed character values (key, code, value, text, keyCode, which).
2. Forbids interactions with password or credential fields (target_type == "password").
3. Validates that only privacy-safe kinematic event types and structural metadata are processed.
"""

from typing import Dict, Any, List, Set, Optional


class PrivacyViolationError(ValueError):
    """Raised when an event contains sensitive or forbidden PII/keystroke metadata."""
    pass


# Permitted top-level telemetry event fields
PERMITTED_TELEMETRY_FIELDS: Set[str] = {
    "event_type",
    "client_timestamp",
    "x",
    "y",
    "delta_x",
    "delta_y",
    "target_tag",
    "target_type",
    "session_id",
    "viewport_width",
    "viewport_height",
    "is_trusted",
}

# Categorically forbidden fields that could leak user text or passwords
FORBIDDEN_PII_FIELDS: Set[str] = {
    "key",
    "code",
    "value",
    "text",
    "inputValue",
    "input_value",
    "keyCode",
    "which",
    "char",
    "charCode",
    "password",
    "secret",
}

# Permitted event categories
PERMITTED_EVENT_TYPES: Set[str] = {
    "keydown",
    "keyup",
    "mousemove",
    "mousedown",
    "mouseup",
    "click",
    "wheel",
    "scroll",
}


def validate_event_privacy(event: Dict[str, Any], event_index: Optional[int] = None) -> None:
    """
    Validates a single behavioral telemetry event dictionary against strict privacy rules.

    Raises:
        PrivacyViolationError: If forbidden PII or typed key identifiers are present.
    """
    if not isinstance(event, dict):
        raise PrivacyViolationError(f"Event at index {event_index} must be a dictionary, got {type(event)}")

    # Check for forbidden fields
    event_keys = set(event.keys())
    forbidden_present = event_keys.intersection(FORBIDDEN_PII_FIELDS)
    if forbidden_present:
        idx_str = f" at index {event_index}" if event_index is not None else ""
        raise PrivacyViolationError(
            f"Privacy Violation{idx_str}: Forbidden keystroke or PII fields detected: {sorted(list(forbidden_present))}"
        )

    # Check for unauthorized fields outside permitted schema
    unauthorized = event_keys - PERMITTED_TELEMETRY_FIELDS
    if unauthorized:
        idx_str = f" at index {event_index}" if event_index is not None else ""
        raise PrivacyViolationError(
            f"Privacy Violation{idx_str}: Unauthorized fields outside telemetry schema: {sorted(list(unauthorized))}"
        )

    # Check event_type validity
    etype = event.get("event_type")
    if etype not in PERMITTED_EVENT_TYPES:
        idx_str = f" at index {event_index}" if event_index is not None else ""
        raise PrivacyViolationError(
            f"Privacy Violation{idx_str}: Unrecognized or forbidden event_type '{etype}'"
        )

    # Forbid password inputs
    target_type = str(event.get("target_type", "")).lower()
    if target_type == "password":
        idx_str = f" at index {event_index}" if event_index is not None else ""
        raise PrivacyViolationError(
            f"Privacy Violation{idx_str}: Interaction with sensitive password input is strictly forbidden."
        )


def validate_session_events_privacy(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validates an entire session event stream.
    Returns audit summary if all events pass, or raises PrivacyViolationError immediately.
    """
    if not events:
        return {"total_events": 0, "privacy_passed": True}

    for idx, ev in enumerate(events):
        validate_event_privacy(ev, event_index=idx)

    return {
        "total_events": len(events),
        "privacy_passed": True,
        "audited_categories": sorted(list(set(ev.get("event_type") for ev in events))),
    }
