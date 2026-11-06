import assert from "node:assert/strict";
import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { createServer as createTcpServer, type Socket } from "node:net";
import test, { type TestContext } from "node:test";
import { captureHttp, type HttpLimits } from "../../skills/anthropic-readiness/scripts/src/runner/http.ts";

async function peer(t: TestContext, handler: (req: IncomingMessage, res: ServerResponse) => void) {
  const server = createServer(handler);
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  t.after(async () => {
    server.closeAllConnections();
    await new Promise<void>((resolve) => server.close(() => resolve()));
  });
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("missing_fixture_address");
  return `http://127.0.0.1:${address.port}/v1/messages`;
}
const limits = { attemptMs: 2000, connectMs: 1000, readMs: 1000, maxBytes: 1024 };
const body = Buffer.from('{"model":"synthetic"}');

test("captures exact application bytes, duplicate headers and one POST without retries", async (t) => {
  let requests = 0;
  const bytes = Buffer.from([0x7b, 0xff, 0x7d]);
  const url = await peer(t, (req, res) => {
    requests++;
    assert.equal(req.method, "POST");
    assert.equal(req.headers["accept-encoding"], "identity");
    let sent = Buffer.alloc(0);
    req.on("data", (chunk: Buffer) => {
      sent = Buffer.concat([sent, chunk]);
    });
    req.on("end", () => {
      assert.deepEqual(sent, body);
      res.writeHead(503, ["x-observed", "first", "X-Observed", "second"]);
      res.end(bytes);
    });
  });
  const captured = await captureHttp({ url, body }, limits);
  assert.equal(captured.end, "eof");
  assert.equal(captured.statusCode, 503);
  assert.deepEqual(captured.body, bytes);
  assert.deepEqual(
    captured.headers.filter(([key]) => key.toLowerCase() === "x-observed"),
    [
      ["x-observed", "first"],
      ["X-Observed", "second"],
    ],
  );
  assert.equal(captured.receivedBytes, 3);
  assert.equal(requests, 1);
});

test("redirects remain observable responses and are never followed", async (t) => {
  let redirected = 0;
  const target = await peer(t, (_req, res) => {
    redirected++;
    res.end("unexpected");
  });
  const url = await peer(t, (_req, res) => {
    res.writeHead(307, { location: target });
    res.end();
  });
  const captured = await captureHttp({ url, body }, limits);
  assert.equal(captured.statusCode, 307);
  assert.equal(captured.end, "eof");
  assert.equal(redirected, 0);
});

test("connection failures expose a stable code without leaking request secrets", async (t) => {
  const url = await peer(t, (req) => req.socket.destroy());
  const captured = await captureHttp(
    { url, body, headers: [["authorization", "Bearer synthetic-private-key"]] },
    limits,
  );
  assert.equal(captured.end, "network_error");
  assert.match(captured.errorCode ?? "", /^[A-Z0-9_]+$/u);
  assert.equal(captured.statusCode, null);
  assert.doesNotMatch(JSON.stringify(captured), /synthetic-private-key|127\.0\.0\.1/u);
});

test("body limits preserve a bounded prefix without claiming complete evidence", async (t) => {
  const url = await peer(t, (_req, res) => res.end(Buffer.alloc(65536, 97)));
  const captured = await captureHttp({ url, body }, { ...limits, maxBytes: 17 });
  assert.equal(captured.end, "response_limit");
  assert.deepEqual(captured.body, Buffer.alloc(17, 97));
  assert.ok(captured.receivedBytes > captured.body.length);
});

test("idle reads retain received bytes and record timeout rather than a protocol verdict", async (t) => {
  const url = await peer(t, (_req, res) => {
    res.writeHead(200);
    res.write("prefix");
  });
  const captured = await captureHttp({ url, body }, { ...limits, readMs: 100 });
  assert.equal(captured.end, "read_timeout");
  assert.equal(captured.statusCode, 200);
  assert.equal(captured.body.toString(), "prefix");
});

test("an absolute attempt deadline bounds a response that keeps arriving", async (t) => {
  let timer: ReturnType<typeof setInterval>;
  const url = await peer(t, (_req, res) => {
    res.write("a");
    timer = setInterval(() => res.write("a"), 10);
    res.on("close", () => clearInterval(timer));
  });
  const captured = await captureHttp({ url, body }, { ...limits, attemptMs: 150 });
  assert.equal(captured.end, "attempt_timeout");
  assert.ok(captured.body.length > 0);
});

test("cancelling before admission makes no request; cancelling a read retains its prefix", async (t) => {
  let requests = 0;
  const url = await peer(t, (_req, res) => {
    requests++;
    res.write("prefix");
  });
  const aborted = new AbortController();
  aborted.abort();
  assert.equal(
    (await captureHttp({ url, body }, limits, { signal: aborted.signal })).end,
    "cancelled",
  );
  assert.equal(requests, 0);
  const active = new AbortController();
  const captured = await captureHttp({ url, body }, limits, {
    signal: active.signal,
    onProgress: (received) => {
      if (received > 0) active.abort();
    },
  });
  assert.equal(captured.end, "cancelled");
  assert.equal(captured.body.toString(), "prefix");
  assert.equal(requests, 1);
});

test("invalid budgets and credential-bearing URLs are rejected before network I/O", async () => {
  await assert.rejects(captureHttp({ url: "http://u:p@127.0.0.1/", body }, limits), /invalid_url/);
  await assert.rejects(captureHttp({ url: "file:///tmp/fixture", body }, limits), /invalid_url/);
  for (const bad of [0, -1, NaN, Infinity])
    await assert.rejects(
      captureHttp({ url: "http://127.0.0.1/", body }, { ...limits, maxBytes: bad }),
      /invalid_limits/,
    );
});

test("missing limit members are rejected rather than silently capturing an empty response", async (t) => {
  const url = await peer(t, (_req, res) => res.end("must not be requested"));
  const missing = {
    attemptMs: limits.attemptMs,
    connectMs: limits.connectMs,
    readMs: limits.readMs,
  };
  await assert.rejects(captureHttp({ url, body }, missing as HttpLimits), /invalid_limits/);
});

test("connection deadlines include a TLS handshake that never completes", async (t) => {
  const sockets = new Set<Socket>();
  const server = createTcpServer((socket) => {
    sockets.add(socket);
    socket.on("error", () => {});
    socket.on("data", () => {});
    socket.on("close", () => sockets.delete(socket));
  });
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  t.after(async () => {
    for (const socket of sockets) socket.destroy();
    await new Promise<void>((resolve) => server.close(() => resolve()));
  });
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("missing_fixture_address");
  const captured = await captureHttp(
    { url: `https://127.0.0.1:${address.port}/`, body },
    { ...limits, connectMs: 80 },
  );
  assert.equal(captured.end, "connect_timeout");
  assert.equal(captured.statusCode, null);
});
