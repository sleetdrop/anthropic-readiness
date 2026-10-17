import assert from "node:assert/strict";
import test from "node:test";
import {
  resolvePreviewState,
  resolveEndpoint,
} from "../../src/anthropic_readiness/resources/web/forms.js";

test("test_edit_invalidates_preview", () => {
  const current = {
    target: { model: "one", limits: { max_requests: 4 }, beta_headers: [] },
    previewId: "frozen-plan",
  };
  const edited = { ...current.target, model: "two" };
  assert.equal(resolvePreviewState(current, edited).previewId, null);
  assert.equal(current.previewId, "frozen-plan");
  assert.equal(
    resolvePreviewState(current, { beta_headers: [], limits: { max_requests: 4 }, model: "one" })
      .previewId,
    "frozen-plan",
  );
  assert.equal(
    resolvePreviewState(current, { ...current.target, limits: { max_requests: 5 } }).previewId,
    null,
  );
});

test("URL helper resolves only explicit origin or v1 bases without host substitution", () => {
  assert.equal(
    resolveEndpoint("http://localhost:34567", "base"),
    "http://localhost:34567/v1/messages",
  );
  assert.equal(
    resolveEndpoint("https://example.test/v1/", "base"),
    "https://example.test/v1/messages",
  );
  assert.equal(
    resolveEndpoint("https://example.test/custom/messages", "messages"),
    "https://example.test/custom/messages",
  );
  for (const value of [
    "https://example.test/custom",
    "https://key:secret@example.test",
    "https://example.test/?key=secret",
    "https://example.test/#fragment",
    "https://example.test/ path",
  ]) {
    assert.throws(() => resolveEndpoint(value, "base"), /invalid_url|ambiguous_base_url/);
  }
});

test("alias set equivalence preserves preview without changing other array semantics", () => {
  const current = {
    target: { response_model_aliases: ["\ue000", "😀", "later"], beta_headers: ["a", "b"] },
    previewId: "frozen",
  };
  const edited = { ...current.target, response_model_aliases: ["later", "😀", "\ue000", "later"] };
  assert.equal(resolvePreviewState(current, edited).previewId, "frozen");
  assert.deepEqual(current.target.response_model_aliases, ["\ue000", "😀", "later"]);
  assert.equal(
    resolvePreviewState(current, { ...edited, response_model_aliases: ["different"] }).previewId,
    null,
  );
  assert.equal(
    resolvePreviewState(current, { ...edited, beta_headers: ["b", "a"] }).previewId,
    null,
  );
});
