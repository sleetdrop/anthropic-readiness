"""Single-worker optional server entry; no process starts during import."""

from pathlib import Path

import uvicorn

from anthropic_readiness.web.app import create_app
from anthropic_readiness.web.settings import WebSettings


def serve(data_root: Path, settings: WebSettings) -> int:
    uvicorn.run(
        create_app(data_root=data_root, settings=settings),
        host=settings.host,
        port=settings.port,
        workers=1,
        proxy_headers=False,
        server_header=False,
        access_log=False,
        log_level="warning",
    )
    return 0
