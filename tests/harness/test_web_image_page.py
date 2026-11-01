"""Image UI inventory follows the shipped catalog, independently of execution scope."""

import pytest

from anthropic_readiness.cases import list_cases
from scripts import web_image_checks

CASE_IDS = (
    "ANT-MESSAGE-001",
    "ANT-TEXT-SSE-001",
    "ANT-TEXT-SSE-002",
    "ANT-TOOL-FORCED-001",
    "ANT-TOOL-LOOP-001",
)


def page(
    case_ids: tuple[str, ...] = CASE_IDS,
    button: str = '<button id="preview-button" type="submit">Check configuration</button>',
) -> str:
    return (
        "<ul>"
        + "".join(f'<li data-case-id="{case_id}"></li>' for case_id in case_ids)
        + "</ul>"
        + button
    )


def test_shipped_catalog_and_semantic_preview_control_are_verified() -> None:
    web_image_checks.verify_web_page(page(), CASE_IDS)
    web_image_checks.verify_web_page(
        page(button='<button type="submit" id="preview-button">检查配置</button>'), CASE_IDS
    )


def test_image_inventory_tracks_the_versioned_source_catalog() -> None:
    assert set(web_image_checks.EXPECTED_WEB_CASE_IDS) == {case.id for case in list_cases()}
    assert web_image_checks.EXPECTED_WEB_CASE_IDS == CASE_IDS


@pytest.mark.parametrize(
    "bad_page",
    [
        page(CASE_IDS[:-1]),
        page((*CASE_IDS, "ANT-UNSHIPPED-001")),
        page((*CASE_IDS[:-1], CASE_IDS[0])),
        page(button=""),
        page(button='<div id="preview-button">Check configuration</div>'),
        page(button='<button type="button" id="preview-button">Check configuration</button>'),
        page(
            button='<button type="submit" id="preview-button" disabled>Check configuration</button>'
        ),
        page(
            button='<button type="submit" id="preview-button">Check</button><button id="preview-button" type="submit">Duplicate</button>'
        ),
    ],
)
def test_missing_extra_duplicate_cases_and_invalid_preview_controls_fail(bad_page: str) -> None:
    with pytest.raises(RuntimeError, match="web_page_scope"):
        web_image_checks.verify_web_page(bad_page, CASE_IDS)
