import assert from "node:assert/strict";
import test from "node:test";
import {
  INPUT_HISTORY_KEY,
  readInputHistory,
  rememberInput,
  clearInputHistory,
} from "../../src/anthropic_readiness/resources/web/forms.js";

/** @returns {Pick<Storage,"getItem"|"setItem"|"removeItem">} */
function storage() {
  /** @type {Map<string,string>} */
  const values = new Map();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key),
  };
}

test("recent values are unique, most recent first and bounded independently", () => {
  const saved = storage();
  rememberInput(saved, "endpoints", " http://localhost:8000/v1 ");
  for (let n = 0; n < 25; n++) rememberInput(saved, "models", "model-" + n);
  rememberInput(saved, "models", "model-20");
  const result = readInputHistory(saved);
  assert.deepEqual(result.endpoints, ["http://localhost:8000/v1"]);
  assert.equal(result.models.length, 20);
  assert.deepEqual(result.models.slice(0, 3), ["model-20", "model-24", "model-23"]);
  assert.equal(new Set(result.models).size, 20);
});

test("corrupt and future documents are ignored; only valid allowed fields are retained", () => {
  const saved = storage();
  for (const value of ["{bad", "null", "[]", '{"version":2,"models":["ignored"]}']) {
    saved.setItem(INPUT_HISTORY_KEY, value);
    assert.deepEqual(readInputHistory(saved), { version: 1, endpoints: [], models: [] });
  }
  saved.setItem(
    INPUT_HISTORY_KEY,
    JSON.stringify({
      version: 1,
      credential: "synthetic-private-key",
      endpoints: ["https://example.test/v1", "https://key:secret@example.test", 123],
      models: ["valid-model", "bad\nmodel", {}, "valid-model"],
    }),
  );
  rememberInput(saved, "models", "next-model");
  assert.deepEqual(JSON.parse(saved.getItem(INPUT_HISTORY_KEY) ?? "null"), {
    version: 1,
    endpoints: ["https://example.test/v1"],
    models: ["next-model", "valid-model"],
  });
  assert.ok(!(saved.getItem(INPUT_HISTORY_KEY) ?? "").includes("synthetic-private-key"));
});

test("URLs containing credentials or query data and invalid values are never remembered", () => {
  const saved = storage();
  for (const endpoint of [
    "javascript:alert(1)",
    "https://user:secret@example.test/v1/messages",
    "https://example.test/v1?api_key=secret",
    "https://example.test/#secret",
    "not-a-url",
    "https://example.test/" + "x".repeat(2048),
  ])
    rememberInput(saved, "endpoints", endpoint);
  for (const model of ["", " ", "bad\nmodel", "x".repeat(513)])
    rememberInput(saved, "models", model);
  assert.equal(saved.getItem(INPUT_HISTORY_KEY), null);
});

test("unavailable or full storage does not block inputs, and clearing preserves unrelated keys", () => {
  const blocked = {
    getItem() {
      throw new Error("blocked");
    },
    setItem() {
      throw new Error("full");
    },
    removeItem() {
      throw new Error("blocked");
    },
  };
  assert.deepEqual(rememberInput(blocked, "models", "model"), {
    version: 1,
    endpoints: [],
    models: [],
  });
  assert.equal(clearInputHistory(blocked), false);
  assert.deepEqual(readInputHistory(null), { version: 1, endpoints: [], models: [] });
  const saved = storage();
  saved.setItem("unrelated", "keep");
  rememberInput(saved, "models", "model");
  assert.equal(clearInputHistory(saved), true);
  assert.equal(saved.getItem(INPUT_HISTORY_KEY), null);
  assert.equal(saved.getItem("unrelated"), "keep");
});
