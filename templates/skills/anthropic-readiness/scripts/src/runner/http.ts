/** One bounded HTTP attempt. Capture application bytes without SDK normalization. */
import { request as httpRequest, type ClientRequest, type IncomingMessage } from "node:http";
import { request as httpsRequest } from "node:https";
import { performance } from "node:perf_hooks";

export interface HttpLimits {
  readonly attemptMs: number;
  readonly connectMs: number;
  readonly readMs: number;
  readonly maxBytes: number;
}
export interface HttpInput {
  readonly url: string;
  readonly body: Uint8Array;
  readonly headers?: readonly (readonly [string, string])[];
}
export type CaptureEnd =
  | "eof"
  | "connect_timeout"
  | "read_timeout"
  | "attempt_timeout"
  | "response_limit"
  | "cancelled"
  | "network_error"
  | "observer_error";
export interface HttpCapture {
  readonly statusCode: number | null;
  readonly headers: readonly (readonly [string, string])[];
  /** Encoded application bytes, before content decoding; never called wire packets. */
  readonly body: Buffer;
  readonly receivedBytes: number;
  readonly end: CaptureEnd;
  readonly errorCode: string | null;
  readonly elapsedMs: number;
  readonly headersMs: number | null;
  readonly firstByteMs: number | null;
}
export interface CaptureOptions {
  readonly signal?: AbortSignal;
  /** Received-byte counts, never credentials or body data. Exceptions stop the attempt. */
  readonly onProgress?: (receivedBytes: number) => void;
}

export async function captureHttp(
  input: HttpInput,
  limits: HttpLimits,
  options: CaptureOptions = {},
): Promise<HttpCapture> {
  let url: URL;
  try {
    url = new URL(input.url);
  } catch {
    throw new Error("invalid_url");
  }
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || url.hash)
    throw new Error("invalid_url");
  if (
    ![limits.attemptMs, limits.connectMs, limits.readMs, limits.maxBytes].every(
      (value) => Number.isSafeInteger(value) && value > 0,
    )
  )
    throw new Error("invalid_limits");
  const headers = [...(input.headers ?? [])];
  if (!headers.some(([name]) => name.toLowerCase() === "host")) headers.push(["host", url.host]);
  if (!headers.some(([name]) => name.toLowerCase() === "accept-encoding"))
    headers.push(["accept-encoding", "identity"]);
  if (!headers.some(([name]) => name.toLowerCase() === "content-length"))
    headers.push(["content-length", String(input.body.byteLength)]);

  return new Promise((resolve) => {
    const started = performance.now();
    const chunks: Buffer[] = [];
    let retained = 0,
      received = 0;
    let statusCode: number | null = null;
    const responseHeaders: [string, string][] = [];
    let headersMs: number | null = null,
      firstByteMs: number | null = null;
    let done = false;
    let errorCode: string | null = null;
    let request: ClientRequest | undefined;
    let response: IncomingMessage | undefined;
    let readTimer: ReturnType<typeof setTimeout> | undefined;
    let connectTimer: ReturnType<typeof setTimeout> | undefined;
    let attemptTimer: ReturnType<typeof setTimeout> | undefined;
    const abort = () => finish("cancelled");
    function finish(end: CaptureEnd) {
      if (done) return;
      done = true;
      clearTimeout(readTimer);
      clearTimeout(connectTimer);
      clearTimeout(attemptTimer);
      options.signal?.removeEventListener("abort", abort);
      response?.destroy();
      request?.destroy();
      resolve({
        statusCode,
        headers: responseHeaders,
        body: Buffer.concat(chunks, retained),
        receivedBytes: received,
        end,
        errorCode,
        elapsedMs: performance.now() - started,
        headersMs,
        firstByteMs,
      });
    }
    function resetRead() {
      clearTimeout(readTimer);
      readTimer = setTimeout(() => finish("read_timeout"), limits.readMs);
    }
    function connected() {
      if (done) return;
      clearTimeout(connectTimer);
      resetRead();
    }
    if (options.signal?.aborted) {
      finish("cancelled");
      return;
    }
    options.signal?.addEventListener("abort", abort, { once: true });
    attemptTimer = setTimeout(() => finish("attempt_timeout"), limits.attemptMs);
    connectTimer = setTimeout(() => finish("connect_timeout"), limits.connectMs);
    try {
      const send = url.protocol === "https:" ? httpsRequest : httpRequest;
      request = send(url, {
        method: "POST",
        headers: headers.flatMap(([key, value]) => [key, value]),
        agent: false,
      });
      const failed = (error: Error & { code?: string }) => {
        if (!done && error.code && /^[A-Z0-9_]{1,80}$/u.test(error.code)) errorCode = error.code;
        finish("network_error");
      };
      request.on("error", failed);
      request.once("socket", (socket) => {
        if (!socket.connecting && url.protocol === "http:") connected();
        else socket.once(url.protocol === "https:" ? "secureConnect" : "connect", connected);
      });
      request.once("response", (incoming) => {
        response = incoming;
        if (done) {
          incoming.destroy();
          return;
        }
        clearTimeout(connectTimer);
        resetRead();
        statusCode = incoming.statusCode ?? null;
        headersMs = performance.now() - started;
        for (let index = 0; index < incoming.rawHeaders.length; index += 2)
          responseHeaders.push([incoming.rawHeaders[index]!, incoming.rawHeaders[index + 1]!]);
        incoming.on("data", (chunk: Buffer) => {
          if (done) return;
          firstByteMs ??= performance.now() - started;
          received += chunk.length;
          const room = limits.maxBytes - retained;
          const prefix = chunk.subarray(0, room);
          chunks.push(Buffer.from(prefix));
          retained += prefix.length;
          resetRead();
          try {
            options.onProgress?.(received);
          } catch {
            finish("observer_error");
            return;
          }
          if (chunk.length > room) finish("response_limit");
        });
        incoming.once("end", () => finish(incoming.complete ? "eof" : "network_error"));
        incoming.once("aborted", () => {
          if (!done) errorCode = "RESPONSE_ABORTED";
          finish("network_error");
        });
        incoming.once("error", failed);
      });
      request.end(input.body);
    } catch {
      finish("network_error");
    }
  });
}
