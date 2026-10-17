import assert from "node:assert/strict";
import test from "node:test";
import { api } from "../../src/anthropic_readiness/resources/web/app.js";

test("session recovery retries reads once and then stops", async (context) => {
  let reads = 0;
  let sessions = 0;
  /** @type {typeof fetch} */
  const peer = async (resource) => {
    if (String(resource).endsWith("/session")) {
      sessions += 1;
      return Response.json({ csrf_token: "synthetic" });
    }
    reads += 1;
    if (reads > 2) throw new Error("unbounded_session_retries");
    return Response.json(
      { error: { code: "session_required", message: "会话已失效" } },
      { status: 401 },
    );
  };
  context.mock.method(globalThis, "fetch", peer);
  await assert.rejects(api("/api/v1/runs/synthetic"), /会话/);
  assert.equal(reads, 2);
  assert.equal(sessions, 1);
});

test("recovering a session never automatically resubmits a start", async (context) => {
  let posts = 0;
  /** @type {typeof fetch} */
  const peer = async (resource, options) => {
    if (String(resource).endsWith("/session")) return Response.json({ csrf_token: "synthetic" });
    if (options?.method === "POST") posts += 1;
    return Response.json(
      { error: { code: "csrf_invalid", message: "会话已失效" } },
      { status: 403 },
    );
  };
  context.mock.method(globalThis, "fetch", peer);
  await assert.rejects(api("/api/v1/runs", { method: "POST", body: {} }), /未自动重发/);
  assert.equal(posts, 1);
});
