import assert from "node:assert/strict";
import test from "node:test";
import { validateMessage } from "../../src/protocol/messages.ts";
import { summarize, type MessageValidationContext, type Observation } from "../../src/domain.ts";

const context: MessageValidationContext = {
  captureId: "capture-1",
  requestedModel: "model-a",
  modelAliases: ["model-alias"],
  checkModelIdentity: true,
  stopReasons: ["end_turn", "max_tokens", "stop_sequence", "tool_use"],
};

function validTextMessage(): Record<string, unknown> {
  return {
    id: "msg-1",
    type: "message",
    role: "assistant",
    model: "model-a",
    content: [{ type: "text", text: "Hello." }],
    stop_reason: "end_turn",
    stop_sequence: null,
    usage: { input_tokens: 8, output_tokens: 2 },
  };
}

function byRule(
  observations: readonly Observation[],
  ruleId: string,
): Observation {
  const observation = observations.find((item) => item.ruleId === ruleId);
  assert.ok(observation, `expected observation ${ruleId}`);
  return observation;
}

test("accepts structurally valid text and tool-use messages", () => {
  const text = validateMessage(validTextMessage(), context);
  assert.equal(summarize(text), "PASS");
  assert.equal(byRule(text, "MSG-CORE").status, "PASS");
  assert.equal(byRule(text, "MSG-CORE").expected, "JSON object at message root");
  assert.equal(byRule(text, "MSG-STOP").status, "PASS");
  assert.equal(byRule(text, "MSG-STOP-SEQUENCE").status, "PASS");
  assert.equal(byRule(text, "MSG-MODEL").status, "PASS");

  const tool = validTextMessage();
  tool.content = [{
    type: "tool_use",
    id: "tool-1",
    name: "lookup",
    input: { query: "weather" },
  }];
  tool.stop_reason = "tool_use";
  const toolObservations = validateMessage(tool, context);
  assert.equal(summarize(toolObservations), "PASS");
  assert.equal(byRule(toolObservations, "MSG-CORE").status, "PASS");
});

test("reports every missing required field at its existing parent", () => {
  const cases: readonly [string, string, string, string?][] = [
    ["id", "id", ""],
    ["type", "type", ""],
    ["role", "role", ""],
    ["model", "model", ""],
    ["content", "content", ""],
    ["stop_reason", "stop_reason", ""],
    ["stop_sequence", "stop_sequence", ""],
    ["usage", "usage", ""],
    ["input_tokens", "input_tokens", "/usage", "usage"],
    ["output_tokens", "output_tokens", "/usage", "usage"],
  ];

  for (const [key, expectedKey, pointer, parent] of cases) {
    const message = validTextMessage();
    if (parent) {
      const usage = { ...(message.usage as Record<string, unknown>) };
      delete usage[key];
      message.usage = usage;
    } else {
      delete message[key];
    }
    const failed = validateMessage(message, context).filter((item) => item.status === "FAIL");
    const observation = failed.find((item) => item.location?.missingKey === expectedKey);
    assert.ok(observation, `missing ${key} should have its own failure`);
    assert.equal(observation.location?.pointer, pointer);
    assert.equal(observation.location?.captureId, context.captureId);
  }
});

test("rejects wrong required field types and values with field locations", () => {
  const cases: readonly [string, unknown, string][] = [
    ["id", "", "/id"],
    ["id", 1, "/id"],
    ["type", "not-message", "/type"],
    ["role", "user", "/role"],
    ["model", "", "/model"],
    ["content", {}, "/content"],
    ["stop_sequence", 1, "/stop_sequence"],
  ];
  for (const [key, value, pointer] of cases) {
    const message = validTextMessage();
    message[key] = value;
    const observation = validateMessage(message, context).find(
      (item) => item.status === "FAIL" && item.location?.pointer === pointer,
    );
    assert.ok(observation, `${key}=${String(value)} should fail at ${pointer}`);
  }
});

test("requires usage and tool inputs to be objects, not arrays or null", () => {
  for (const usage of [[], null]) {
    const message = validTextMessage();
    message.usage = usage;
    const observation = validateMessage(message, context).find(
      (item) => item.status === "FAIL" && item.location?.pointer === "/usage",
    );
    assert.ok(observation, "usage must be a JSON object");
  }

  for (const input of [[], null]) {
    const message = validTextMessage();
    message.content = [{ type: "tool_use", id: "tool-1", name: "lookup", input }];
    const observation = validateMessage(message, context).find(
      (item) => item.status === "FAIL" && item.location?.pointer === "/content/0/input",
    );
    assert.ok(observation, "tool input must be a JSON object");
  }
});

test("validates each known text and tool-use block field", () => {
  const malformedBlocks: readonly [unknown, string, string?][] = [
    [{ type: "text", text: 4 }, "MSG-TEXT", "/content/0/text"],
    [{ type: "tool_use", id: "", name: "lookup", input: {} }, "MSG-TOOL-ID", "/content/0/id"],
    [{ type: "tool_use", id: "tool-1", name: "", input: {} }, "MSG-TOOL-NAME", "/content/0/name"],
    [{ type: "tool_use", id: "tool-1", name: "lookup", input: [] }, "MSG-TOOL-INPUT", "/content/0/input"],
  ];
  for (const [block, ruleId, pointer] of malformedBlocks) {
    const message = validTextMessage();
    message.content = [block];
    const observation = byRule(validateMessage(message, context), ruleId);
    assert.equal(observation.status, "FAIL");
    assert.equal(observation.location?.pointer, pointer);
  }

  const missingText = validTextMessage();
  missingText.content = [{ type: "text" }];
  const missing = byRule(validateMessage(missingText, context), "MSG-TEXT");
  assert.equal(missing.status, "FAIL");
  assert.equal(missing.location?.pointer, "/content/0");
  assert.equal(missing.location?.missingKey, "text");
});

test("token counts reject booleans, fractions, negative values, and nonnumbers", () => {
  for (const value of [true, 1.5, -1, "2", null]) {
    for (const key of ["input_tokens", "output_tokens"]) {
      const message = validTextMessage();
      (message.usage as Record<string, unknown>)[key] = value;
      const pointer = `/usage/${key}`;
      const observation = validateMessage(message, context).find(
        (item) => item.status === "FAIL" && item.location?.pointer === pointer,
      );
      assert.ok(observation, `${key}=${String(value)} should fail at ${pointer}`);
    }
  }
});

test("accepts requested model and explicit aliases, reports mismatches, skips disabled identity", () => {
  for (const model of ["model-a", "model-alias"]) {
    const message = validTextMessage();
    message.model = model;
    assert.equal(byRule(validateMessage(message, context), "MSG-MODEL").status, "PASS");
  }

  const mismatch = validTextMessage();
  mismatch.model = "different-model";
  const mismatchObservation = byRule(validateMessage(mismatch, context), "MSG-MODEL");
  assert.equal(mismatchObservation.status, "FAIL");
  assert.equal(mismatchObservation.location?.pointer, "/model");

  const structureOnly = validateMessage(validTextMessage(), {
    ...context,
    checkModelIdentity: false,
  });
  const skipped = byRule(structureOnly, "MSG-MODEL");
  assert.equal(skipped.status, "SKIP");
  assert.equal(skipped.required, false);
});

test("accepts configured stop reasons and a custom stop sequence", () => {
  const message = validTextMessage();
  message.stop_reason = "stop_sequence";
  message.stop_sequence = "<END>";
  const observations = validateMessage(message, context);
  assert.equal(byRule(observations, "MSG-STOP").status, "PASS");
  assert.equal(byRule(observations, "MSG-STOP-SEQUENCE").status, "PASS");

  message.stop_reason = "end_turn";
  message.stop_sequence = "<END>";
  assert.equal(byRule(validateMessage(message, context), "MSG-STOP-SEQUENCE").status, "FAIL");
});

test("unknown stop reasons and content blocks are inconclusive, not structural failures", () => {
  const message = validTextMessage();
  message.stop_reason = "future_reason";
  message.content = [{ type: "future_block", payload: 1 }];
  const observations = validateMessage(message, context);
  assert.equal(byRule(observations, "MSG-STOP").status, "INDETERMINATE");
  assert.equal(byRule(observations, "MSG-CONTENT").status, "INDETERMINATE");
  assert.equal(byRule(observations, "MSG-CORE").status, "PASS");
  assert.equal(summarize(observations), "INDETERMINATE");
});

test("unknown stop reasons do not make a valid string stop sequence fail", () => {
  const message = validTextMessage();
  message.stop_reason = "future_reason";
  message.stop_sequence = "<CUSTOM-END>";
  const observations = validateMessage(message, context);
  assert.equal(byRule(observations, "MSG-STOP").status, "INDETERMINATE");
  assert.equal(summarize(observations), "INDETERMINATE");
  assert.equal(byRule(observations, "MSG-STOP-SEQUENCE").status, "INDETERMINATE");
});

test("reports malformed known blocks at exact nested and missing-member locations", () => {
  const message = validTextMessage();
  message.content = [{ type: "text", text: 4 }];
  const wrongText = validateMessage(message, context).find(
    (item) => item.status === "FAIL" && item.location?.pointer === "/content/0/text",
  );
  assert.ok(wrongText);

  message.content = [{ type: "tool_use", id: "tool-1", input: {} }];
  const missingName = validateMessage(message, context).find(
    (item) => item.status === "FAIL" && item.location?.pointer === "/content/0" &&
      item.location.missingKey === "name",
  );
  assert.ok(missingName);
  assert.equal(missingName.location?.captureId, context.captureId);
});

test("root must be an object; array content entries must be objects", () => {
  const rootObservation = byRule(validateMessage([], context), "MSG-CORE");
  assert.equal(rootObservation.status, "FAIL");
  assert.equal(rootObservation.location?.pointer, "");

  const message = validTextMessage();
  message.content = [["text", "Hello"]];
  const block = validateMessage(message, context).find(
    (item) => item.status === "FAIL" && item.location?.pointer === "/content/0",
  );
  assert.ok(block);
});
