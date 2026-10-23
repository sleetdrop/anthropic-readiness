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
