"""Server-rendered local pages expose real scope and preserve safe source meaning."""

from pathlib import Path

import httpx
import pytest

from tests.export_fixtures import prepared_run
from tests.http_server import SyntheticServer
from tests.web_fixtures import anyio_backend as anyio_backend
from tests.web_fixtures import client as client
from tests.web_fixtures import web_app as web_app

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def seeded_run(tmp_path: Path, request: pytest.FixtureRequest) -> str:
    scenario = getattr(request, "param", False)
    return prepared_run(
        tmp_path, partial=bool(scenario), keep_unpublished=scenario == "unpublished"
    )


async def test_page_renders_only_installed_capabilities(
    client: httpx.AsyncClient, server: SyntheticServer
) -> None:
    response = await client.get("/new")
    assert response.status_code == 200
    html = response.text
    for identifier in (
        "ANT-MESSAGE-001",
        "ANT-TEXT-SSE-001",
        "ANT-TEXT-SSE-002",
        "ANT-TOOL-FORCED-001",
    ):
        assert f'data-case-id="{identifier}"' in html
    assert html.count("data-case-id=") == 4
    assert "开始测试" in html
    assert "预览计划" in html
    assert 'type="password"' in html
    assert 'autocomplete="off"' in html
    assert "host.docker.internal" in html
    assert "完整工具闭环" in html
    assert not server.requests
    assert (await client.get("/history")).status_code == 200
    assert (await client.get("/assets/web/app.js")).status_code == 200
    assert (await client.get("/assets/..%2F..%2Fpyproject.toml")).status_code == 404


@pytest.mark.parametrize("seeded_run", [True], indirect=True)
async def test_partial_page_is_distinct_and_does_not_export_automatically(
    client: httpx.AsyncClient, tmp_path: Path, seeded_run: str
) -> None:
    run_id = seeded_run
    response = await client.get("/runs/" + run_id)
    assert response.status_code == 200
    assert "部分记录" in response.text
    assert "已中断" in response.text
    assert "导出" in response.text
    assert not (tmp_path / "runs" / run_id / "exports").exists()
    rerun = await client.get("/new", params={"copy": run_id})
    assert rerun.status_code == 200
    assert "重新预览" in rerun.text


async def test_history_exposes_frozen_rule_identity_and_filters(
    client: httpx.AsyncClient, tmp_path: Path, seeded_run: str
) -> None:
    run_id = seeded_run
    await client.get("/api/v1/session")
    response = await client.get("/api/v1/runs", params={"contract_revision": "1.0.0"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["api_version"] == "2023-06-01"
    assert items[0]["contract_revision"] == "1.0.0"
    assert items[0]["beta_headers"] == []
    assert (await client.get("/api/v1/runs", params={"contract_revision": "uninstalled"})).json()[
        "items"
    ] == []
    html = (await client.get("/history")).text
    assert run_id in html
    assert "2023-06-01" in html
    assert "1.0.0" in html
    assert "复制配置" in html
    assert not list((tmp_path / "runs").glob("*/exports"))


@pytest.mark.parametrize("seeded_run", ["unpublished"], indirect=True)
async def test_interrupted_checkpoint_is_recovered_as_browsable_evidence(
    client: httpx.AsyncClient, seeded_run: str
) -> None:
    await client.get("/api/v1/session")
    response = await client.get("/api/v1/runs/" + seeded_run)
    assert response.status_code == 200
    paths = [item["path"] for item in response.json()["evidence"]]
    assert any("ANT-MESSAGE-001" in path for path in paths)
    assert any("ANT-TEXT-SSE-001" in path for path in paths)
    assert response.json()["report"]["summary"]["completed_cases"] == 2
    assert any("恢复" in note for note in response.json()["report"]["limitations"])
