import assert from "node:assert/strict";
import test from "node:test";
import { sameUIRevision } from "../../src/anthropic_readiness/resources/web/ui-update.js";
test("only two valid distinct UI identities establish a deployment change", () => {
  const revision = "a".repeat(64);
  assert.equal(sameUIRevision(revision, revision), true);
  assert.equal(sameUIRevision(revision, "b".repeat(64)), false);
  for (const value of [null, undefined, "", "new", "A".repeat(64), 42, {}]) {
    assert.equal(sameUIRevision(revision, value), true);
    assert.equal(sameUIRevision(value, revision), true);
  }
});
