/** Pure, bounded reading projections. No protocol verdicts are generated here. */
/** @typedef {import('./contracts.js').JsonValue} JsonValue */
/** @typedef {{pointer:string,missing:boolean}} ReadingTarget */
/** @param {JsonValue} value @param {string} pointer */
export function locatePointer(value, pointer) {
  let current = value,
    existing = "";
  if (pointer && !pointer.startsWith("/")) return { pointer: "", missing: true };
  for (const part of pointer ? pointer.slice(1).split("/") : []) {
    const key = part.replace(/~1/gu, "/").replace(/~0/gu, "~");
    if (current === null || typeof current !== "object" || !Object.hasOwn(current, key))
      return { pointer: existing, missing: true };
    current = /** @type {Record<string,JsonValue>} */ (current)[key] ?? null;
    existing += "/" + part;
  }
  return { pointer: existing, missing: false };
}
/** @param {JsonValue} value @param {string} pointer @returns {JsonValue} */
export function pointerValue(value, pointer) {
  let current = value;
  for (const part of pointer ? pointer.slice(1).split("/") : []) {
    if (current === null || typeof current !== "object") return null;
    current =
      /** @type {Record<string,JsonValue>} */ (current)[
        part.replace(/~1/gu, "/").replace(/~0/gu, "~")
      ] ?? null;
  }
  return current;
}
/** Known display associations only; unknown compound failures retain no node marker.
 * @param {JsonValue} value @param {string|null} pointer @param {string} reason @returns {ReadingTarget|null}
 */
export function readingTarget(value, pointer, reason) {
  if (pointer === null && value && typeof value === "object" && !Array.isArray(value)) {
    const start = value.type === "message_start";
    const message = start ? value.message : value;
    const base = start ? "/message" : "";
    if (reason === "duplicate_message_start" && start) pointer = "/type";
    if (
      message &&
      typeof message === "object" &&
      !Array.isArray(message) &&
      message.type === "message"
    ) {
      if (reason === "model_identity_mismatch") pointer = base + "/model";
      if (reason === "invalid_stop_reason" || reason === "unknown_stop_reason")
        pointer = base + "/stop_reason";
      if (reason === "unexpected_stop_sequence") pointer = base + "/stop_sequence";
      if (reason === "invalid_message_structure" || reason === "invalid_initial_message") {
        const missing = ["stop_reason", "stop_sequence"].find(
          (key) => !Object.hasOwn(message, key),
        );
        if (missing) pointer = base + "/" + missing;
        else {
          const usage = message.usage;
          if (!usage || typeof usage !== "object" || Array.isArray(usage))
            pointer = base + "/usage";
          else {
            const key = ["input_tokens", "output_tokens"].find(
              (key) =>
                typeof usage[key] !== "number" || !Number.isInteger(usage[key]) || usage[key] < 0,
            );
            if (key) pointer = base + "/usage/" + key;
          }
        }
      }
    }
  }
  if (pointer === null || !/^(?:\/(?:[^~]|~[01])*)*$/u.test(pointer)) return null;
  const found = locatePointer(value, pointer);
  const parent = pointerValue(value, found.pointer);
  return found.missing && (parent === null || typeof parent !== "object") ? null : found;
}
/** @typedef {{pointer:string,text:string,start:number,length:number,container:boolean,expanded:boolean,closing:boolean,depthLimited:boolean}} JsonRow */
/** @param {JsonValue} value @param {Set<string>} expanded @param {number} [limit] @param {string|null} [focus] */
export function jsonRows(value, expanded, limit = 500, focus = null) {
  /** @param {JsonValue} data @param {string} pointer @param {number} depth @param {string|null} key @param {string} comma @returns {Generator<JsonRow>} */
  function* walk(data, pointer, depth, key, comma) {
    const prefix = "  ".repeat(depth) + (key === null ? "" : JSON.stringify(key) + ": ");
    const container = data !== null && typeof data === "object";
    const depthLimited = container && depth >= 64;
    const open = container && expanded.has(pointer) && !depthLimited;
    const literal = container ? (Array.isArray(data) ? "[" : "{") : JSON.stringify(data);
    const close = Array.isArray(data) ? "]" : "}";
    yield {
      pointer,
      text: prefix + literal + (container ? (open ? "" : " … " + close + comma) : comma),
      start: prefix.length,
      length: literal.length,
      container: container && !depthLimited,
      expanded: open,
      closing: false,
      depthLimited,
    };
    if (open) {
      const entries = Object.entries(/** @type {Record<string,JsonValue>} */ (data));
      for (let index = 0; index < entries.length; index++) {
        const [name, child] = entries[index];
        yield* walk(
          child,
          pointer + "/" + name.replace(/~/gu, "~0").replace(/\//gu, "~1"),
          depth + 1,
          Array.isArray(data) ? null : name,
          index < entries.length - 1 ? "," : "",
        );
      }
      yield {
        pointer,
        text: "  ".repeat(depth) + close + comma,
        start: 0,
        length: 0,
        container: false,
        expanded: false,
        closing: true,
        depthLimited: false,
      };
    }
  }
  let start = 0;
  if (focus !== null) {
    let index = 0;
    for (const row of walk(value, "", 0, null, "")) {
      if (!row.closing && row.pointer === focus) {
        if (index >= limit) start = index - Math.floor(limit / 3);
        break;
      }
      index++;
    }
  }
  /** @type {JsonRow[]} */ const rows = [];
  let index = 0,
    limited = false;
  for (const row of walk(value, "", 0, null, "")) {
    if (index++ < start) continue;
    if (rows.length >= limit) {
      limited = true;
      break;
    }
    rows.push(row);
  }
  return { rows, limited, start };
}
