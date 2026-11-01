import type { MessageValidationContext, Observation } from "../domain.ts";

type JsonObject = Record<string, unknown>;

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function pointerPart(value: string): string {
  return value.replaceAll("~", "~0").replaceAll("/", "~1");
}

function describe(value: unknown): string {
  if (value === null) return "null";
  if (Array.isArray(value)) return "array";
  if (typeof value === "number") {
    if (Number.isNaN(value)) return "number (NaN)";
    if (!Number.isFinite(value)) return "number (non-finite)";
    return Number.isInteger(value) ? "integer" : "fractional number";
  }
  return typeof value;
}

/** Validate the structure and selected-snapshot identity of one decoded message. */
export function validateMessage(
  value: unknown,
  context: MessageValidationContext,
): readonly Observation[] {
  const observations: Observation[] = [];
  const add = (
    ruleId: string,
    status: Observation["status"],
    reason: string,
    expected: string,
    actual: string,
    pointer: string,
    options: { required?: boolean; missingKey?: string } = {},
  ): void => {
    observations.push({
      ruleId,
      ruleVersion: 1,
      dimension: "protocol",
      status,
      required: options.required ?? true,
      reason,
      expected,
      actual,
      location: {
        captureId: context.captureId,
        pointer,
        ...(options.missingKey === undefined ? {} : { missingKey: options.missingKey }),
      },
    });
  };
  const field = (
    object: JsonObject,
    key: string,
    parent: string,
    ruleId: string,
    valid: (item: unknown) => boolean,
    expected: string,
  ): { present: boolean; value: unknown } => {
    const present = Object.hasOwn(object, key);
    const item = object[key];
    const location = present
      ? `${parent}/${pointerPart(key)}`
      : parent;
    const options = present ? {} : { missingKey: key };
    const passes = present && valid(item);
    add(
      ruleId,
      passes ? "PASS" : "FAIL",
      passes ? "field_valid" : present ? "invalid_field" : "missing_field",
      expected,
      present ? describe(item) : "missing",
      location,
      options,
    );
    return { present, value: item };
  };

  if (!isObject(value)) {
    add("MSG-CORE", "FAIL", "message_not_object", "JSON object", describe(value), "");
    return observations;
  }

  field(value, "id", "", "MSG-ID", (item) => typeof item === "string" && item.length > 0, "nonempty string");
  field(value, "type", "", "MSG-TYPE", (item) => item === "message", 'string "message"');
  field(value, "role", "", "MSG-ROLE", (item) => item === "assistant", 'string "assistant"');
  const model = field(value, "model", "", "MSG-MODEL-FIELD", (item) => typeof item === "string" && item.length > 0, "nonempty string");
  const content = field(value, "content", "", "MSG-CONTENT-FIELD", Array.isArray, "array");
  const stopReasonPresent = Object.hasOwn(value, "stop_reason");
  const stopReasonValue = value.stop_reason;
  const stopSequence = field(value, "stop_sequence", "", "MSG-STOP-SEQUENCE-FIELD", (item) => item === null || typeof item === "string", "string or null");

  const usageField = field(value, "usage", "", "MSG-USAGE", isObject, "JSON object");
  if (usageField.present && isObject(usageField.value)) {
    field(usageField.value, "input_tokens", "/usage", "MSG-INPUT-TOKENS", (item) => typeof item === "number" && Number.isInteger(item) && item >= 0, "nonnegative integer");
    field(usageField.value, "output_tokens", "/usage", "MSG-OUTPUT-TOKENS", (item) => typeof item === "number" && Number.isInteger(item) && item >= 0, "nonnegative integer");
  }

  add("MSG-CORE", "PASS", "message_object", "JSON object at message root", "object", "");

  if (model.present && typeof model.value === "string" && model.value.length > 0) {
    if (!context.checkModelIdentity) {
      add("MSG-MODEL", "SKIP", "identity_not_checked", "requested model or configured alias", "identity check disabled", "/model", { required: false });
    } else {
      const matches = model.value === context.requestedModel || context.modelAliases.includes(model.value);
      add("MSG-MODEL", matches ? "PASS" : "FAIL", matches ? "model_identity_matches" : "model_identity_mismatch", "requested model or configured alias", matches ? "configured identity" : "different model identity", "/model");
    }
  }

  if (!stopReasonPresent) {
    add("MSG-STOP", "FAIL", "missing_field", "reason in selected protocol snapshot", "missing", "", { missingKey: "stop_reason" });
  } else if (typeof stopReasonValue !== "string") {
    add("MSG-STOP", "FAIL", "invalid_stop_reason", "string stop reason", describe(stopReasonValue), "/stop_reason");
  } else {
    const knownStopReason = context.stopReasons.includes(stopReasonValue);
    add("MSG-STOP", knownStopReason ? "PASS" : "INDETERMINATE", knownStopReason ? "stop_reason_known" : "unknown_stop_reason", "reason in selected protocol snapshot", knownStopReason ? "known stop reason" : "unrecognized stop reason", "/stop_reason");
  }

  if (stopReasonPresent && stopSequence.present) {
    const knownReason = typeof stopReasonValue === "string" && context.stopReasons.includes(stopReasonValue);
    const requiresString = stopReasonValue === "stop_sequence";
    const valid = knownReason && (requiresString
      ? typeof stopSequence.value === "string"
      : stopSequence.value === null);
    const status = !knownReason
      ? "INDETERMINATE"
      : valid ? "PASS" : "FAIL";
    add(
      "MSG-STOP-SEQUENCE",
      status,
      !knownReason ? "stop_sequence_relation_unknown" : valid ? "stop_sequence_valid" : "unexpected_stop_sequence",
      "string when reason is stop_sequence; otherwise null",
      describe(stopSequence.value),
      "/stop_sequence",
    );
  } else if (!stopSequence.present) {
    // The field-level observation above already describes the missing member.
  }

  if (content.present && Array.isArray(content.value)) {
    content.value.forEach((block: unknown, index: number) => {
      const blockPointer = `/content/${index}`;
      if (!isObject(block)) {
        add("MSG-CONTENT", "FAIL", "content_block_not_object", "JSON object", describe(block), blockPointer);
        return;
      }
      if (!Object.hasOwn(block, "type")) {
        add("MSG-CONTENT", "FAIL", "content_block_type_missing", "string block type", "missing", blockPointer, { missingKey: "type" });
        return;
      }
      if (typeof block.type !== "string") {
        add("MSG-CONTENT", "FAIL", "content_block_type_invalid", "string block type", describe(block.type), `${blockPointer}/type`);
        return;
      }
      if (block.type === "text") {
        field(block, "text", blockPointer, "MSG-TEXT", (item) => typeof item === "string", "string");
      } else if (block.type === "tool_use") {
        field(block, "id", blockPointer, "MSG-TOOL-ID", (item) => typeof item === "string" && item.length > 0, "nonempty string");
        field(block, "name", blockPointer, "MSG-TOOL-NAME", (item) => typeof item === "string" && item.length > 0, "nonempty string");
        field(block, "input", blockPointer, "MSG-TOOL-INPUT", isObject, "JSON object");
      } else {
        add("MSG-CONTENT", "INDETERMINATE", "unknown_content_type", "recognized content block type", "unrecognized content block type", `${blockPointer}/type`);
      }
    });
  }

  return observations;
}
