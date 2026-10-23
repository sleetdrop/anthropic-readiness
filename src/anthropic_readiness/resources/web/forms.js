/** @typedef {import("./contracts.js").JsonValue} JsonValue */
/** @typedef {import("./contracts.js").JsonObject} JsonObject */
/** @typedef {{target:JsonObject,previewId:string|null}} PreviewState */

/** @param {JsonValue} value @returns {JsonValue} */
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, canonical(value[key])]),
    );
  }
  return value;
}

/** Compare the alias membership used by the server, independent of input order.
 * @param {JsonObject} value @returns {JsonValue}
 */
function comparableTarget(value) {
  const target = { ...value };
  if (Array.isArray(target.response_model_aliases))
    target.response_model_aliases = [...new Set(strings(target.response_model_aliases))].sort();
  return canonical(target);
}

/** @param {PreviewState} current @param {JsonObject} edited @returns {PreviewState} */
export function resolvePreviewState(current, edited) {
  return {
    target: structuredClone(edited),
    previewId:
      JSON.stringify(comparableTarget(current.target)) === JSON.stringify(comparableTarget(edited))
        ? current.previewId
        : null,
  };
}

/** @param {string} value @param {string} mode @returns {string} */
export function resolveEndpoint(value, mode) {
  let parsed;
  try {
    parsed = new URL(value);
  } catch {
    throw new Error("invalid_url");
  }
  if (
    !["http:", "https:"].includes(parsed.protocol) ||
    parsed.username ||
    parsed.password ||
    /[?#\s]/u.test(value) ||
    Array.from(value).some((character) => character.charCodeAt(0) < 32) ||
    !["base", "messages", "auto"].includes(mode)
  )
    throw new Error("invalid_url");
  if (mode === "messages") return value;
  if (mode === "auto" && parsed.pathname.endsWith("/messages")) return value;
  if (parsed.pathname === "/") return value.replace(/\/+$/, "") + "/v1/messages";
  if (["/v1", "/v1/"].includes(parsed.pathname)) return value.replace(/\/+$/, "") + "/messages";
  throw new Error("ambiguous_base_url");
}

/** @param {unknown} value @returns {JsonObject} */
export function object(value) {
  if (value === null || typeof value !== "object" || Array.isArray(value))
    throw new Error("invalid_document");
  return /** @type {JsonObject} */ (value);
}

/** @param {JsonValue|undefined} value @returns {JsonObject[]} */
export function objects(value) {
  if (!Array.isArray(value)) return [];
  return value.map(object);
}

/** @param {JsonValue|undefined} value @returns {string[]} */
export function strings(value) {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string"))
    throw new Error("invalid_document");
  return /** @type {string[]} */ (value);
}
