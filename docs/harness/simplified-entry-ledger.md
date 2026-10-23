# Simplified test entry

## Approved scope

On 2026-10-23 the owner approved reducing the initial setup form to endpoint and
model, with an optional API Key. This supports starting an assessment; it adds
zero endpoint scenarios or validator capabilities. The installed catalog remains
five cases with up to six requests for all profiles.

## Behavior

- Fresh forms automatically resolve origin and /v1 bases, or accept explicit
  /messages paths. Other custom paths require the explicit full-URL setting.
  Credentials, query strings and fragments remain rejected. Addresses are never
  silently redirected from container loopback to the host.
- A blank display name uses the model name. Copied and saved names are preserved.
- A blank optional key sends no authentication. A supplied key selects x-api-key;
  only the credential reference enters a preview or preset. Explicit no-auth,
  explicit API-key and allowed server credential references remain available.
  Changing the inferred authentication mode invalidates the reviewed plan.
- All installed profiles remain selected on a fresh form. A compact summary
  shows distinct case count and maximum initiated request count. Scope can be
  expanded and changed; imported controlled retests retain their locked scope.
  Counts use server-supplied request counts, including both tool-loop exchanges.
- Scope and advanced settings start collapsed. Rules, model identity policy,
  aliases, capability exclusions and execution/capture limits retain their
  previous semantics. Model identity is still checked by default.
- The empty preview sidebar is removed. Reviewing the plan reveals an inline
  confirmation section; only the separate explicit Start action sends requests.
  Presets can be reused without retaining secrets.

## Verification and delivery ledger

- RED: automatic URL resolution failed before implementation; the new browser
  entry test failed because the simplified controls did not exist.
- Initial targeted browser run: three passed and one failed because the action
  extended below a 390px English viewport. Fixed layout rather than weakening
  the viewport assertion. Failed logs/screenshots remain ignored.
- Final related browser run: 47 passed, including both widths' accessibility
  checks, two-field startup, optional-key secrecy/invalidation, scope counts,
  locale/theme screenshots, existing console and workbench flows, and the tool
  round trip. All transport traffic used synthetic local fixtures.
- One independent read-only review of the final diff found no material blocking
  issue. It did not run tests or claim independent execution acceptance.
- Final-source fast graph passed eight gates with unchanged source. An additional
  imported original-scope retest/comparison browser check passed. Documentation
  checks passed. Local trial revision `decd559` is running at
  http://localhost:8765/new; all 157 installed package files match source, health
  and new-form checks passed, and the three prior completed records remain.
  Keep the trial running; the development container is stopped at handoff.
  No full graph or new remote CI is claimed.
- The first package build used an incompatible no-network cache key and failed
  dependency resolution. An intermediate image assembled before that package
  build completed was not deployed. Restored the original cached build mode,
  awaited its successful completion, rebuilt the trial image and verified all
  installed source hashes before declaring delivery. Failed logs remain retained.

Evidence is ignored under artifacts/simplified-entry-20261023/. This iteration
does not call an owner's model endpoint, push to GitHub or publish an image.

## Browser input history follow-up

The owner explicitly requested localStorage memory for endpoint/model autocomplete.
Only these two fields may now persist in browser storage; earlier zero-storage
expectations are superseded for these fields only. API Keys, credential references,
full target objects, reports and captures are not persisted by this feature.

The versioned history key is anthropic-readiness.input-history.v1, limited to 20
unique recent values per field. Valid values are remembered on change or after a
successful plan preview. Native datalists expose suggestions after refresh, without
restoring field contents or starting requests. URL credentials/query/fragment data,
control characters and excessively long values are excluded. Storage is scoped to
the browser origin; it is separate from server presets and assessment history.
Clear input history removes only this key and its suggestions. Corrupt, unavailable
or full storage must not prevent normal configuration. Clear failures are reported
rather than claiming deletion. Other tabs refresh suggestions on storage changes.

RED browser verification observed missing history after leaving the input fields.
Four helper tests cover recency/deduplication, bounds, corrupt documents, allowed
fields, rejected URLs and storage failures/clear ownership. Seven related browser
checks passed, including existing secret clearing and locale/theme behavior. Those
privacy tests now assert the exact allowed storage document and absence of secrets,
instead of requiring all browser storage to remain empty. One independent bounded
read-only review found no material issue. The first fast run caught missing test
type annotations and a disallowed control-character regex; corrected without
relaxing the validation. Final checks and trial identity are recorded in progress.md.

This follow-up adds zero endpoint scenarios or protocol rules. Private inputs are
never copied from the owner's trial into source or build context. Evidence is
ignored under artifacts/input-history-20261023/; no genuine endpoint call, remote
CI, push or image publication accompanies this work.

Final closure: stable-source fast checks passed all eight gates, and the two
history browser checks passed after the type/lint corrections. Cached package
build, offline local image assembly and documentation checks passed. Trial
revision e8e270e is running; 157 installed files match source, health/new-form
checks passed, and all three original records remain. Keep the trial running and
stop the completed development container. No single full graph is claimed.

## User-perspective walkthrough

On 2026-10-23 the owner requested an actual usage review, without implementation.
Inspected nine current desktop screenshots from entry through standalone HTML
download, using the existing disposable fixture. Entry and the running overview
are usable. Highest-priority opportunities: compact the technical plan confirmation;
foreground concrete outcomes/impact after completion; organize export by reading
versus diagnostic handoff and collapse raw file inventories. Issue excerpts remain
useful but generic next actions need more context. Raw policy IDs, verbose helper
labels and skipped report section numbering are secondary polish items.

The in-app browser was unavailable and Chrome control timed out. The owner/tool
approval authorized fallback to the existing independent test browser. Six calls
went only to the synthetic peer. Its deliberately held count stream timed out
during the progress observation; neither that timeout nor the fixture clock age
is a production finding. No full accessibility/mobile audit or real endpoint check
is claimed. All fixture processes/listeners were cleaned up. No product code was
changed. Inspected screenshots, notes and a visual report remain ignored under
artifacts/ux-walkthrough-20261023/. Await the owner's choice before implementation.

## External reference follow-up

On 2026-10-23 the owner requested comparable-tool research and an independent
engineering-tool identity, rather than Anthropic branding. The
[reference study](../reviews/2026-10-23-engineering-console-reference-study.md)
records official-source mechanisms and distinguishes proposed adaptations from
verified behavior. Reconsider the earlier separate confirmation-page recommendation:
explore an inline summary while preserving validation and explicit live opt-in.
No product implementation or additional endpoint coverage accompanies this study.

## Representative interaction sample

The owner approved one overview/issue-detail design sample after the reference
study. See [prototype scope and verification](../design/console-study/README.md).
It is a separate static preview on 8767 with fictional observations; the current
product trial and its original results remain on 8765. Final desktop/narrow browser
checks and visual inspection completed after preserving/fixing the initial layout
overflow and transient dark-button contrast failure. No production implementation,
new diagnostic case, actual endpoint call or container upgrade accompanies this
sample. Await owner feedback before choosing a production change.

Palette follow-up: the owner rejected the original blue-gray appearance. The
standalone sample now offers three restrained neutral alternatives plus the
original reference, all with light/dark and bilingual controls. Graphite is only
a proposed default. Bounded isolated-browser rendering and sampled contrast/width
checks are recorded in the prototype README and ignored console-palettes artifacts.
No owner's Chrome profile, production source, endpoint or container was accessed.
