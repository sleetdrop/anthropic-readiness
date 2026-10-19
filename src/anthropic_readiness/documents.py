"""Pure document composition; source assertions and counts remain authoritative."""

import hashlib
import json
from copy import deepcopy

from anthropic_readiness.diagnostics.models import Comparison, DocumentView
from anthropic_readiness.models import JsonObject, JsonValue, object_value
from anthropic_readiness.presentation import DEFAULT_PRESENTATION, PresentationOptions
from anthropic_readiness.report_models import ReportSource
from anthropic_readiness.report_view import build_report_view, objects

# Credential references are omitted by field, never by global word replacement;
# a reference can legitimately equal a verdict or part of a model name.
PRIVATE_KEYS = frozenset({"messages_url", "credential_env", "auth", "authorization", "endpoint"})


def _private_values(value: JsonValue) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"messages_url", "endpoint"} and isinstance(item, str) and item:
                found.add(item)
            found.update(_private_values(item))
        if str(value.get("field", value.get("path", ""))).split(".")[-1] in {
            "messages_url",
            "endpoint",
        }:
            for key in ("before", "after"):
                item = value.get(key)
                if isinstance(item, str) and item:
                    found.add(item)
    elif isinstance(value, list):
        for item in value:
            found.update(_private_values(item))
    return found


def _sanitize(value: JsonValue, private: set[str]) -> JsonValue:
    if isinstance(value, dict):
        result = {
            key: _sanitize(item, private) for key, item in value.items() if key not in PRIVATE_KEYS
        }
        if str(value.get("field", value.get("path", ""))).split(".")[-1] in {
            "credential_env",
            "authorization",
        }:
            for key in ("before", "after"):
                if key in result:
                    result[key] = "[omitted]"
        return result
    if isinstance(value, list):
        return [_sanitize(item, private) for item in value]
    if isinstance(value, str):
        for item in sorted(private, key=len, reverse=True):
            value = value.replace(item, "[omitted]")
    return value


def build_document_view(
    source: ReportSource,
    *,
    comparison: Comparison | None = None,
    presentation: PresentationOptions = DEFAULT_PRESENTATION,
) -> DocumentView:
    if source.result is not None and source.result_sha256 is None:
        raise ValueError("document_source_identity_required")
    facts = build_report_view(source).document
    # An operational execution embeds the full target schema. It is not part of
    # the document body; recorded aggregate times remain in summary/attempts.
    facts["execution"] = None
    facts["figures"] = [
        item
        for item in objects(facts["figures"])
        if item["kind"] in {"matrix", "impact", "distribution"}
    ]
    value: JsonObject = {
        "schema_version": "1.0",
        "presentation_version": "3.0",
        "presentation": presentation.to_json(),
        "available_locales": ["zh-CN", "en"],
        "facts": facts,
        "comparison": deepcopy(comparison.document) if comparison else None,
        "source": {
            "run_id": facts["run_id"],
            "assessment_id": source.result.assessment_id if source.result else None,
            "result_sha256": source.result_sha256,
            "checkpoint_sha256": hashlib.sha256(
                json.dumps(
                    list(source.checkpoint_inventory or ()),
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    allow_nan=False,
                ).encode()
            ).hexdigest()
            if source.result is None
            else None,
            "recipe_sha256": None,
            "context_sha256": None,
        },
    }
    if comparison is not None:
        after = object_value(comparison.document["after"])
        identity = object_value(value["source"])
        if any(
            after[key] != identity[key]
            for key in ("run_id", "assessment_id", "result_sha256", "checkpoint_sha256")
        ):
            raise ValueError("document_comparison_source_mismatch")
        value["source"] = deepcopy(after)
    private = _private_values(value)

    return DocumentView(object_value(_sanitize(value, private)))


def group_observations(observations: list[JsonObject]) -> list[JsonObject]:
    """Share identical excerpts while retaining every original evidence member."""
    buckets: dict[str, list[JsonObject]] = {}
    for observation in observations:
        key = json.dumps(
            [observation.get("expected_excerpt"), observation.get("actual_excerpt")],
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        buckets.setdefault(key, []).append(observation)
    groups: list[JsonObject] = []
    for members in buckets.values():
        case_ids: list[JsonValue] = []
        case_ids.extend(sorted({str(member["case_id"]) for member in members}))
        rows: list[JsonValue] = [deepcopy(member) for member in members]
        groups.append(
            {
                "expected_excerpt": members[0].get("expected_excerpt"),
                "actual_excerpt": members[0].get("actual_excerpt"),
                "case_ids": case_ids,
                "observations": rows,
            }
        )
    return groups
