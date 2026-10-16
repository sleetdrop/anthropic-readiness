# Architecture

The CLI selects an immutable contract and explicit case plan before any request.
Four versioned cases feed a sequential runner. Transport enforces absolute
budgets, response limits, TLS verification, no redirects and no implicit retries.
Evidence is sanitized in memory before exclusive atomic writes. Replay consumes
verified persisted captures without network access. Reports expose scope,
non-PASS assertions, missing coverage and a versioned offline reader guide.

## Dependency direction

`cli` → `runner` / `reporting` → adapters and cases → `config` →
`schema` / stream validation → message validation → pure JSON validation /
SSE framing → `models`. Import Linter enforces these layers and forbids pure
modules from importing adapters, filesystem/resource loaders, HTTP or YAML.
`schema` loads packaged resources; `json_validation` performs pure offline
validation and rejects external references. No validation fetches a remote schema.

JSON Schema governs shape; relational validation governs required case/profile
membership, assertion accounting and aggregates. Evidence hashes and relative
pointers are verified independently. The five statuses preserve uncertainty:
FAIL is an observed defect; INCONCLUSIVE, BLOCKED and NOT_RUN cannot prove support.

## Scope and provenance

The first core bundle fixes API version, empty beta set, rule sources and fixture
hashes. It tests a subset, not the whole vendor protocol. API dates, beta headers,
rule revision, SDK/CLI versions and actual model behavior are distinct axes.
Later stages add matrices, tool loops, client workflows and reviewed protocol
maintenance; current reports must not imply they already exist.

The harness checks source, schemas, synthetic behavior, installed packaging and
collaboration definitions. Image acceptance, visual review, independent review,
remote CI and real endpoint outcomes are distinct evidence. See the
[acceptance map](harness/acceptance.json) and [progress record](harness/progress.md).
