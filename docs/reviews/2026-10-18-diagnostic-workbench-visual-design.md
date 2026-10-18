# Diagnostic workbench: selected direction and companion surfaces

Date: 2026-10-18. Status: the owner selected the first overview concept and
approved continued refinement. Companion surfaces are submitted for review.
These are static design images, not an implemented or browser-verified product.

## Selected direction

Retain a compact application rail, target-oriented run header, view navigation,
grouped operational progress and a separate attention area. The owner preferred
this to a full case-table overview or a current-phase-dominated overview.
Refinements are a smaller target-alias heading, secondary model/configuration
identity and neutral execution completion. Only successful checks use green.

The authoritative reference is the first displayed generation:
`artifacts/w2/visual-20261018/exec-4e87de9b-ef7e-4626-ac6e-105bedcae9ed.png`.
The original generated title/emphasis and completion coloring are refined by the
rules above, not copied blindly into product behavior.

## Companion screens

All local artifacts are ignored design material under
`artifacts/w2/visual-20261018/`. Original generated images remain preserved.
Each generation received the selected overview image as an actual reference;
later generations also received the preceding companion where useful.

| Surface | Artifact | Main decision |
| --- | --- | --- |
| Issue diagnosis | `exec-4767842e-fafb-40a7-bcc3-39a79003f8a4.png` | Two-column issue list/inspector; expected and actual fields, scope, next verification and evidence entry points. |
| Repair comparison | `exec-e4d40757-6653-4df6-9f78-122fbcf3b047.png` | Conditions first; original recoveries, persistent failures and new failures together, followed by paired evidence. |
| Standalone report | `exec-f7a2a61a-532a-4816-968d-59f18b89f94f.png` | Editorial document with conclusion, numbered coverage/difference tables, findings and evidence links; no workbench controls. |

These are three successive product surfaces in the selected direction, not three
new alternative layouts requiring another ordinal choice.

## Consistent synthetic story

The baseline completes four installed cases. Its controlled behavioral tasks
pass, but the missing stop fields and response-model identity policy cause protocol
failures. The issue inspector shows a representative missing `stop_sequence`
field, distinguished from explicit null, with affected-case/evidence links.

The retest uses the same rules/judgment conditions against a different synthetic
endpoint. It corrects the stop fields, retains the response-model mismatch and
adds a duplicate stream-stop event in one streaming case. The current validator
has `STR-STOP` / `duplicate_message_stop`; implementation fixtures must generate
the corresponding actual assertion outcomes rather than preassign report results.
This is design data, not an observed run or claim that a real endpoint was repaired.

Issue-family counts are not case counts. The comparison's one recovered family,
one persistent family and one new family do not mean three cases were tested.
The same case can appear in several families. Both samples can have four behavior
passes and zero protocol-passing cases despite recovery of a specific check.

## Exact implementation requirements beyond the images

- Treat generated text as layout guidance. Real templates use exact fixture-driven
  strings and validated count derivation, not image OCR or screenshots as UI.
- The report matrix's fraction must be explicitly labeled as passing/assessed
  cases. Do not reproduce a bare failure label with `0/4` that could be read as
  zero failures. Mixed outcomes retain their full state counts.
- Generated navigation/control appearances are not proof that they work. Verify
  filters, details, evidence, Back/refresh and export/import through browser tests.
- A green recovery denotes only the paired check's result in this sample. It does
  not assert causal attribution, whole-client compatibility or long-term stability.
- Keep condition changes and verification gaps prominent when the clean comparison
  fixture is replaced by partial/mismatched inputs.
- The overview must meet actual 1280x800 and 1440x900 layout checks. These generated
  image dimensions and static compositions do not establish viewport acceptance.
- At narrow widths, use list/detail navigation and accessible horizontal table
  regions where needed; preserve readable type and primary actions at 200% zoom.
- Test a separately labeled 96-row synthetic catalog for scaling. No such catalog
  is currently shipped; overview remains grouped and the complete list lives in Cases.
- Documents remain readable offline, without scripts and when printed. A contents
  rail may collapse or disappear in print while numbered headings remain clear.
- Independent report and diagnostic archive are different deliveries: original
  machine/evidence files can contain source endpoint/model/business context, which
  the export preview must disclose. The document's alias is not proof that the
  accompanying original-source archive has been anonymized.

## Review and implementation handoff

The [approved specification](../superpowers/specs/2026-10-18-diagnostic-workbench-design.md)
governs behavior. The [implementation plan](../superpowers/plans/2026-10-18-diagnostic-workbench-implementation.md)
maps this direction to sequential source work and explicit visual/functional
acceptance. Companion visual review and written-plan approval are still pending.
No prototype server, product implementation, container acceptance or new endpoint
call is claimed by this design follow-up.
