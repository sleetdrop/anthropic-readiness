# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e
FROM ghcr.io/astral-sh/uv@sha256:4a1f3666816dafadd20ceb71eac9a7d56d7ef30279f7d64048519ab901ada336 AS uv
FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 AS base
COPY --from=uv /uv /uvx /usr/local/bin/
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_LINK_MODE=copy

FROM base AS dev
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 developer
ENV UV_PROJECT_ENVIRONMENT=/home/developer/.venv
USER developer
WORKDIR /workspaces/anthropic-readiness
CMD ["sleep", "infinity"]

FROM base AS build
ENV UV_PROJECT_ENVIRONMENT=/opt/build-venv UV_HTTP_TIMEOUT=600 UV_HTTP_RETRIES=5
WORKDIR /build
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --group build --no-install-project
COPY src ./src
RUN UV_OFFLINE=1 /opt/build-venv/bin/python -m hatchling build -t wheel \
    && UV_OFFLINE=1 UV_PROJECT_ENVIRONMENT=/opt/runtime-venv uv sync --locked --no-dev --no-install-project \
    && uv pip install --offline --no-deps --python /opt/runtime-venv/bin/python dist/*.whl \
    && uv pip check --python /opt/runtime-venv/bin/python

FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 AS runtime
ARG VCS_REF=unknown
LABEL org.opencontainers.image.title="Anthropic Readiness" \
      org.opencontainers.image.revision=$VCS_REF
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/opt/runtime-venv/bin:$PATH
COPY --from=build /opt/runtime-venv /opt/runtime-venv
RUN useradd --no-create-home --uid 10001 app && mkdir /work && chown app /work
USER app
WORKDIR /work
ENTRYPOINT ["anthropic-readiness"]
CMD ["--help"]
