"""Pure authoritative membership and assertion requirements for shipped cases."""

from anthropic_readiness.models import JsonValue

SUPPORTED = (("anthropic-messages-2023-06-01-core", "1.0.0"),)
PROFILE_CASES = {
    "anthropic-basic": ("ANT-MESSAGE-001", "ANT-TEXT-SSE-001", "ANT-TEXT-SSE-002"),
    "anthropic-tools-smoke": ("ANT-TOOL-FORCED-001",),
}
CASE_IDS = frozenset(case for cases in PROFILE_CASES.values() for case in cases)


def assertion_plan(case_id: str, model_required: bool) -> list[JsonValue]:
    if case_id not in CASE_IDS:
        raise ValueError("unsupported_case")
    ids = [
        "HTTP-STATUS",
        "HTTP-CONTENT-TYPE",
        "CAPTURE-COMPLETE",
        "MSG-CORE",
        "MSG-MODEL",
        "MSG-STOP",
        "MSG-STOP-SEQUENCE",
        "TASK-COMPLETE",
    ]
    ids.extend(
        [
            "SSE-FRAMING",
            "STR-JSON",
            "STR-TYPE",
            "STR-LIFECYCLE",
            "STR-START",
            "STR-DELTA",
            "STR-STOP",
        ]
        if case_id.startswith("ANT-TEXT-SSE-")
        else ["MSG-JSON"]
    )
    if case_id == "ANT-TOOL-FORCED-001":
        ids.extend(["MSG-TOOL-CALLS", "MSG-TOOL-ID", "MSG-TOOL-NAME", "MSG-TOOL-INPUT"])
    return [
        {"id": key, "version": 1, "required": key != "MSG-MODEL" or model_required} for key in ids
    ]
