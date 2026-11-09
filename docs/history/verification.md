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
[review](reviews/2026-11-05-current-implementation.md) for the reproduction
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
See [the coverage and usage guide](../../templates/skills/anthropic-readiness/references/probes.md) for the case groups and exclusions.

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

See the [review](reviews/2026-11-05-current-implementation.md) for priorities,
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

## 2026-11-07 — Full core acceptance and release preparation

The independent consumer project continued using the unchanged npm package
from `1bd9aaa`. A fresh Codex CLI chat used only the generated Skill and
helpers on Node 24.22.2. Both previews completed with zero HTTP requests.
The normal synthetic target passed all 22 core cases in 27 requests; protocol
status passed for every case, with 16 task passes and 6 task skips for the
count and error cases. The service checked request paths, version, synthetic
authentication, model, request-specific fields, actual tool-ID round trips,
fresh history and tool-result tokens, parallel results, and error recovery.

The separate one-request forced-tool control omitted `stop_sequence`.
The generated checker reported exactly one failing rule,
`MSG-STOP-SEQUENCE-FIELD`, at the response root with the missing key named.
Task behavior passed while protocol status failed, as expected. Across both
corrected runs, 23 case executions represent 22 distinct case IDs and 28
requests. Actual SDK/client behavior remains `not_tested`.

The agent reviewed retained evidence and generated the English synthesis with
the bundled assessment renderer. The source session independently verified
the saved case outcomes, task counts, overlap accounting, and all 57 local
report links and anchors. The report separates the expected faulty control,
successful core coverage, and untested capabilities. The consumer retained
the report, run evidence, and transcripts locally; none were added to source.

The first acceptance fixture misread two plan outputs in one command as a
single preview and shut down early. Its 23 attempts produced one received
HTTP request and blocked results, which remain separate from successful
coverage. After an offline control fixed the observer, the corrected round
completed 28 attempts and 28 received requests. Both rounds total 51 attempts
and 29 received HTTP requests, within the explicit 32-HTTP-request ceiling.
The corrected service completed within its 180-second window and was stopped.
The consumer audit found no synthetic credential in transcripts or reports.
No product defect was identified.

The source Node 24.22.2 check passed strict types and all 85 executed tests,
with no failures, skips, or cancellations. Local loopback tests required the
execution environment to permit listening; the initial restricted invocation
could not start those peers. The release guide now requires validation,
merging to `main`, an annotated tag matching the `0.2.0` package version, and
packing from that revision before any authorized remote push or npm publish.
No registry installation, real diagnostic endpoint, optional capability
profile, or actual SDK client was tested in this acceptance.

## 2026-11-07 — Private configuration smoke check

After the owner supplied target and credential files in the generated
consumer project, the execution session validated the configuration and
completed a zero-request preview. It then used the unchanged bundled runner
on Node 24 for one authorized `anthropic-tools-smoke` attempt, capped at one
request and 45000 ms overall, with a 30000 ms attempt deadline. The request
returned a complete HTTP 200 response in approximately 2.56 seconds. No retry
was made, and the owner-supplied files were not changed.

The selected forced-tool task passed, with no explicit authentication or
model rejection. Protocol status failed on three observations:
`MSG-STOP-SEQUENCE-FIELD` for the missing root field, `MSG-MODEL` for a
response identifier different from the configured model, and
`MSG-THINKING-SIGNATURE` for the missing signature in the first thinking
block. The execution session checked the original response hash and fields
and independently inspected the retained response record. The source
session verified the saved attempt count, limits, task status, failing rules,
and evidence locations without copying private target or model values.

The configured target completed this task; the evidence does not verify the
requested model routing, establish broad protocol compatibility, or show
that the owner filled in the configuration incorrectly. Actual SDK/client
status remains `not_tested`. Private configuration, original captures, and
the local trial record remain outside the source repository. No full core
suite, remote push, npm publication, or product change occurred in this
trial.

## 2026-11-07 — Full private protocol assessment

The owner described a self-hosted inference stack using an OpenAI-native
interface and API conversion software to expose Anthropic Messages. The
assessment target was the resulting external API; exact component versions
and backend identity were not independently established. The owner authorized
a full assessment of the existing configured target. Configuration and
credential files were preserved, with no aliases added to suppress identity
findings and no automatic retries.

The consumer selected the complete core and every non-migration capability
profile under the configured `2023-06-01` header: 32 cases reserving at most
38 requests. The three `2026-10-21` migration cases were explicitly untested.
The run was admitted with a ceiling of 41 attempts and 600000 ms overall,
45000 ms per attempt, 10000 ms to connect, and 30000 ms between reads.
All 32 cases received results. Actual execution started 36 attempts in
approximately 87.5 seconds. The streamed tool loop and error-result
continuation each lacked a prerequisite for its second request; neither was
sent or counted as passing coverage.

All 36 captures ended at EOF. HTTP results were 31 status 200, three status
404, and two status 400. Aggregate case results were 27 FAIL and 5 BLOCKED;
protocol results were 27 FAIL and 5 INDETERMINATE. Task behavior was reported
separately: 15 PASS, 7 FAIL, 4 INDETERMINATE, and 6 SKIP. These counts do not
mean every capability failed: successful behavior coexisted with repeated
wire deviations and an unverified response-model mapping.

Verified findings included missing stop and thinking-signature fields,
stream-start and delta deviations, output usage above the one-token test
limit, invalid requests receiving successful responses, and structured-output
differences. The count-token route returned 404 for the selected requests.
The complete image and PDF error responses rejected the supplied input and
declared text-only support. Cache responses reported read counters but did not
establish the selected creation-then-hit condition, so the report retained an
inconclusive capability conclusion. No individual stack component was blamed
without a distinguishing comparison.

The consumer generated a formal English synthesis using the bundled renderer.
The source session independently checked every request and response hash,
case and task counts, all 82 selected evidence references, and all 107 local
links and anchors in the main report. Original captures, private target and
model values, report input, and HTML remain outside the source repository.
The consumer also checked 451 links across the local report set and inspected
desktop and mobile layouts. Actual SDK/client behavior remains `not_tested`.

The workflow completed the requested scope, retained complete evidence, and
distinguished endpoint deviations from successful task behavior and uncertain
coverage. No product defect was identified in these checks. The project
intent, generated README, Skill entry point, and reporting guide now make
protocol implementation assessment the primary workflow, with focused
diagnosis available for individual findings. The runner and validators are
unchanged. The next package candidate is `0.2.1`; the local `v0.2.0` tag was
not moved. Node 24.22.2 strict types and all 85 executed tests passed with no
failures, skips, or cancellations. Skill metadata and local documentation
links validated. No remote push, new release tag, or npm publication occurred.

## 2026-11-07 — First portable workbench release candidate

The owner clarified that previous designs and version numbers documented
unreleased exploration. The scaffold's first public release candidate is
therefore `0.1.0`, rather than a continuation of the internal `0.2.x` numbers.
Private development-package version fields were removed without changing
locked dependencies. The locked tools installed successfully with Node 24
using offline `npm ci`. Protocol-contract identifiers and original test
archives keep their existing meaning and were not rewritten.

A read-only remote tag query found no remote `v0.2.0` tag.
The mistaken local tag was removed after saving its annotation locally.
All commits, prior verification records, and test artifacts were preserved.
The working branch was renamed to `feat/agent-workbench` to describe the
portable generated workspace rather than a host-specific adaptation.

The initializer now generates a root `AGENTS.md` describing the workbench,
configuration and evidence paths, authorization bounds, and bundled Skill
entry point. Its link uses the selected `.agents/skills/` or `.claude/skills/`
location and portable forward slashes. The npm package includes the template.
The generated README explains explicit loading when the agent does not
automatically discover instructions or skills. No agent framework, provider
configuration, or extra credential service is required.

The package regression first failed because the packed archive omitted
`project/AGENTS.md`. After the implementation, the actual packed initializer
generated valid Skill links under both layouts, and the existing bounded
synthetic probe passed. Node 24.22.2 strict types and all 85 executed tests
passed, with no failures, skips, or cancellations. This check sent no new
requests to a real diagnostic endpoint. No replacement release tag, remote
write, or npm publication was performed.

## 2026-11-08 — Local workbench merge

The validated `feat/agent-workbench` branch was fast-forward merged into
local `main` at `3fdf2d0`, without conflicts. The merged package remains the
first public `0.1.0` candidate and includes the generated `AGENTS.md` entry
point. The previously recorded Node 24.22.2 strict-type check and all 85
executed tests cover the merged implementation. This status update changes
documentation only. No new release tag, endpoint request, remote push, or
npm publication was performed.


## 2026-11-08 — Repository layout cleanup

The repository is now one npm package. The command moved to `bin/`, workbench
files to `templates/`, and all tests to `tests/`. Development checks, the lock
file, TypeScript configuration, and Node version pin now live at the root.
CI uses the same root-level install and check commands. Test discovery is
limited to `tests/` so local archives are not executed as tests.

Removed the obsolete `next/` package and duplicate scaffold metadata, README,
and license. Deleted the old Python environment and caches. Earlier local
check logs, coverage data, and UI prototypes were archived under ignored
`artifacts/archive/`. Historical reviews and verification records moved to
`docs/history/`; their original paths and commands remain historical context.

Rewrote the current README and contributor guide and added architecture,
release, fixture, and initial changelog documentation. Local Markdown links
and GitHub YAML syntax validated. The 24 bundled Skill files and 10 original
protocol fixtures are byte-identical to the pre-cleanup copies. Fixture text
conversion is disabled to preserve exact framing across platforms.

Node 24.22.2 installed the locked root dependencies offline and passed strict
types and all 85 executed tests, with no failures, skips, or cancellations.
The tests packed the root package, created both workbench layouts, inspected
saved evidence, rendered reports, and used bounded synthetic HTTP peers.
The 30-file npm archive contains only `bin/`, `templates/`, package metadata,
README, and license. No real endpoint request, remote push, release tag, or
npm publication was performed.


## 2026-11-08 — Source release preparation

The owner authorized pushing `main` and creating the annotated `v0.1.0` tag.
The remote branch was checked and can be fast-forwarded; no remote tag with
that name exists. The changelog now identifies the first source release.
Only documentation changed after the recorded 85-test repository check.
The npm package remains unpublished; registry installation is unverified.

## 2026-11-08 — Interactive npm publish helper

Added `scripts/publish.sh`, following the registry, login, interactive publish,
and verification workflow used by `sleetdrop/dsh-plugin-topology`. The helper
finds the repository root, selects Node 24 from PATH or an installed Homebrew
formula, checks the annotated version tag and package inputs, and requires the
`sleetdrop` npm account. Registry operations target npmjs.org; a conflicting
scope registry is rejected before authentication or publication.

The helper installs locked tools, runs repository checks, and packs the Git
tag. npm keeps its terminal input and output for login, OTP, and browser
verification. After publishing, bounded read-only checks compare the registry
version, archive integrity, and npm dist-tag. A registry-package initialization
check runs in an empty temporary directory. Publication itself is never
retried automatically. `--dry-run` skips sign-in and actual publication.

Eight tests use temporary Git repositories and a simulated npm command.
They cover normal publication, dry-run, missing tags, changed package inputs,
account mismatch, publish failure, prerelease tags, integrity mismatch, Node
selection, scope-registry overrides, and isolated registry installation.
Controls first reproduced the scope-override and non-isolated-installation
failures before the corresponding guards were added.

Node 24.22.2 strict types and all 93 executed tests passed with no skipped or
cancelled checks. Bash syntax and ShellCheck passed. A full helper dry-run
completed without sign-in or publication, and its 30-file archive retained the
validated `v0.1.0` SHA-256. Package inputs and the existing source tag were not
changed. No actual npm publish, OTP exchange, or diagnostic endpoint request
was performed.


## 2026-11-08 — Separate npm publication from Git

The owner clarified that source tagging and npm publication are independent.
Removed all Git commands and tag requirements from `scripts/publish.sh`.
It now packs the current project directory, with archives stored by npm
version. Authentication, repository checks, public-registry guards, publication,
and registry-installation verification remain part of the npm workflow.

Node 24 is found through PATH or an optional dynamic Homebrew lookup. There
are no machine-specific user directories or installation prefixes. A failed
Homebrew lookup no longer supplies an empty prefix to the Node search.

The regression fixture has no Git repository and rejects any Git invocation;
publication succeeds using its current package files. A full helper dry-run
also passed from an isolated source copy without `.git`, using Node 24.22.2.
Strict types and all 93 executed tests passed. Bash syntax and ShellCheck
passed, and the dry-run archive contained the expected 30 files. Temporary
source files were removed after preserving local check results and the archive.
No sign-in, OTP exchange, actual npm publication, or Git tag change occurred.

## 2026-11-08 — Read-only source tag contract

The owner clarified that reading Git metadata is allowed. Creating or pushing
source tags must remain separate from npm publication. Restored the existing
`v<package.json version>` tag contract without requiring the tag to be pushed.
The helper resolves that tag to a commit, checks package inputs against it,
and packs an exported snapshot. It never creates, moves, fetches, or pushes
Git references. Node selection remains portable and contains no local paths.

A failing control first showed that working-directory packing included an
untracked file. Nine simulated helper tests now pass, including missing tags,
changed package inputs, snapshot packing, and unchanged Git references.
The test Git wrapper rejects commands outside its read-only allowlist.

Node 24.22.2 strict types and all 94 executed tests passed with no failures,
skips, or cancellations. Bash syntax and ShellCheck passed. A full helper
dry-run produced the expected 30-file archive with the previously validated
`v0.1.0` SHA-256. Git references were identical before and after the dry-run;
package inputs and the existing source tag are unchanged. No sign-in, OTP
exchange, actual npm publication, remote write, or diagnostic endpoint request
was performed.

## 2026-11-08 — Deferred npm publication verification

The owner submitted `@sleetdrop/anthropic-readiness@0.1.0` from their terminal.
npm accepted the upload and reported that processing might take a few minutes.
The old helper exhausted three immediate queries and incorrectly treated
temporary unavailability as a verification failure. A read-only query found
the version record and matching archive integrity while the package index
still returned 404; installation was not yet possible at that point.

A synthetic pending-registry control reproduced that false failure before
the fix. Normal publication now ends successfully when npm accepts the
submission, without querying or installing the package afterward. The
separate `--verify-only` mode compares registry metadata with the saved
archive and tests initialization in an empty temporary directory. It never
signs in, publishes, or reruns repository checks. Unavailable metadata is
reported as pending with exit code 2; metadata mismatches remain errors.
Verification requests use online metadata, a 15-second request timeout,
and no automatic retries.

Node 24.22.2 strict types and all 97 executed tests passed, including twelve
simulated publish-helper checks. There were no failures, skips, or cancelled
checks. Bash syntax, ShellCheck, and whitespace checks passed. A later real
`--verify-only` run completed successfully after the registry became ready:
version `0.1.0`, archive integrity, and `latest` matched, and the registry
package created the expected workbench. This run did not publish or change
Git tags. Package inputs remain unchanged from `v0.1.0`. No diagnostic
endpoint calls or remote Git writes were performed.

## 2026-11-09 — Consumer Node compatibility

Broadened the npm engine declaration from `>=24 <25` to
`^22.18.0 || >=24.2.0` and aligned the initializer's runtime check. Unsupported
releases report the required range and detected version before any workbench
directory is created. Future stable major versions are no longer blocked;
prerelease runtimes remain outside the declared range. Workbench guidance,
the Skill, and runtime documentation now distinguish consumer compatibility
from the Node 24 development and publication environment.

Before the change, the real packed-consumer test on Node 22.23.4 failed with
`EBADENGINE` for the old range. A version-guard control simulating Node 28.0.0
also failed with `Use Node 24 LTS.` before the implementation changed. The
new guard tests exercise future-version acceptance and explicit rejection of
unsupported stable and prerelease versions. These simulations only test the
guard and do not establish runtime compatibility with future versions.

Installed Homebrew Node 22.23.4, 24.22.2, and 26.13.0 each passed strict
TypeScript validation and all 99 executed tests, with no failures, skips,
cancellations, or todos. Each run packed the actual source and used npm's
strict engine checking to initialize both workbench layouts, preview a plan,
and execute a bounded synthetic loopback probe. The suite also exercised
offline inspectors and HTML reports. The twelve publish-helper simulations
now model publish-time Node selection independently of the test runner's
Node version, while preserving the publisher's Node 24 requirement.

An actual Node 20.20.2 initialization attempt exited with code 1, reported its
unsupported version, and created no directory. Per the owner's requested
scope, historical minor releases, including the precise 22.18.0 and 24.2.0
feature floors, were not downloaded or executed. No additional Node
installation was required. CI now checks the latest 22, 24, and 26 releases
and retains the `ci-required` aggregate check; remote CI has not run yet.

The locally packed archive still has 30 files and excludes development
tools, tests, history, and local artifacts. Per-version check logs, executed
test summaries, the Node 20 rejection record, and the package inventory are
saved under ignored `artifacts/node-compat/`. Dependency installation used
the locked tools and an offline cache. Whitespace checks passed. The package
version remains `0.1.0` with an Unreleased changelog entry; the published
package and existing source tag were not modified. No real diagnostic
endpoint calls, authentication, npm publication, or remote Git writes occurred.

## 2026-11-09 — Prepare npm 0.1.1

Prepared the patch release for broader Node compatibility. Package and lock
versions are `0.1.1`; the changelog and local package example use that version.
Read-only remote checks found `main` at `9e1a21d`, the existing `v0.1.0` tag,
and npm's `latest` at `0.1.0`; npm had no `0.1.1` version.

On the prepared `0.1.1` source, Node 24.22.2 passed strict types and all 99
executed tests, with zero failures, skips, cancellations, or todos. The
previously recorded Node 22.23.4 and 26.13.0 checks cover the same runtime
implementation. The new-version package preview contains the expected 30
files and excludes tests, development tools, history, and local artifacts.
Check output and the inventory are under ignored `artifacts/releases/0.1.1/`.

The owner authorized the Git push and release tag, and requested guidance
for their own interactive npm publication. The package is prepared for a
new `v0.1.1` source tag; npm publication and registry verification remain
pending. The existing `v0.1.0` tag and npm package are unchanged.

## 2026-11-09 — Push and verify the 0.1.1 source release

Created release commit `8089e7b` and the annotated `v0.1.1` tag. The actual
publish helper's offline `--dry-run` passed its tagged-source checks, locked
tool installation, strict types, all 99 tests, archive packing, and npm
publication preview. The archive has 30 files and is saved at
`artifacts/releases/0.1.1/sleetdrop-anthropic-readiness-0.1.1.tgz`.

Pushed `main` and `v0.1.1` atomically, as authorized by the owner. A remote
read confirmed that the branch and peeled tag both pointed to
`8089e7b78ec27acd1f77aa8287b75e6c06d5d3eb`. GitHub Actions
[run 42586118958](https://github.com/sleetdrop/anthropic-readiness/actions/runs/42586118958)
completed successfully: `node-compatibility (22)`, `node-compatibility (24)`,
`node-compatibility (26)`, and `ci-required` all passed. The compact job
summary is retained at `artifacts/releases/0.1.1/github-ci.json`.

Actual npm publication was left to the owner's interactive terminal, as
requested. The dry-run did not sign in or publish. npm availability,
registered integrity, dist-tag, and installation of `0.1.1` remain unverified
until publication and the separate `--verify-only` step complete. This
verification-record update changes no tagged package inputs.
