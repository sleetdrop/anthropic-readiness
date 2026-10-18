"""Synthetic structural documents, not evidence-verified or executable baselines."""

from copy import deepcopy

from anthropic_readiness.models import JsonObject
from anthropic_readiness.report_view import build_report_view
from tests.unit.test_report_view import source

RUN_ID = "11111111-1111-4111-8111-111111111111"
OTHER_ID = "22222222-2222-4222-8222-222222222222"
SHA = "a" * 64
OTHER_SHA = "b" * 64
TIME = "2026-10-18T12:00:00Z"


def contract_documents() -> dict[str, JsonObject]:
    identity: JsonObject = {
        "schema_version": "1.0",
        "semantic_revision": "1",
        "python": {"implementation": "CPython", "version": "3.12"},
        "file_hashes": {"validation/messages.py": SHA},
        "dependencies": {"httpx": "0.28.1"},
        "content_sha256": SHA,
    }
    check: JsonObject = {"id": "MSG-CORE", "version": 1, "category": "protocol", "required": True}
    recipe: JsonObject = {
        "schema_version": "1.0",
        "content_sha256": SHA,
        "implementation": identity,
        "contract": {"id": "messages-core", "revision": "1.0.0", "content_sha256": SHA},
        "protocol": {"name": "anthropic.messages", "api_version": "2023-06-01", "beta_headers": []},
        "model": {"requested": "synthetic-model", "policy": "request_or_alias", "aliases": []},
        "capabilities": {"streaming": True, "tools": True},
        "limits": {
            "connect_timeout_s": 5,
            "read_timeout_s": 30,
            "attempt_timeout_s": 90,
            "run_timeout_s": 300,
            "max_response_bytes": 4194304,
            "max_event_bytes": 262144,
            "max_events": 10000,
            "max_requests": 4,
            "max_tokens": 512,
        },
        "profiles": [{"id": "anthropic-basic", "version": 1, "cases": ["ANT-MESSAGE-001"]}],
        "cases": [{"id": "ANT-MESSAGE-001", "version": 1, "required": True, "assertions": [check]}],
        "requests": [
            {
                "case_id": "ANT-MESSAGE-001",
                "method": "POST",
                "headers": {"anthropic-version": "2023-06-01"},
                "body": {"model": "synthetic-model", "messages": []},
                "streaming": False,
                "sha256": SHA,
            }
        ],
        "repeat": 1,
        "retry": 0,
    }
    source_identity: JsonObject = {
        "run_id": RUN_ID,
        "assessment_id": "synthetic-assessment",
        "result_sha256": SHA,
        "checkpoint_sha256": None,
        "recipe_sha256": SHA,
        "context_sha256": SHA,
    }
    context: JsonObject = {
        "schema_version": "1.0",
        "run_id": RUN_ID,
        "plan_sha256": SHA,
        "config_sha256": SHA,
        "recipe": recipe,
        "recipe_sha256": SHA,
        "baseline": None,
        "declared_changes": [],
    }
    file: JsonObject = {"path": "result.json", "sha256": SHA, "bytes": 10}
    evidence: JsonObject = {"status": "verified", "errors": [], "delivery": "external_files"}
    package: JsonObject = {
        "schema_version": "1.0",
        "source": source_identity,
        "partial": False,
        "recipe": {"path": "retest-recipe.json", "sha256": SHA},
        "context": {"path": "assessment-context.json", "sha256": SHA},
        "files": [file],
        "omissions": [],
        "evidence_verification": evidence,
    }
    baseline: JsonObject = {
        "schema_version": "1.0",
        "id": OTHER_ID,
        "archive_sha256": OTHER_SHA,
        "source": source_identity,
        "imported_at": TIME,
        "artifact_root": "baselines/" + OTHER_ID,
        "eligibility": {"read": True, "retest": True, "compare": True, "reasons": []},
        "evidence_verification": evidence,
    }
    pair: JsonObject = {
        "case_id": "ANT-MESSAGE-001",
        "assertion_id": "MSG-CORE",
        "assertion_version": 1,
        "category": "protocol",
        "required": True,
        "before": "FAIL",
        "after": "PASS",
        "transition": "recovered",
        "before_reason": "missing_core_field",
        "after_reason": "core_fields_present",
        "before_expected": "stop_sequence is present",
        "before_actual": "stop_sequence is missing",
        "after_expected": "stop_sequence is present",
        "after_actual": "stop_sequence is null",
        "before_evidence": [],
        "after_evidence": [],
    }
    comparison: JsonObject = {
        "schema_version": "1.0",
        "before": source_identity,
        "after": {**source_identity, "run_id": OTHER_ID, "result_sha256": OTHER_SHA},
        "comparable": True,
        "reasons": [],
        "condition_changes": [],
        "pairs": [pair],
        "unmatched_before": [],
        "unmatched_after": [],
        "coverage": {
            "before_checks": 1,
            "after_checks": 1,
            "matched_checks": 1,
            "missing_required_checks": 0,
            "before_cases": 1,
            "after_cases": 1,
            "matched_cases": 1,
            "missing_required_cases": 0,
        },
        "summary": {
            "unit": "checks",
            "recovered": 1,
            "persistent": 0,
            "new_failure": 0,
            "passed_both": 0,
            "gap": 0,
            "newly_evaluated": 0,
            "incomparable": 0,
        },
        "all_previous_failures_passed": True,
    }
    presentation: JsonObject = {"schema_version": "1.0", "locale": "zh-CN", "theme": "system"}
    facts = build_report_view(source()).document
    workbench: JsonObject = {
        "schema_version": "1.0",
        "presentation_version": "1.0",
        "presentation": presentation,
        "facts": facts,
        "generation": "synthetic-generation",
        "available_locales": ["zh-CN", "en"],
        "job": None,
        "worker": {"state": "not_running", "observed_at": TIME},
        "comparison": None,
        "baseline": None,
    }
    document: JsonObject = {
        "schema_version": "1.0",
        "presentation_version": "3.0",
        "presentation": presentation,
        "available_locales": ["zh-CN", "en"],
        "facts": facts,
        "comparison": None,
        "source": source_identity,
    }
    manifest: JsonObject = {
        "schema_version": "2.0",
        "export_id": OTHER_ID,
        "run_id": RUN_ID,
        "created_at": TIME,
        "presentation_version": "3.0",
        "presentation": presentation,
        "source_result_sha256": SHA,
        "partial": False,
        "formats": ["html", "markdown", "json", "zip"],
        "include_evidence": True,
        "files": [file],
        "omissions": [],
        "evidence_verification": evidence,
    }
    return deepcopy(
        {
            "implementation-identity": identity,
            "retest-recipe": recipe,
            "assessment-context": context,
            "diagnostic-package": package,
            "imported-baseline": baseline,
            "comparison": comparison,
            "workbench-view": workbench,
            "document-view": document,
            "export-manifest-v2": manifest,
        }
    )
