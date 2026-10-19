"""
CrossTrace Phase 2: Telemetry Privacy & PII Schema Validator.

Guarantees:
1. Strictly rejects raw keystroke identities, key codes, and typed character values (key, code, value, text, keyCode, which).
2. Forbids interactions with password or credential fields (target_type == "password").
3. Validates both flat and nested (event_data) telemetry payloads.
4. Recursively scans dictionaries without ever logging or leaking sensitive user values.
"""

from typing import Dict, Any, List, Set, Optional


class PrivacyViolationError(ValueError):
    """Raised when an event contains sensitive or forbidden PII/keystroke metadata."""
    pass


# Permitted top-level telemetry event fields
PERMITTED_TELEMETRY_FIELDS: Set[str] = {
    "event_type",
    "client_timestamp",
    "server_timestamp",
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
    "event_data",
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

# Permitted event categories across client SDK and backend schemas
PERMITTED_EVENT_TYPES: Set[str] = {
    "keydown",
    "keyup",
    "mousemove",
    "mousedown",
    "mouseup",
    "click",
    "wheel",
    "scroll",
    "mouse_move",
    "mouse_click",
    "key_meta",
    "navigation",
    "visibility",
}


def _scan_for_forbidden_keys(data: Any, path: str = "") -> None:
    """
    Recursively scans nested dictionaries/lists for forbidden PII keys or password targets.
    Never outputs sensitive values into exception messages.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            k_lower = str(k).strip()
            if k_lower in FORBIDDEN_PII_FIELDS:
                loc = f" at '{path}.{k}'" if path else f" '{k}'"
                raise PrivacyViolationError(
                    f"Privacy Violation: Forbidden keystroke or PII field detected{loc}."
                )

            # Check target_type
            if k_lower == "target_type" and str(v).strip().lower() == "password":
                raise PrivacyViolationError(
                    "Privacy Violation: Interaction with sensitive password input is strictly forbidden."
                )

            _scan_for_forbidden_keys(v, path=f"{path}.{k}" if path else str(k))
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            _scan_for_forbidden_keys(item, path=f"{path}[{idx}]")


def validate_event_privacy(event: Dict[str, Any], event_index: Optional[int] = None) -> None:
    """
    Validates a single behavioral telemetry event dictionary against strict privacy rules.
    Supports both flat event streams and backend event_data nested objects.

    Raises:
        PrivacyViolationError: If forbidden PII or typed key identifiers are present.
    """
    if not isinstance(event, dict):
        raise PrivacyViolationError(f"Event at index {event_index} must be a dictionary, got {type(event)}")

    # 1. Check top-level schema fields
    event_keys = set(event.keys())
    unauthorized = event_keys - PERMITTED_TELEMETRY_FIELDS
    if unauthorized:
        idx_str = f" at index {event_index}" if event_index is not None else ""
        raise PrivacyViolationError(
            f"Privacy Violation{idx_str}: Unauthorized fields outside telemetry schema: {sorted(list(unauthorized))}"
        )

    # 2. Check event_type validity
    etype = event.get("event_type")
    if etype not in PERMITTED_EVENT_TYPES:
        idx_str = f" at index {event_index}" if event_index is not None else ""
        raise PrivacyViolationError(
            f"Privacy Violation{idx_str}: Unrecognized or forbidden event_type '{etype}'"
        )

    # 3. Recursive scan for forbidden fields (covers top-level and nested event_data)
    _scan_for_forbidden_keys(event)


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
