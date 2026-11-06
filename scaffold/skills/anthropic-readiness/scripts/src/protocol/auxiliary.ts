import type { Observation } from "../domain.ts";

const object = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

export function validateAuxiliary(
  value: unknown,
  captureId: string,
  kind: "count_tokens" | "invalid_request",
): Observation[] {
  const observations: Observation[] = [];
  function check(
    ruleId: string,
    parent: Record<string, unknown>,
    key: string,
    pointer: string,
    expected: string,
    valid: boolean,
  ): void {
    const present = Object.hasOwn(parent, key);
    observations.push({
      ruleId,
      ruleVersion: 1,
      dimension: "protocol",
      required: true,
      status: valid ? "PASS" : "FAIL",
      reason: valid ? "field_valid" : present ? "invalid_field" : "missing_field",
      expected,
      actual: valid
        ? expected
        : present
          ? parent[key] === null
            ? "null"
            : typeof parent[key]
          : "missing",
      location: present
        ? { captureId, pointer: `${pointer}/${key}` }
        : { captureId, pointer, missingKey: key },
    });
  }
  if (!object(value)) {
    return [
      {
        ruleId: "AUX-OBJECT",
        ruleVersion: 1,
        dimension: "protocol",
        required: true,
        status: "FAIL",
        reason: "response_not_object",
        expected: "JSON object",
        actual: value === null ? "null" : Array.isArray(value) ? "array" : typeof value,
        location: { captureId, pointer: "" },
      },
    ];
  }
  if (kind === "count_tokens") {
    check(
      "COUNT-INPUT",
      value,
      "input_tokens",
      "",
      "positive integer",
      typeof value.input_tokens === "number" &&
        Number.isSafeInteger(value.input_tokens) &&
        value.input_tokens > 0,
    );
    return observations;
  }
  check("ERROR-TYPE", value, "type", "", "error", value.type === "error");
  check("ERROR-DETAIL", value, "error", "", "JSON object", object(value.error));
  if (object(value.error)) {
    check(
      "ERROR-CODE",
      value.error,
      "type",
      "/error",
      "invalid_request_error",
      value.error.type === "invalid_request_error",
    );
    check(
      "ERROR-MESSAGE",
      value.error,
      "message",
      "/error",
      "nonempty string",
      typeof value.error.message === "string" && value.error.message.trim().length > 0,
    );
  }
  return observations;
}
