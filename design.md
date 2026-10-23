# Approved design baseline

Status: owner-approved on 2026-10-23. This is the current presentation baseline
for subsequent interface work. Small details can evolve through use; preserve
the accepted character and interaction model rather than reopening the design
direction on each iteration. Current owner instructions take precedence.

## Scope and reference

The accepted reference is the bounded issue -> occurrence -> evidence -> return
sample in [flow.html](docs/design/console-study/flow.html), with its
[CSS](docs/design/console-study/flow.css) and
[JavaScript](docs/design/console-study/flow.js). Reference revision: `bf98290`.
Its CSS/JavaScript match `93220f5`; the intervening teal-running trial was withdrawn.

This approves the sample's visual language and demonstrated interactions. It does
not claim that the installed application already implements them, or approve a
complete new configuration, report, export or repair-comparison layout. Their
existing data, evidence, accessibility and execution contracts still apply.
Sample counts and captures are fictional, not fixed product limits or new coverage.

The checked-in reference images are synthetic captures at 737x694 CSS pixels:

| View | Light | Dark |
| --- | --- | --- |
| Running issue list | [Reference](docs/design/baseline-2026-10-23/issues-light.png) | [Reference](docs/design/baseline-2026-10-23/issues-dark.png) |
| Selected event and raw evidence | [Reference](docs/design/baseline-2026-10-23/evidence-light.png) | [Reference](docs/design/baseline-2026-10-23/evidence-dark.png) |

These preserve the approved appearance without a running preview or ignored
artifact directory. They originate from verified `93220f5` sample captures and
include hover/selection states. They are visual references, not pixel-exact OS
font goldens. The live preview port and query revision are not the authority.

For presentation, this baseline supersedes earlier overview/runner/palette trials
and conflicting W1/W2 visual compositions. Their verification records remain
historical evidence. Protocol rules, evidence integrity and product scope are
governed by [project intent](intends.md) and the current engineering contracts.

## Character and information organization

Use a simple, calm engineering-tool character. Tables should read like clear
technical-article tables, with deliberate alignment, restrained rules and a small
number of visual accents. Keep an independent identity, including from Anthropic
branding. Avoid decorative gradients, glows, oversized metric cards and repeating
boxed status labels.

The interactive workspace supports following execution and investigating evidence.
Keep global run identity/status accessible while opening details. Normal progress
is quiet; exceptions are easy to scan. Broader report narratives belong in exported
reading documents. A report's final composition is outside this sample's approval.

Organize detail as run -> case -> step/exchange -> captured evidence. Grouped
observations cross-reference their occurrences; similar symptoms do not establish
a shared root cause. Show expected/observed information before technical IDs.
Separate issue categories, affected cases, assertions and request counts.
Keep task completion and protocol judgment separate; a protocol deviation alone
does not establish that an untested client workflow is broken.

## Typography and geometry

Use the sample's system UI/CJK font stack and monospace for identifiers/raw data.
Do not add a remote font dependency. Preserve hierarchy in both languages/themes.

| Element | Reference treatment |
| --- | --- |
| Base UI / line height | 14px / 1.55 |
| Main view heading | 18px, weight 600; 17px on narrow screens |
| Run-state heading | 16px, weight 600 |
| Issue-table header | 12px, weight 600, primary text color |
| Primary issue name | 12px, weight 500; linked when actionable |
| Supporting row description | 11px, weight 400, secondary text color |
| Table body / raw data | 12px; raw data uses monospace |
| Main content inset | 20px 24px; narrow 15px 12px |
| Issue-table cell inset | 12px; narrow 10px 8px |
| Issue filters / search input | 32px high, aligned centers |
| Supporting icons / header targets | 14px glyphs / 32px buttons |
| Protocol-status rule | 2px wide, 24px high, vertically centered beside text |

Headers need not dominate every cell, but the issue table must retain the accepted
clear header/name/description hierarchy. Prefer spacing and alignment to new
containers. These values anchor the sample density; extend them deliberately for
new components rather than forcing every future screen into identical geometry.

## Light and dark color roles

Color is restrained and meaningful, not prohibited. Neutral surfaces and reading
text dominate. Use the coordinated pair below; do not independently improvise
colors for each component or recolor entire traces to indicate one failed check.

| CSS token | Light | Dark | Meaning |
| --- | --- | --- | --- |
| `--surface` | `#fcfcfc` | `#1c1c1c` | Main surface |
| `--subtle` | `#f2f2f2` | `#242424` | Quiet surface hierarchy |
| `--text` | `#262626` | `#dedede` | Reading text |
| `--muted` | `#626262` | `#a8a8a8` | Secondary text; completed execution |
| `--line` | `#d7d7d7` | `#3b3b3b` | Table/surface separators |
| `--control` | `#8e8e8e` | `#666666` | Input/control boundaries |
| `--code` | `#f7f7f7` | `#191919` | Raw/parsed evidence surface |
| `--accent` | `#416b7b` | `#93b6c5` | Running, active interaction, focus |
| `--accent-soft` | `#eaf0f2` | `#29353b` | Selected occurrence/event or active view |
| `--fail` | `#984c57` | `#d1949e` | Confirmed protocol deviation |
| `--pass` | `#397052` | `#9bbda9` | Reserved for a verified passing result |

`--status-edge` aliases `--fail`. Use red on short status text and its adjacent
rule, keeping event names, payloads and long explanations neutral. A selected row
can carry a blue selection surface and a red deviation label at the same time.
The rule must not span the full cell or shrink to a letter-like 10px stroke.

Running uses gray-blue, including the heading and progress fill. The owner compared
and rejected teal running. Execution completion is neutral and never means all
checks passed. Inconclusive/untested conditions stay neutral and retain explicit
labels. Success green requires actual passing evidence; do not add passing results
or compatibility scores merely to display the palette. State meaning must remain
clear from words, counts and context when color is unavailable.

## Controls and lifecycle

- Keep issue filters as exclusive inline text options with a selected underline,
  followed by search with its magnifier inside the field and a separate result
  count. Retain a full accessible search label. Avoid scattered external labels
  and dropdowns for these three short filter choices.
- Keep run status separate from editable controls: explicit Running/Run finished
  heading, run identity, native case progress, and distinct finished-case and
  sent-request counts. Running findings are provisional; the finished view still
  exposes deviations, inconclusive results and untested client workflows.
- Preserve filter/query, selected occurrence/event/tab, reading position and
  return paths. Updating progress must not replace the evidence being read;
  browser history must not rewind the current run state or presentation choice.
- Start evidence inspection at the related location and relevant context. Full
  ordered capture remains available; search reaches the entire capture, not just
  expanded rows. An absent field is explained at its observed parent object;
  do not insert an invented missing line into raw data.
- Use local Heroicons 2.2.0 outline assets with their MIT license. Add an icon only
  when it aids recognition/direction. Back and integrated search use small neutral
  glyphs. The evidence button is text-only; its document icon was redundant.
- Theme switching uses only the day/night icon; language switching shows EN/中.
  Both have full localized action names and hover titles. Decorative glyphs are
  hidden from assistive tools; keyboard focus remains visible.
- Keep Chinese/English and light/dark geometry consistent. At the sample's 650px
  breakpoint, stack run information and reflow filter/search groups; keep detail
  scrollable and actions reachable without document-width overflow. Information
  hidden from a compact summary remains available in the investigation detail.

The footer's Prototype state controls, fabricated run ID/counts and study notices
are demonstration aids. They must not become production execution controls or
fake live activity. Product progress/results must come from the shared engine.

## Iteration and review

Read this document before changing interface/report presentation. Reuse accepted
patterns and tokens. For a deliberate baseline change, explain the user problem,
show a bounded before/after comparison and update this document with the decision.
Routine spacing, wrapping and usability corrections can proceed within that scope;
this is not a requirement to start another long design stage.

For presentation changes, check the affected states at comparable viewports in
both themes and languages. Include running/finished, inconclusive, selected
deviation and long-evidence return paths where relevant. Target at least 4.5:1 for
normal text and 3:1 for focus/meaningful control indicators; labels and structure
must carry meaning independently of color. Do not equate sampled contrast with
complete accessibility conformance.

Show previews through the Codex in-app browser when available; do not automatically
open the owner's everyday Chrome. Keep detailed checks/failed attempts in ignored
artifacts and record material observations in the progress/implementation ledger.
Update the reference images when a future accepted change changes their appearance.

This documentation delivery changes no product code or endpoint coverage. Approval
of the baseline does not authorize a new implementation stage. Follow the owner's
small, usable increments and separate actual delivery from prototype acceptance.
