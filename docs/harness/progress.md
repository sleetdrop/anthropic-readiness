# Verification record

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
