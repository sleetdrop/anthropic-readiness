import { object, objects } from "./forms.js";
/** @typedef {import("./forms.js").JsonObject} JsonObject */
/** @typedef {{case_id:string,state:string,checkpoint_path:string|null,checkpoint_sha256:string|null}} CaseState */
/** @typedef {{schema_version:string,run_id:string,config_sha256:string,target:JsonObject,contract:JsonObject,plan:JsonObject,sequence:number,state:string,case_states:CaseState[],actual_requests:number,elapsed_ms:number,started_at:string,updated_at:string,finished_at:string|null,spans:JsonObject[],warnings:string[],result_sha256:string|null,terminal_reason:string|null}} Execution */
/** @typedef {{execution:Execution|null,needsSnapshot:boolean}} ProgressState */
const JOB_STATES = [
  "queued",
  "running",
  "cancelling",
  "completed",
  "cancelled",
  "interrupted",
  "error",
];
const CASE_STATES = ["pending", "running", "PASS", "FAIL", "INDETERMINATE", "BLOCKED", "SKIP"];

/** @param {unknown} value @returns {Execution|null} */
export function parseExecution(value) {
  if (value === null) return null;
  const data = object(value);
  if (
    !Number.isInteger(data.sequence) ||
    Number(data.sequence) < 0 ||
    !JOB_STATES.includes(String(data.state)) ||
    !Array.isArray(data.case_states) ||
    !Number.isFinite(data.actual_requests) ||
    !Number.isFinite(data.elapsed_ms)
  )
    throw new Error("invalid_snapshot");
  for (const item of objects(data.case_states)) {
    if (typeof item.case_id !== "string" || !CASE_STATES.includes(String(item.state)))
      throw new Error("invalid_snapshot");
  }
  return /** @type {Execution} */ (/** @type {unknown} */ (data));
}

/** @param {ProgressState} snapshot @param {{type:string,value:unknown}} event @returns {ProgressState} */
export function reduceSnapshot(snapshot, event) {
  if (event.type === "snapshot" || event.type === "reset") {
    const value = parseExecution(event.value);
    if (
      event.type === "snapshot" &&
      value &&
      snapshot.execution &&
      value.sequence < snapshot.execution.sequence
    )
      return snapshot;
    return { execution: value, needsSnapshot: false };
  }
  if (event.type !== "progress") return snapshot;
  const data = object(event.value);
  const current = snapshot.execution;
  if (!current) return { ...snapshot, needsSnapshot: true };
  if (
    data.run_id !== current.run_id ||
    !Number.isInteger(data.sequence) ||
    data.schema_version !== "1.0"
  )
    return { ...snapshot, needsSnapshot: true };
  const sequence = Number(data.sequence);
  if (sequence <= current.sequence) return snapshot;
  if (sequence !== current.sequence + 1) return { ...snapshot, needsSnapshot: true };
  const result = structuredClone(current);
  const payload = object(data.payload);
  const state = result.case_states.find((item) => item.case_id === payload.case_id);
  if (data.kind === "case_started" && state) state.state = "running";
  if (data.kind === "case_committed" && state) {
    if (!CASE_STATES.includes(String(payload.status))) return { ...snapshot, needsSnapshot: true };
    state.state = String(payload.status);
    state.checkpoint_path = String(payload.checkpoint_path);
    state.checkpoint_sha256 = String(payload.sha256);
  }
  if (data.kind === "request_started") {
    if (payload.request_index !== current.actual_requests + 1)
      return { ...snapshot, needsSnapshot: true };
    result.actual_requests = Number(payload.request_index);
  }
  if (data.kind === "job_transition" && JOB_STATES.includes(String(payload.to)))
    result.state = String(payload.to);
  if (data.kind === "result_committed") result.result_sha256 = String(payload.sha256);
  if (!Number.isFinite(data.elapsed_ms) || Number(data.elapsed_ms) < current.elapsed_ms)
    return { ...snapshot, needsSnapshot: true };
  result.sequence = sequence;
  result.elapsed_ms = Number(data.elapsed_ms);
  result.updated_at = String(data.occurred_at);
  return { execution: result, needsSnapshot: false };
}
