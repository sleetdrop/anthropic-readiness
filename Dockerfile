# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e
FROM ghcr.io/astral-sh/uv@sha256:4a1f3666816dafadd20ceb71eac9a7d56d7ef30279f7d64048519ab901ada336 AS uv
FROM node:24.22.0-bookworm-slim@sha256:a5f4366e834695d5f363b920c104953a535d3a9864d1bdf74566a0ebe01daee5 AS node_toolchain
FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 AS base
COPY --from=uv /uv /uvx /usr/local/bin/
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_LINK_MODE=copy

FROM base AS dev
RUN printf 'Acquire::Retries "8";\nAcquire::http::Timeout "600";\nAcquire::https::Timeout "600";\n' > /etc/apt/apt.conf.d/80-readiness-network
COPY --from=node_toolchain /usr/local/bin/node /usr/local/bin/node
COPY --from=node_toolchain /usr/local/lib/node_modules/ /usr/local/lib/node_modules/
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 developer \
    && ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
WORKDIR /opt/frontend-preparation
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts \
    && npx --no-install playwright install-deps chromium \
    && rm -rf /opt/frontend-preparation
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

FROM build AS web_build
RUN UV_PROJECT_ENVIRONMENT=/opt/web-venv uv sync --locked --no-dev --extra web --no-install-project \
    && uv pip install --offline --no-deps --python /opt/web-venv/bin/python dist/*.whl \
    && uv pip check --python /opt/web-venv/bin/python

FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 AS runtime_base
ARG VCS_REF=unknown
ARG IMAGE_CONTEXT_SHA=unknown
LABEL org.opencontainers.image.title="Anthropic Readiness" \
      org.opencontainers.image.revision=$VCS_REF \
      io.anthropic-readiness.image-context=$IMAGE_CONTEXT_SHA
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --no-create-home --uid 10001 app && mkdir /work /data && chown app /work /data
USER app
WORKDIR /work

FROM runtime_base AS runtime
ENV PATH=/opt/runtime-venv/bin:$PATH
COPY --from=build /opt/runtime-venv /opt/runtime-venv
ENTRYPOINT ["anthropic-readiness"]
CMD ["--help"]

FROM runtime_base AS web
ENV PATH=/opt/web-venv/bin:$PATH
COPY --from=web_build /opt/web-venv /opt/web-venv
EXPOSE 8765
ENTRYPOINT ["anthropic-readiness"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8765", "--data-dir", "/data"]
