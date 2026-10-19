"""
Synthetic Behavioral Event Stream Fixtures for Phase 2 Testing.

Provides deterministic, reproducible in-memory event sequences for unit testing:
1. Sparse modality windows (pure mouse, pure keyboard, pure scroll).
2. Boundary test cases (short <30 event sessions, fractional trailing events).
3. Mock multi-participant sessions for testing 4-fold grouped CV and freeze gates.

CRITICAL: These fixtures are strictly used in automated testing and do NOT represent
genuine human empirical sessions.
"""

from typing import List, Dict, Any


def make_mouse_event(ts: int, x: float, y: float, v: float = 500.0, a: float = 1000.0, dc: float = 6.0) -> Dict[str, Any]:
    """Creates a standardized mouse_move behavioral event dictionary."""
    return {
        "event_type": "mouse_move",
        "client_timestamp": ts,
        "event_data": {
            "x": x,
            "y": y,
            "distance_px": 15.0,
            "time_delta_ms": 30.0,
            "velocity_px_s": v,
            "acceleration_px_s2": a,
            "angle_degrees": 45.0,
            "direction_change_deg": dc,
        },
    }


def make_click_event(ts: int, x: float = 200.0, y: float = 300.0, category: str = "button") -> Dict[str, Any]:
    """Creates a standardized mouse_click behavioral event dictionary."""
    return {
        "event_type": "mouse_click",
        "client_timestamp": ts,
        "event_data": {
            "x": x,
            "y": y,
            "button": 0,
            "click_type": "single",
            "time_since_last_click_ms": 250.0,
            "target_category": category,
        },
    }


def make_key_event(ts: int, dwell: float = 85.0, flight: float = 120.0) -> Dict[str, Any]:
    """Creates a standardized key_meta behavioral event dictionary."""
    return {
        "event_type": "key_meta",
        "client_timestamp": ts,
        "event_data": {
            "dwell_ms": dwell,
            "flight_ms": flight,
            "inter_key_interval_ms": dwell + flight,
            "is_backspace": False,
            "is_paste": False,
        },
    }


def make_scroll_event(ts: int, dy: float = 120.0, v: float = 400.0) -> Dict[str, Any]:
    """Creates a standardized scroll behavioral event dictionary."""
    return {
        "event_type": "scroll",
        "client_timestamp": ts,
        "event_data": {
            "delta_x": 0.0,
            "delta_y": dy,
            "direction": "down" if dy > 0 else "up",
            "velocity_px_s": v,
            "time_since_last_scroll_ms": 50.0,
        },
    }


# ==============================================================================
# Fixture Generators for Specific Modality & Boundary Scenarios
# ==============================================================================

def get_pure_mouse_window_fixture(n_events: int = 30, base_ts: int = 1000) -> List[Dict[str, Any]]:
    """Returns exactly 30 mouse_move events with zero clicks, keystrokes, or scrolls."""
    events = []
    for i in range(n_events):
        events.append(make_mouse_event(
            ts=base_ts + i * 33,
            x=100.0 + i * 10,
            y=150.0 + (i % 5) * 8,
            v=450.0 + (i % 3) * 50,
            a=900.0 + (i % 2) * 200,
            dc=8.0 if i % 4 == 0 else 2.0,
        ))
    return events


def get_pure_keyboard_window_fixture(n_events: int = 30, base_ts: int = 1000) -> List[Dict[str, Any]]:
    """Returns exactly 30 key_meta events with zero mouse movement, clicks, or scrolls."""
    events = []
    for i in range(n_events):
        events.append(make_key_event(
            ts=base_ts + i * 150,
            dwell=70.0 + (i % 5) * 10,
            flight=100.0 + (i % 4) * 20,
        ))
    return events


def get_pure_scroll_window_fixture(n_events: int = 30, base_ts: int = 1000) -> List[Dict[str, Any]]:
    """Returns exactly 30 scroll events with zero mouse movement, clicks, or keys."""
    events = []
    for i in range(n_events):
        events.append(make_scroll_event(
            ts=base_ts + i * 50,
            dy=-120.0 if i < 15 else 120.0,
            v=350.0 + (i % 5) * 40,
        ))
    return events


def get_mixed_modality_stream_fixture(n_events: int = 60, base_ts: int = 1000) -> List[Dict[str, Any]]:
    """
    Returns a 60-event stream with mixed mouse, clicks, keys, and scrolls.
    At W=30, S=15, this should yield exactly 3 sliding windows:
    Window 1: events 0–29
    Window 2: events 15–44
    Window 3: events 30–59
    """
    events = []
    for i in range(n_events):
        mod = i % 10
        ts = base_ts + i * 40
        if mod in (0, 1, 2, 3, 4, 5):
            events.append(make_mouse_event(ts, x=50.0 + i * 5, y=80.0 + (i % 6) * 4))
        elif mod in (6, 7):
            events.append(make_click_event(ts, category="button" if mod == 6 else "link"))
        elif mod == 8:
            events.append(make_key_event(ts))
        else:
            events.append(make_scroll_event(ts))
    return events


def get_insufficient_events_fixture() -> List[Dict[str, Any]]:
    """Returns 20 events (<30 window size), which must yield zero valid windows."""
    return get_pure_mouse_window_fixture(n_events=20)


def get_trailing_events_stream_fixture() -> List[Dict[str, Any]]:
    """
    Returns 52 events.
    At W=30, S=15:
    Window 1: events 0–29
    Window 2: events 15–44
    Remaining 7 events (45–51): must be dropped (not yield a 3rd window).
    """
    return get_mixed_modality_stream_fixture(n_events=52)


def get_mock_multi_participant_dataset() -> List[Dict[str, Any]]:
    """
    Constructs a mock dataset of 20 development sessions (across H1..H4 and B1..B4)
    and 10 held-out sessions (across H5..H6 and B5..B6).
    Each session contains a 60-event stream yielding 3 windows.
    Strictly for unit testing fold isolation, freeze manifest, and aggregation logic.
    """
    sessions = []
    
    # 1. Development Human (H1..H4: 5 sessions each = 20 sessions)
    for p_idx, p_id in enumerate(["H1", "H2", "H3", "H4"]):
        for s_idx in range(5):
            sessions.append({
                "session_id": f"sess_mock_{p_id}_{s_idx}",
                "participant_id": p_id,
                "label": 0,
                "task_id": "TASK_01" if s_idx < 2 else ("TASK_02" if s_idx < 4 else "TASK_03"),
                "partition": "DEVELOPMENT",
                "events": get_mixed_modality_stream_fixture(n_events=60, base_ts=1000 + p_idx * 10000 + s_idx * 5000),
            })
            
    # 2. Development Bot M1 (B1..B4: 5 sessions each = 20 sessions)
    for b_idx, b_id in enumerate(["B1", "B2", "B3", "B4"]):
        for s_idx in range(5):
            sessions.append({
                "session_id": f"sess_mock_{b_id}_{s_idx}",
                "participant_id": b_id,
                "label": 1,
                "task_id": "TASK_01" if s_idx < 2 else ("TASK_02" if s_idx < 4 else "TASK_03"),
                "partition": "DEVELOPMENT",
                "events": get_pure_mouse_window_fixture(n_events=60, base_ts=50000 + b_idx * 10000 + s_idx * 5000),
            })

    # 3. Held-Out Human (H5, H6: 5 sessions each = 10 sessions)
    for p_idx, p_id in enumerate(["H5", "H6"]):
        for s_idx in range(5):
            sessions.append({
                "session_id": f"sess_mock_{p_id}_{s_idx}",
                "participant_id": p_id,
                "label": 0,
                "task_id": "TASK_01" if s_idx < 2 else ("TASK_02" if s_idx < 3 else "TASK_03"),
                "partition": "HELD_OUT",
                "events": get_mixed_modality_stream_fixture(n_events=60, base_ts=100000 + p_idx * 10000 + s_idx * 5000),
            })

    # 4. Held-Out Bot M1 (B5, B6: 5 sessions each = 10 sessions)
    for b_idx, b_id in enumerate(["B5", "B6"]):
        for s_idx in range(5):
            sessions.append({
                "session_id": f"sess_mock_{b_id}_{s_idx}",
                "participant_id": b_id,
                "label": 1,
                "task_id": "TASK_01" if s_idx < 2 else ("TASK_02" if s_idx < 3 else "TASK_03"),
                "partition": "HELD_OUT",
                "events": get_pure_mouse_window_fixture(n_events=60, base_ts=150000 + b_idx * 10000 + s_idx * 5000),
            })

    # 5. Quarantined Method 2 Bot Fixture (M2: 5 sessions)
    for s_idx in range(5):
        sessions.append({
            "session_id": f"sess_mock_M2_{s_idx}",
            "participant_id": "M2_AGENT",
            "label": 1,
            "task_id": "TASK_01",
            "partition": "METHOD_2_QUARANTINE",
            "events": get_mixed_modality_stream_fixture(n_events=60, base_ts=200000 + s_idx * 5000),
        })

    return sessions
