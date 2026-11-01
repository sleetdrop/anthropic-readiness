import assert from "node:assert/strict";
import test from "node:test";
import {
  evidenceFrames,
  contextFrames,
  locatePointer,
} from "../../src/anthropic_readiness/resources/web/evidence-view.js";

test("SSE event numbers preserve comments, multiline data, and original frame bytes", () => {
  const raw =
    ': keepalive\r\n\r\nevent: message_start\r\ndata: {"type":\r\ndata: "message_start"}\r\n\r\nevent: broken\ndata: {bad}\n\n';
  const frames = evidenceFrames(raw, true);
  assert.equal(frames.length, 2);
  assert.equal(frames[0].event, 0);
  assert.equal(frames[0].label, "message_start");
  assert.deepEqual(frames[0].value, { type: "message_start" });
  assert.equal(
    frames[0].raw,
    'event: message_start\r\ndata: {"type":\r\ndata: "message_start"}\r\n\r\n',
  );
  assert.equal(frames[1].value, null);
  assert.match(frames[1].raw, /\{bad\}/u);
});

test("context includes lifecycle start and search reaches beyond the local window", () => {
  const frames = evidenceFrames(
    Array.from(
      { length: 300 },
      (_, n) => `event: ${n === 0 ? "message_start" : "content_block_delta"}\ndata: {"n":${n}}\n\n`,
    ).join(""),
    true,
  );
  assert.deepEqual(
    contextFrames(frames, 230, "").map((f) => f.event),
    [0, 228, 229, 230, 231, 232],
  );
  assert.deepEqual(
    contextFrames(frames, 230, '"n":14').map((f) => f.event),
    [14, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149],
  );
});

test("missing JSON pointers locate their real parent without inventing a value", () => {
  assert.deepEqual(locatePointer({ message: { model: "alias" } }, "/message/stop_sequence"), {
    pointer: "/message",
    missing: true,
  });
  assert.deepEqual(locatePointer({ "a/b": { "~key": null } }, "/a~1b/~0key"), {
    pointer: "/a~1b/~0key",
    missing: false,
  });
  assert.deepEqual(locatePointer({}, "/constructor/prototype"), { pointer: "", missing: true });
});

test("persisted event records keep their checked sequence and ignore incomplete trailing records", () => {
  const source =
    '{"sequence":0,"event":"message_start","data":"{\\"type\\":\\"message_start\\"}"}\n';
  const frames = evidenceFrames(source + '{"sequence":1,"data":', "events");
  assert.equal(frames.length, 1);
  assert.equal(frames[0].raw, source);
  assert.deepEqual(frames[0].value, { type: "message_start" });
  assert.equal(evidenceFrames(source.replace('"sequence":0', '"sequence":3'), "events").length, 0);
});
