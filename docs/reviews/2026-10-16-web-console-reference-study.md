# Local Web console: reference study and design proposal

Status: research proposal; its visual/local direction was approved by the owner.
The [written W1 specification](../superpowers/specs/2026-10-16-local-web-console-design.md)
was approved by the owner and governs implementation scope; the implementation
plan is self-reviewed and awaits owner review.
Research date: 2026-10-16. The owner confirmed that each user will run Docker on
their own computer. Product code, dependencies and live endpoint results are unchanged.

## Intended outcome

Provide a local browser interface for target/model configuration, bounded live
execution, progress, investigation and optional exports. Preserve an independent
CLI that executes tests and writes reports without a running Web service. Both
interfaces must use the same planning, validation, evidence and report contracts.

## Primary references

| Reference | Documented behavior | Proposed adaptation |
| --- | --- | --- |
| [Promptfoo setup](https://www.promptfoo.dev/docs/getting-started/) and [self-hosting](https://www.promptfoo.dev/docs/usage/self-hosting/) | Browser setup guides provider/test configuration; Docker volumes persist local evaluation data. | Guided target and test selection, explicit persistent data directory. Do not adopt prompt-quality scoring as protocol compatibility. |
| [Inspect log viewer](https://inspect.aisi.org.uk/log-viewer.html) | Live sample completion, evaluation history, separate messages/scoring/metadata, and a self-contained viewer/log bundle. | Continue from live case progress into evidence-backed findings and history; offer an offline sharing package. Our standalone report must also open directly without a server. |
| [Postman Collection Runner](https://learning.postman.com/docs/tests-and-scripts/running-collections/intro-to-collection-runs/) | Live request/assertion results and run metadata; documented run export is desktop-only. | Link failed cases to precise assertions and responses. Our Web interface explicitly supports export rather than inheriting that limitation. |
| [Locust headless execution](https://docs.locust.io/en/stable/running-without-web-ui.html) | Headless execution, finite run time, shutdown handling and CI exit status. | Preserve CLI independence, bounded execution and explicit cancellation semantics. Do not turn this project into a load-testing dashboard. |

These observations come from official documentation, not an interactive browser
evaluation. No upstream implementation or styling was copied. The designs below
are project-specific recommendations, not features attributed to these tools.

## Approaches

1. **Recommended: a Python Web console over the existing engine.** FastAPI,
   server-rendered pages and small packaged browser modules provide forms,
   navigation and live updates. A persistent job service runs each assessment in
   a child process. This fits the Python package and keeps one deployment unit.
2. **A Streamlit-style application.** Useful for an exploratory interface, but
   durable jobs, evidence, reconnection and exports still need their own service
   boundaries. It saves initial form work without eliminating the main work.
3. **A separate full SPA and API.** Appropriate if a substantially richer workspace
   is needed later; currently adds frontend build, routing and state-management
   scope beyond the small set of necessary pages.

[FastAPI templates](https://fastapi.tiangolo.com/advanced/templates/) support the
first approach. [SSE](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
supports named events, event IDs and reconnection. Application-side persistence,
replay and deduplication remain our responsibility. Exact dependency versions and
browser tooling belong to a reviewed implementation plan.

## Proposed user flow

- **New assessment:** endpoint, model and authentication; immutable rule bundle,
  API date and beta set; concrete case groups and request/time limits. Show the
  effective Messages URL. Explain Docker host addressing without silently changing
  a user's loopback target. Save non-secret target presets if requested.
- **Plan preview:** validate locally without model requests. Display selected cases,
  unavailable groups, request limits and version identities. Starting the displayed
  plan is the explicit live opt-in. Changing configuration invalidates that plan.
  Optional connectivity or model discovery must be separate, explicit and budgeted.
- **Run detail:** show completed cases/total, actual requests/budget, current case,
  observed phase, elapsed time and last activity. Avoid invented time estimates or
  a token-count-based completion percentage. Distinguish pending from skipped and
  unknown. Allow cancellation and viewing already persisted case results.
- **Completed detail and history:** use the same run URL, with conclusions, scope,
  grouped issues, expected/actual evidence and references. Filter history by model,
  rule snapshot and time. Re-running creates a new plan and run; viewing does not.

Use a restrained white engineering style, readable typography, tables, small status
markers and progressive disclosure. Explain task behavior, strict protocol results
and client workflow outcomes separately. No composite compatibility score.
The owner subsequently requested stronger visual explanation and interaction.
The [visual-expression proposal](2026-10-16-visual-expression-design.md) adds matrices,
charts, linked detail views and equivalent offline/agent-readable representations.
Restrained styling must not reduce reports to prose with navigation links.

## Proposed execution and data boundaries

- CLI and HTTP are adapters over shared planning/execution/report services. Domain
  validators remain pure. Do not launch the CLI and parse its terminal prose.
- A single local service owns scheduling; default maximum active runs is one, with
  a bounded queue. Use worker processes to isolate the runner's existing main-thread
  signal handling. No Redis, distributed workers or Docker socket is required.
- Persist immutable plans, sanitized evidence, versioned results and ordered progress
  events in run directories on a Docker volume. SQLite indexes job lifecycle and
  history; it does not replace result/evidence truth. Commit event visibility only
  after the referenced artifacts are safely written.
- SSE sends sanitized operational events with monotonic IDs. Reconnection loads a
  snapshot and later events without restarting requests. Bound event volume; do not
  broadcast raw streamed model text or credentials by default.
- Job state (queued/running/cancelling/completed/cancelled/interrupted/error) is
  separate from existing compatibility statuses. A completed job can contain FAIL,
  BLOCKED or INDETERMINATE results. Pending cases never become PASS.
- Closing a browser does not cancel a run. Explicit cancellation stops new requests,
  interrupts the current request and retains partial evidence and case accounting.
  A service restart marks unfinished work interrupted; it must not silently resend
  upstream requests. A later run requires a new explicit start.

## Proposed reports, credentials and deployment

- Web runs always persist machine results and evidence; HTML/Markdown and sharing
  archives are generated on demand, without model calls. CLI retains automatic
  report output and existing exit-code semantics. Both use the same reader model.
- Offer HTML for reading, Markdown plus JSON for agents, and ZIP with reports,
  selected sanitized evidence, an explanation of scope/limitations, source links,
  versions and a file-hash manifest. Preview included data before export. Do not
  include credentials or imply that retained responses contain no private content.
- A derived shareable view must state omissions and preserve provenance; never
  rewrite original evidence or invalidate its hashes under the original identity.
- Default deployment publishes only to host loopback, with packaged assets and no
  CDN or telemetry dependency. Apply local session, Host/Origin and mutation-request
  protections. Shared remote use, user accounts and team permissions are separate
  scope, rather than a supported deployment of an unauthenticated local service.
- Browser-entered credentials are per-run server-memory data, never saved in browser
  storage, query strings, history, exports or SQLite. Deployment-provided secrets
  may be referenced by an explicit allowlist; the browser cannot enumerate arbitrary
  environment values. Queued work whose secret is lost requires re-entry.
- Provide a Web image target with the existing CLI and a `serve` command, while
  retaining the minimal CLI runtime target. Use one codebase and version; verify
  both image targets. Persist data through an explicit volume. Future client runners
  retain their own isolation and installation requirements.

## Scope and proposed acceptance

The shipped catalog still contains four Stage A cases. The private comprehensive
assessment is not a packaged test suite. A console must show the actual available
catalog and disabled/unavailable future capabilities, never label four cases as a
full compatibility certification. Productizing broader API cases, version matrices
and fixed client workflows needs separately reviewed contracts and synthetic controls.

Suggested sequence: shared execution events and lifecycle; complete local Web flow
and automatic CLI reports; then history/export hardening and broader test catalogs.
The first Web milestone is accepted against the shipped catalog, with its scope
visible. A broad-suite milestone must precede any advertised comprehensive mode.

Required verification includes CLI/Web result equivalence with synthetic peers;
event reconnection without duplicate requests; cancellation, worker crashes and
service restart accounting; lost-secret behavior; safe rendering of hostile target
text; export link/hash integrity; browser form and keyboard use; Docker volume
persistence and host access; and existing Python/schema/import gates. CI uses
synthetic endpoints by default. No implementation, browser acceptance, container
acceptance or new real-endpoint result is claimed by this proposal.
