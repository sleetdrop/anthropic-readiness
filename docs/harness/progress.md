# Verification record

## 2026-11-05 — Saved count-token record inspection

Fixed follow-up finding R5. The record adapter preserves `route: "count_tokens"`
and dispatches JSON to the existing auxiliary response validator. A valid
`{"input_tokens":42}` capture now passes with no findings; a string token count
fails at `/input_tokens`; and a valid-looking body from a non-EOF capture stays
INDETERMINATE. Normal Message records continue to pass, and unsupported route
values are rejected by the adapter.

The new count-token regression first failed before the code change: its normal
control was reported as a Message protocol failure. It passes after the fix.
The original retained count-token and normal-Message records were also
inspected directly; both returned PASS. Node `v24.22.2`: `npm run check` passed
all 82 tests, with no skipped, cancelled or TODO tests, and strict types passed.
`git diff --check` passed. Only synthetic local records and loopback peers were
used; no real endpoint, credential or remote write was involved. No commit was
made, pending the requested follow-up review.

## 2026-11-05 — Independent follow-up review

Reviewed the uncommitted R1–R4 implementation and associated improvements.
Node 24.22.2 strict types and all 81 tests passed. The original bounded review
driver made seven loopback requests and confirmed the corrected token-limit,
final-stop, partial-task, and cumulative-usage outcomes with passing controls.

An offline additional control found R5: the new `--record` adapter treats a
complete HTTP 200 `count_tokens` record as a Message and emits eight missing
Message-field failures. The existing auxiliary validator passes the same
`{"input_tokens":42}` body; a normal Message record also passes the adapter.
Synthetic records and inspection outputs are retained under ignored
`artifacts/review-followup-2026-11-05/`. See the follow-up section of the
[review](../reviews/2026-11-05-current-implementation.md) for the reproduction
and requested correction. Commit approval was withheld pending R5. No
production code, remote writes, or real endpoint calls were made.

## 2026-11-05 — Current implementation review fixes

Fixed all four findings in `docs/reviews/2026-11-05-current-implementation.md`.
The token-limit presets now emit a request-aware protocol observation comparing
`usage.output_tokens` with the sent `max_tokens`; normal one-token controls
report one output token, while both JSON and SSE overrun controls fail at
`/usage/output_tokens`. SSE validation now requires a non-null final stop reason
at `message_stop`, with the finding linked to the final delta. The offline
inspector and online validator agree on identical faulty bytes, while a stream
without a terminal event remains inconclusive. Exact-output task passes now
require the latest exchange to have a complete message and EOF. SSE usage
assembly validates and replaces supplied input, cache creation, cache read, and
output counters without mutating retained event data.

The offline inspector accepts `--record RESPONSE_RECORD`; it verifies the body
hash, success status, content encoding and media type, then derives format and
capture completeness. `CaptureRecord` now retains the HTTP adapter's
`headersMs` and `firstByteMs` values. No chunk or event arrival series was added.

The review's six improvement proposals were evaluated individually:

1. Implemented the saved-record adapter because it removes manual decoding and
   hash checks without moving I/O into protocol validators.
2. Deferred single-case selection and request preview. This needs coordinated
   changes to catalog selection, request construction and preview safety; it is
   broader than the current correctness and evidence work.
3. Deferred decoded event views and exchange-linked report navigation. They
   require coordinated report, viewer and evidence-identity changes.
4. Implemented retention of existing header and first-byte timings. Deferred
   chunk/event timing because it adds per-capture data and boundedness questions
   without an identified incident needing that detail.
5. Added paired normal/fault controls and an offline/online parity invariant
   for the repaired rules. Deferred a repository-wide rule-to-fixture ledger
   and retrieval metadata framework; the current fix does not need one to keep
   its evidence independent.
6. Kept the existing architecture small. No plugin system, standalone web app,
   generic orchestration layer or shared evaluation abstraction was introduced.

Node `v24.22.2`: `npm run check` passed all 81 tests, with no skipped, cancelled
or TODO tests, and strict types passed. Loopback HTTP checks used bounded
synthetic peers only. A first restricted run could not bind loopback; rerunning
the same check with local server access passed. No real endpoint, credentials,
hosted CI or browser workflow was used. No Git commit was made.

## 2026-11-04: Repository transition to the diagnosis Skill

The Skill, Node helpers, contract fixtures, and Node CI are the active
project. The former standalone assessment and its evidence are available in
the parent commit `8048934`. The inspector, probe implementation, and fixture
bytes were reused. This transition adds no endpoint cases.

A fresh worktree installed the locked Node tools and passed strict
TypeScript validation and all 63 tests on Node 24.22.2. The offline exercise
returned PASS for the normal stream, located the duplicate message start
at event index 1, and returned INDETERMINATE for the partial stream. The
forced-tool probe preview planned one request. Skill metadata and local
documentation links validated. The full check used synthetic HTTP peers.

## 2026-11-04: Live diagnosis walkthrough

An owner-authorized local trial completed the three basic probes against the
corrected model selection. All returned HTTP 200 and complete captures. All
task checks passed. Offline inspection verified the saved body hashes and
located omitted stop fields in the JSON message, the SSE start message, and
the SSE delta. Both SSE captures included the terminal event. Thinking
blocks remain outside the inspector's implemented rules.

Three probes using the previously used model name completed before the
correction. Both selections returned the same declared model label and the
same stop-field omissions. The declared label is evidence for checking the
routing configuration. It does not establish the backend model identity.
Private captures and report outputs are stored outside the repository. This
walkthrough exercised existing scenarios and added no endpoint coverage.

## 2026-11-04: Independent offline diagnosis

A fresh agent received the Skill, three anonymously named SSE bodies, and
the known capture completeness. It received neither expected findings nor
previous reports. One body came from the authorized local trial and the
other two were synthetic controls.

The agent matched all three reference outcomes. It located the missing
stop fields at event indexes 0 and 40 in the complete saved response. It
kept thinking extensions outside the tested rules and identified the
properly framed terminal event. The partial control was inconclusive.
Its terminal event text was present and its bytes matched the passing
control apart from the final two LF bytes. The passing control established
only that the inspected rules passed.

The agent kept protocol findings separate from client behavior and suggested
comparing captures before and after serialization to locate where the
fields disappear. The exercise made zero endpoint requests and added no
endpoint cases. The Skill and inspector code were unchanged.

## 2026-11-04 — Documented Messages probe expansion

Expanded the preset catalog from 5 to 35 cases. The 22-case core group reserves
27 requests. The remaining cases cover version migration and opt-in model
capabilities. Selection sends either `2023-06-01` or `2026-10-21`, without betas.
See [the coverage and usage guide](../probes.md) for the case groups and exclusions.

The new synthetic checks first reproduced the missing core profile and the
missing SSE thinking assembly. The full synthetic endpoint then exercised every
preset in 41 exchanges, with separate controls for malformed error envelopes,
incorrect token-count types, unsigned thinking streams, and request-specific
wire constraints. The complete Node check passed with 69 executed tests.
No live model was contacted during this expansion.

## 2026-11-04 — Assessment report readability

The Skill now separates a short evidence-backed synthesis from the generated
check record. The record groups repeated observations, retains independent
protocol and task outcomes, and links representative evidence before the full
case matrix. It does not include free-form response text. The JSON records
and diagnostic rules retain their existing contracts.

The presentation uses the historical baseline at `8048934:design.md` for
table hierarchy, neutral surfaces and evidence navigation. External references
were [llm-comply](https://pypi.org/project/llm-comply/) for summary versus raw
output, [Schemathesis](https://schemathesis.readthedocs.io/en/stable/guides/html-report/)
for failure evidence and execution warnings, and
[Allure](https://allurereport.org/docs/assertion-diff/) for expected versus
observed evidence.

The report regression failed before the presentation change and passed after
it. The complete Node gate passed 70 tests. A private three-batch synthesis
was rendered offline from existing captures and reviewed in a standalone
browser at desktop light and narrow dark widths. Its nine local links resolved.

## 2026-11-04 — HTML report delivery

The CLI emits one human-facing `report.html`. It keeps JSON evidence attachments.
The report uses section links, readable observations, native disclosure for
occurrence locations, and separate protocol and task outcomes. It is bilingual,
uses the system color scheme, and loads no external assets. The Skill guide now
calls for a single HTML synthesis above the automated evidence.

A valid first tool call followed by a protocol gate now leaves tool continuation
inconclusive. The original protocol failure remains visible. A synthetic peer
covers the distinction, and the CLI test checks that a fresh output contains
HTML and no Markdown report. The existing GLM captures were used to preview
a new synthesis and the underlying reports without contacting the endpoint.

## 2026-11-04 — Offline JSON evidence viewer

Report links open static syntax-highlighted HTML companions for the retained
JSON files. The viewer has a direct link to the original and keeps the entire
JSON text selectable. It embeds no scripts and uses the shared color schemes.
The original capture is still persisted before evaluation.

The Node gate passed 71 tests. Local-browser checks followed the real GLM
report links in both themes, verified the original JSON and return navigation,
and compared the largest viewer's DOM text against the source in chunks.

## 2026-11-04 — English report default

Reports and evidence viewer labels default to English. The report guide calls
for concise engineering prose tied to the observed response and applicable
requirement. The existing GLM report was rewritten in English from retained
captures. All local report links resolved, and the Node gate passed 71 tests.

## 2026-11-04 — Technical report layout

The report type, model name, and test scope now have separate places in the
header. Tables use restrained rules and aligned numeric columns. Expanded
findings separate the case, evidence location, and response link. The GLM
report was checked at desktop width in light mode and at 390 pixels in dark
mode. Local evidence links resolved, keyboard expansion worked, and all 71
Node tests passed.

## 2026-11-04 — Navigation on long reports

An offline script adds a contents control after the inline contents scrolls
out of view. It marks the current section and provides a return to the top.
The report permits only the bundled script by content hash. Inline links
still work without JavaScript. The JSON viewer remains script-free.
Browser checks covered desktop, a 390-pixel viewport, keyboard focus,
printing, and the no-script fallback. All 71 Node tests passed.

## 2026-11-04 — Report hierarchy and narrow-screen results

The GLM report now leads with the verified output-limit failure, uses numbered
sections and finding references, and presents the requested and reported token
counts in a two-row evidence table. The shared report style uses system type,
neutral rules, and a reserved palette for links and status. The capability
table retains its row and column roles while giving observations the full row
width on narrow screens. The compact contents control uses a shorter label.

References were the [W3C evaluation report template](https://www.w3.org/WAI/test-evaluate/report-template/),
[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html), and
[Schemathesis HTML reporting](https://schemathesis.readthedocs.io/en/stable/guides/html-report/).
Browser checks passed at 1150, 390, and 320 pixels, including keyboard navigation,
print, the no-script fallback, and local evidence links. All 71 Node tests
passed. No endpoint requests were needed.

## 2026-11-04 — Reusable Skill report workflow

The Skill owns the assessment renderer, shared HTML layout, and navigation.
It reads a short English assessment input and retained probe results, computes
the scope, and resolves each finding to the named run, case, and exchange.
The CLI check records and JSON viewer use the same layout. The example is
synthetic and the project stores no private report or capture.

A synthetic regression verified deduplicated case counts, viewer and raw
links, and rejection of an unrecorded exchange. The renderer also processed
three retained GLM runs offline and verified the 35 selected cases, 42 requests,
and local evidence links. A copied renderer produced identical HTML. Browser
checks covered the finding link, scroll navigation, and JSON viewer at 390
pixels. All 72 Node tests passed.

## 2026-11-05 — Current workflow and authentication

The active checkout contains the Skill, Node helpers and synthetic fixtures.
The old application and container files remain in Git history. The residual
pre-commit framework configuration was removed, and package/check/CI names
now describe the Skill. One Node 24 CI job runs the shared check entry point.

The connection guide documents endpoint normalization, API-key, Bearer and
unauthenticated requests, and the environment in which credentials must be
available. Synthetic endpoint assertions verify the actual headers for all
three modes. An empty named credential fails before creating output. The
Bearer run's output files were checked for the synthetic secret. All 73 tests
passed. This validation does not establish a remote CI result.

## 2026-11-05 — Restore the repository's established name

The project and Skill use Anthropic Readiness and the identifier
`anthropic-readiness`. The unapproved diagnosis-specific product name was
removed from active documentation, package metadata and import paths.
The Skill directory is `skills/anthropic-readiness`. All 73 tests passed
after the path correction.

## 2026-11-05 — Explicit AR_DIAG target configuration

The approved target variables are AR_DIAG_ENDPOINT_URL, AR_DIAG_MODEL,
AR_DIAG_AUTH_MODE, AR_DIAG_AUTH_TOKEN and AR_DIAG_API_VERSION.
The CLI reads the group only with --use-env. Explicit target arguments take
precedence, and --auth-env can select an existing credential variable.
Authentication mode none ignores credentials in both the CLI and engine.

Synthetic endpoint checks covered environment-only API-key, Bearer and
unauthenticated runs, explicit credential overrides, suppression of a supplied
token in none mode, missing credentials before output creation, and exclusion
of the synthetic secret from generated files. All 75 tests passed. Connection
examples passed shell syntax checks.

## 2026-11-05 — Current implementation review

Reviewed the active Skill, helpers, validators, execution flow, reporting,
tests, CI configuration, and documentation at `3503816`. Installed the locked
tools and passed strict types and all 75 tests on Node 24.22.2. The restricted
first attempt could not bind loopback servers; the same gate passed when
allowed to run its synthetic peers.

An additional synthetic driver ran twice with seven loopback requests per
invocation and a two-second deadline per engine run. The final run compared
identical SSE bytes through offline inspection and online evaluation. It
confirmed four open issues: token-limit overruns pass both JSON and SSE probes;
offline inspection passes a null final stop reason that online protocol
validation rejects; a stalled partial stream earns a task pass; and assembled
SSE usage omits final input/cache counter updates. Normal controls were retained.

See the [review](../reviews/2026-11-05-current-implementation.md) for priorities,
source locations, official references, and improvements. Reproduction code and
results remain local under ignored `artifacts/review-2026-11-05/`. Production
code and existing tests were unchanged. No real endpoint, SDK/client workflow,
hosted CI, or browser layout check was run, and endpoint coverage did not grow.

## 2026-11-06 — Project-local Skill installation

The Skill directory now contains the Node runtime, the probe reference,
and the MIT notice. The development toolchain and synthetic fixtures stay
in the source repository. The install instructions extract one selected
Git revision into a consumer project's `.agents/skills/` directory.

The new isolated check reproduced the missing inspector before the runtime
move. It also exposed a probe entry point that silently exited when its
path passed through a symlink. The check now runs in a temporary consumer
with a CommonJS package and a path containing spaces. It verifies a normal
stream, a duplicate start at event index 1, a partial stream, a one-request
probe preview invoked through a symlink, and offline report evidence links.
The preview sends no requests.

On Node 24.22.2, strict types and all 83 tests passed, with zero skipped
or cancelled. The first restricted run could not start the existing
loopback peers. The full gate passed with local loopback access. Skill
metadata, all bundled relative links, and shell example syntax were checked.
Codex discovery and diagnosis in a fresh consumer chat remain for the
[offline exercise](../offline-exercise.md). No real endpoint was called.

## 2026-11-07 — Plugin entry points for three agent hosts

The repository provides one distributable directory with an Agent Plugins
1.0 manifest for Codex, a Claude Code manifest and marketplace, and an
OpenCode 2 server entry point. The plugin ID is `messages-readiness` because
Claude Code reserves the `anthropic-` plugin prefix. The Skill remains
`anthropic-readiness`. The OpenCode entry point registers the bundled Skill
and a slash command that forwards the user's request to the agent.
The README shows how to export only the distributable files and how to
invoke the standalone Skill with natural-language keywords.

Codex 0.167.0-alpha.3.2 read the local marketplace and listed the bundled
Skill. Claude Code 2.1.318 passed strict manifest and marketplace validation
on a clean bundle. OpenCode 2.2.5 loaded that bundle in a temporary consumer
project, where its local server listed the Skill and slash command. The
bundled inspector found the duplicate start at event index 1. The Node
24.22.2 gate passed strict types and all 84 tests, including slash-command
forwarding. These plugin checks did not run a model-driven plugin chat,
test a desktop installation flow, or call a real diagnostic endpoint.

Separately, the consumer project reported that the standalone install from
`166e485` passed explicit and implicit invocation in two fresh Codex CLI
chats. Both used the installed checker and located the duplicate start.
The normal and partial controls, offline preview, and report rendering also
matched their expected results.

## 2026-11-07 — npm scaffold as the distribution entry point

The package source is `scaffold/` and its command is
`npx @sleetdrop/anthropic-readiness init <directory>`. One generated project
holds one target, local credential and evidence paths, run output, and a
copy of the bundled Skill. The initializer uses `.agents/skills/` by default
and supports `--claude-code` for `.claude/skills/`. The earlier standalone
Skill and plugin distribution entries are retained in Git history at
`4d8d105`.

The first target-directory regression failed on the previous CLI's unknown
option. The new mode previews without reading a credential and requires
explicit live consent plus request and time bounds for execution. It rejects
mixed connection settings and reads the local token only for an
authenticated run.

The Node 24.22.2 gate passed strict types and all 85 tests. The package test
packed and invoked the executable offline, checked both output layouts and
repeat initialization, verified that preview made zero requests, and ran one
authenticated request against a synthetic loopback endpoint. The token was
absent from retained outputs. A separate `npx` run created a project from the
local tarball, and Codex discovered its project-level Skill. A model-driven
chat with the new scaffold and registry publication remain unverified.

## 2026-11-07 — Independent acceptance of the generated project

The consumer-project session byte-matched all 29 npm package files against
`1bd9aaa`. It verified and removed the 25 unchanged legacy test files, then
used the actual local tarball through `npx` to regenerate the same project
directory. Configuration defaults, private-file permissions, Git ignore
behavior, bundled Skill contents, and repeat-initialization protection passed.

Two fresh ephemeral Codex CLI conversations used the same default model
settings, one with explicit Skill invocation and one with a natural incident
request. Both read the generated Skill and executed its inspector on neutral
normal, faulty, and partial captures. They returned the expected FAIL, PASS,
and INDETERMINATE results, located the duplicate start at event index 1, and
verified the one-frame difference against the raw evidence. The exact backend
model identifier was not recorded.

A separate agent read `--target-dir`, completed a zero-request preview, and
executed one authenticated request to a synthetic loopback service under a
one-request, 5000 ms authorization. The retained result records one attempt,
protocol PASS, task PASS, and clientStatus not_tested. The token was absent
from agent transcripts and retained outputs. The service was stopped after
the run. The source session also read the acceptance report and checked the
saved result's request count, limits, profile, and status.

No source defect was identified. This acceptance covers the local npm tarball
and Codex CLI. Registry installation, Claude Code's generated layout, desktop
selection, real endpoints, and actual client replay were outside this run.
