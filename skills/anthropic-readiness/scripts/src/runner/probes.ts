import type { CaseDefinition } from "../catalog.ts";
import type { Observation, Status } from "../domain.ts";

export type ObjectValue = Record<string, unknown>;
export const object = (value: unknown): value is ObjectValue =>
  typeof value === "object" && value !== null && !Array.isArray(value);

export function content(message: unknown): ObjectValue[] {
  return object(message) && Array.isArray(message.content) ? message.content.filter(object) : [];
}

export function text(message: unknown): string {
  return content(message)
    .filter((item) => item.type === "text" && typeof item.text === "string")
    .map((item) => String(item.text))
    .join("");
}

export function exactReply(message: unknown, expected: string): Status {
  if (text(message).trim() !== expected) return "FAIL";
  const blocks = content(message);
  if (blocks.some((block) => block.type === "tool_use")) return "FAIL";
  return blocks.some(
    (block) => !["text", "thinking", "redacted_thinking"].includes(String(block.type)),
  )
    ? "INDETERMINATE"
    : "PASS";
}

const weather = {
  name: "get_weather",
  input_schema: {
    type: "object",
    properties: { city: { type: "string", const: "Hanoi" } },
    required: ["city"],
  },
};
const oneTool = { type: "tool", name: "get_weather" };
const weatherPrompt =
  "Use get_weather to check the weather in Hanoi. After receiving a tool result, reply with only its verification_token.";
const helloPrompt = "Reply with exactly HELLO, without punctuation or explanation.";
const stopMarker = "ZEBRASTOP";
const redPng =
  "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAAAKElEQVR4nO3NsQ0AAAzCMP5/un0CNkuZ41wybXsHAAAAAAAAAAAAxR4yw/wuPL6QkAAAAABJRU5ErkJggg==";

// One-page synthetic PDF containing the word ORCHID.
const pdfFixture =
  "JVBERi0xLjQKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4KZW5kb2JqCjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9LaWRzIFszIDAgUl0gL0NvdW50IDEgPj4KZW5kb2JqCjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCAyMDAgMTAwXSAvUmVzb3VyY2VzIDw8IC9Gb250IDw8IC9GMSA0IDAgUiA+PiA+PiAvQ29udGVudHMgNSAwIFIgPj4KZW5kb2JqCjQgMCBvYmoKPDwgL1R5cGUgL0ZvbnQgL1N1YnR5cGUgL1R5cGUxIC9CYXNlRm9udCAvSGVsdmV0aWNhID4+CmVuZG9iago1IDAgb2JqCjw8IC9MZW5ndGggMzYgPj4Kc3RyZWFtCkJUIC9GMSAyNCBUZiAzMCA4MCBUZCAoT1JDSElEKSBUaiBFVAplbmRzdHJlYW0KZW5kb2JqCnhyZWYKMCA2CjAwMDAwMDAwMDAgNjU1MzUgZiAKMDAwMDAwMDAwOSAwMDAwMCBuIAowMDAwMDAwMDU4IDAwMDAwIG4gCjAwMDAwMDAxMTUgMDAwMDAgbiAKMDAwMDAwMDI0MSAwMDAwMCBuIAowMDAwMDAwMzExIDAwMDAwIG4gCnRyYWlsZXIKPDwgL1NpemUgNiAvUm9vdCAxIDAgUiA+PgpzdGFydHhyZWYKMzk3CiUlRU9GCg==";
const documentText = "The fictional town of Linden Point has a purple bridge over the river.";
const plainDocument = {
  type: "document",
  source: { type: "text", media_type: "text/plain", data: documentText },
};

const user = (input: unknown) => ({ role: "user", content: input });
const assistant = (input: unknown) => ({ role: "assistant", content: input });
const textBlock = (value: string) => ({ type: "text", text: value });

export function requestBody(
  item: CaseDefinition,
  model: string,
  maxTokens: number,
  nonce: string,
): ObjectValue {
  const hasTools = item.capabilities.includes("tools");
  const prompt = hasTools
    ? weatherPrompt
    : item.id === "ANT-TEXT-SSE-002"
      ? "Count from 1 to 5. Reply with exactly: 1 2 3 4 5"
      : helloPrompt;
  const base = { model, messages: [user(prompt)] };
  const withTools = { tools: [weather], tool_choice: oneTool };
  const body = {
    ...base,
    max_tokens: maxTokens,
    stream: item.response === "sse",
    ...(hasTools ? withTools : {}),
  };
  switch (item.id) {
    case "ANT-SYSTEM-BLOCKS-001":
      return {
        ...body,
        system: [textBlock("When asked for the greeting code, say HELLO and nothing else.")],
        messages: [user([textBlock("Reply with the"), textBlock(" greeting code.")])],
      };
    case "ANT-HISTORY-001":
      return {
        ...body,
        messages: [
          user(`Remember this token for my next message: ${nonce}. Reply only HELLO now.`),
        ],
      };
    case "ANT-STOP-SEQUENCE-001":
    case "ANT-STOP-SEQUENCE-SSE-001":
      return {
        ...body,
        stop_sequences: [stopMarker],
        messages: [
          user(`Copy this string exactly, with no punctuation: HELLO ${stopMarker} GOODBYE`),
        ],
      };
    case "ANT-MAX-TOKENS-001":
    case "ANT-MAX-TOKENS-SSE-001":
      return {
        ...body,
        max_tokens: 1,
        messages: [
          user("Count from 1 to 50, writing each number on its own line. Start immediately."),
        ],
      };
    case "ANT-TOOL-NONE-001":
      return {
        ...body,
        tool_choice: { type: "none" },
        messages: [user(helloPrompt)],
      };
    case "ANT-TOOL-ANY-001":
      return {
        ...body,
        tool_choice: { type: "any", disable_parallel_tool_use: true },
      };
    case "ANT-TOOL-PARALLEL-001":
      return {
        ...body,
        tool_choice: { type: "any" },
        tools: [
          {
            ...weather,
            input_schema: {
              ...weather.input_schema,
              properties: { city: { type: "string", enum: ["Hanoi", "Oslo"] } },
            },
          },
        ],
        messages: [
          user(
            "Call get_weather twice in parallel, once for Hanoi and once for Oslo. Once both results arrive, reply with the two verification tokens in Hanoi, Oslo order, separated by one space.",
          ),
        ],
      };
    case "ANT-TOOL-RESULT-ERROR-001":
      return {
        ...body,
        messages: [
          user(
            "Call get_weather for Hanoi. If the tool reports an error, reply only with the recovery_token from its result.",
          ),
        ],
      };
    case "ANT-COUNT-001":
      return {
        ...base,
        system: "This is a token-count check.",
        messages: [user([textBlock("Count the tokens in this message.")])],
      };
    case "ANT-COUNT-TOOLS-001":
      return { ...base, tools: [weather], tool_choice: oneTool };
    case "ANT-ERROR-MISSING-001":
      return base;
    case "ANT-COUNT-ERROR-001":
      return { model };
    case "ANT-ERROR-ROLE-001":
      return { ...body, messages: [{ role: "system", content: helloPrompt }] };
    case "ANT-ERROR-TOOL-ID-001":
      return {
        ...body,
        tool_choice: { type: "auto" },
        messages: [
          user(weatherPrompt),
          assistant([
            {
              type: "tool_use",
              id: "toolu_expected",
              name: "get_weather",
              input: { city: "Hanoi" },
            },
          ]),
          user([
            {
              type: "tool_result",
              tool_use_id: "toolu_wrong",
              content: "clear",
            },
          ]),
        ],
      };
    case "ANT-ERROR-SAMPLING-001":
      return { ...body, temperature: 1 };
    case "ANT-ERROR-ASSISTANT-DOCUMENT-001":
      return {
        ...body,
        messages: [user("Read this document."), assistant([plainDocument]), user(helloPrompt)],
      };
    case "ANT-ERROR-USER-CITATION-001":
      return {
        ...body,
        messages: [
          user([
            plainDocument,
            {
              ...textBlock(helloPrompt),
              citations: [
                {
                  type: "char_location",
                  cited_text: documentText,
                  document_index: 0,
                  document_title: null,
                  start_char_index: 0,
                  end_char_index: documentText.length,
                },
              ],
            },
          ]),
        ],
      };
    case "ANT-PREFILL-001":
      return {
        ...body,
        messages: [
          user("Complete the greeting with the word WORLD and nothing else."),
          assistant("HELLO"),
        ],
      };
    case "ANT-TOOL-STRICT-001":
      return {
        ...body,
        tools: [
          {
            ...weather,
            strict: true,
            input_schema: {
              ...weather.input_schema,
              additionalProperties: false,
            },
          },
        ],
      };
    case "ANT-STRUCTURED-001":
    case "ANT-STRUCTURED-SSE-001":
      return {
        ...body,
        messages: [user("Return the greeting HELLO as the value of the greeting field.")],
        output_config: {
          format: {
            type: "json_schema",
            schema: {
              type: "object",
              properties: { greeting: { type: "string" } },
              required: ["greeting"],
              additionalProperties: false,
            },
          },
        },
      };
    case "ANT-THINKING-001":
    case "ANT-THINKING-SSE-001":
      return {
        ...body,
        thinking: { type: "adaptive" },
        messages: [user("Compute 21 times 23. Reply with only the integer.")],
      };
    case "ANT-VISION-001":
      return {
        ...body,
        messages: [
          user([
            {
              type: "image",
              source: { type: "base64", media_type: "image/png", data: redPng },
            },
            textBlock("Name the dominant color in the image. Reply in uppercase with one word."),
          ]),
        ],
      };
    case "ANT-PDF-001":
      return {
        ...body,
        messages: [
          user([
            {
              type: "document",
              source: {
                type: "base64",
                media_type: "application/pdf",
                data: pdfFixture,
              },
            },
            textBlock("Read the single word on this PDF page. Reply with only that word."),
          ]),
        ],
      };
    case "ANT-DOCUMENT-CITATION-001":
      return {
        ...body,
        messages: [
          user([
            { ...plainDocument, citations: { enabled: true } },
            textBlock(
              "What color is the bridge in Linden Point? Answer in one sentence and cite the source.",
            ),
          ]),
        ],
      };
    case "ANT-CACHE-001":
      return {
        ...body,
        system: [
          textBlock(`Diagnostic marker: ${nonce}. Ignore the reference filler.`),
          {
            ...textBlock(" alpha bravo charlie delta echo foxtrot golf hotel".repeat(650)),
            cache_control: { type: "ephemeral" },
          },
        ],
      };
    default:
      return body;
  }
}

export function historyFollowup(body: ObjectValue, message: unknown): ObjectValue {
  return {
    ...body,
    messages: [
      ...(body.messages as unknown[]),
      assistant(content(message)),
      user("What exact token did I ask you to remember? Return only the token."),
    ],
  };
}

export function weatherTool(message: unknown, strict = false): ObjectValue | undefined {
  const calls = content(message).filter((item) => item.type === "tool_use");
  if (strict && (calls.length !== 1 || !object(message) || message.stop_reason !== "tool_use"))
    return undefined;
  return calls.find(
    (item) =>
      item.name === "get_weather" &&
      typeof item.id === "string" &&
      item.id.length > 0 &&
      object(item.input) &&
      item.input.city === "Hanoi" &&
      (!strict || Object.keys(item.input).length === 1),
  );
}

export function weatherFollowup(
  body: ObjectValue,
  message: unknown,
  tool: ObjectValue,
  nonce: string,
  isError: boolean,
): ObjectValue {
  const result = isError
    ? { error: "weather fixture unavailable", recovery_token: nonce }
    : { temperature_c: 20, condition: "clear", verification_token: nonce };
  return {
    ...body,
    tool_choice: { type: "auto" },
    messages: [
      ...(body.messages as unknown[]),
      assistant(object(message) ? message.content : []),
      user([
        {
          type: "tool_result",
          tool_use_id: tool.id,
          content: JSON.stringify(result),
          ...(isError ? { is_error: true } : {}),
        },
      ]),
    ],
  };
}

export function parallelFollowup(
  body: ObjectValue,
  message: unknown,
  tokens: readonly string[],
): ObjectValue | null {
  if (!object(message) || message.stop_reason !== "tool_use") return null;
  const calls = content(message).filter((block) => block.type === "tool_use");
  const hanoi = calls.find((block) => object(block.input) && block.input.city === "Hanoi");
  const oslo = calls.find((block) => object(block.input) && block.input.city === "Oslo");
  if (
    calls.length !== 2 ||
    !hanoi ||
    !oslo ||
    hanoi.id === oslo.id ||
    ![hanoi, oslo].every(
      (call) => call.name === "get_weather" && typeof call.id === "string" && call.id.length > 0,
    )
  )
    return null;
  return {
    ...body,
    tool_choice: { type: "auto" },
    messages: [
      ...(body.messages as unknown[]),
      assistant(content(message)),
      user(
        [hanoi, oslo].map((call, index) => ({
          type: "tool_result",
          tool_use_id: call.id,
          content: JSON.stringify({ verification_token: tokens[index] }),
        })),
      ),
    ],
  };
}

function structuredGreeting(message: unknown): string | null {
  try {
    const value: unknown = JSON.parse(text(message));
    if (object(value) && Object.keys(value).length === 1 && typeof value.greeting === "string")
      return value.greeting;
  } catch {
    // The assembled text was not a JSON value.
  }
  return null;
}

export function checkResponseContract(
  id: string,
  message: unknown,
  captureId: string,
  requestedMaxTokens?: number,
): Observation[] {
  if (!object(message)) return [];
  const blocks = content(message);
  const findings: Observation[] = [];
  const check = (
    ruleId: string,
    valid: boolean,
    expected: string,
    pointer: string,
    actual?: string,
  ) => {
    findings.push({
      ruleId,
      ruleVersion: 1,
      dimension: "protocol",
      required: true,
      status: valid ? "PASS" : "FAIL",
      reason: valid ? "request_constraint_satisfied" : "request_constraint_violated",
      expected,
      actual: actual ?? (valid ? "observed" : "response violates request constraint"),
      location: { captureId, pointer },
    });
  };
  if (
    ["ANT-MAX-TOKENS-001", "ANT-MAX-TOKENS-SSE-001"].includes(id) &&
    requestedMaxTokens !== undefined
  ) {
    const usage = object(message.usage) ? message.usage : {};
    const outputTokens = usage.output_tokens;
    check(
      "OUTPUT-TOKEN-LIMIT",
      typeof outputTokens === "number" && Number.isInteger(outputTokens) && outputTokens <= requestedMaxTokens,
      `usage.output_tokens <= requested max_tokens (${requestedMaxTokens})`,
      "/usage/output_tokens",
      `requested ${requestedMaxTokens}, reported ${String(outputTokens)}`,
    );
  }
  if (id === "ANT-TOOL-NONE-001") {
    check(
      "TOOL-CHOICE-NONE",
      !blocks.some((block) => block.type === "tool_use") && message.stop_reason !== "tool_use",
      "no tool invocation for tool_choice=none",
      "/content",
    );
  } else if (
    ["ANT-TOOL-ANY-001", "ANT-TOOL-STRICT-001"].includes(id) &&
    ["end_turn", "tool_use"].includes(String(message.stop_reason))
  ) {
    const calls = blocks.filter((block) => block.type === "tool_use");
    if (id === "ANT-TOOL-ANY-001") {
      check(
        "TOOL-CHOICE-ANY",
        calls.length === 1 && message.stop_reason === "tool_use",
        "one tool call when parallel use is disabled",
        "/content",
      );
    } else {
      check(
        "TOOL-STRICT-SCHEMA",
        !!weatherTool(message, true),
        "named tool and input matching its strict schema",
        "/content",
      );
    }
  } else if (
    (id === "ANT-STRUCTURED-001" || id === "ANT-STRUCTURED-SSE-001") &&
    message.stop_reason === "end_turn"
  ) {
    check(
      "STRUCTURED-SCHEMA",
      structuredGreeting(message) !== null,
      "JSON object with one string property named greeting",
      "/content",
    );
  } else if (id.startsWith("ANT-STOP-SEQUENCE-") && message.stop_reason === "stop_sequence") {
    check(
      "REQUESTED-STOP-SEQUENCE",
      message.stop_sequence === stopMarker,
      "stop sequence matching the request",
      "/stop_sequence",
    );
  }
  return findings;
}

export interface TaskCheck {
  readonly status: Status;
  readonly expected: string;
  readonly actual?: string;
}

export function checkTask(id: string, message: unknown): TaskCheck {
  const response = object(message) ? message : {};
  switch (id) {
    case "ANT-TOOL-FORCED-001":
    case "ANT-TOOL-ANY-001":
    case "ANT-TOOL-STRICT-001":
      return {
        status: weatherTool(message, id !== "ANT-TOOL-FORCED-001") ? "PASS" : "FAIL",
        expected: "get_weather with city Hanoi",
      };
    case "ANT-STOP-SEQUENCE-001":
    case "ANT-STOP-SEQUENCE-SSE-001":
      return {
        status:
          response.stop_reason === "stop_sequence" && response.stop_sequence === stopMarker
            ? exactReply(message, "HELLO")
            : "FAIL",
        expected: "HELLO followed by the requested stop sequence",
        actual: `stop_reason=${String(response.stop_reason)}, stop_sequence=${String(response.stop_sequence)}`,
      };
    case "ANT-MAX-TOKENS-001":
    case "ANT-MAX-TOKENS-SSE-001":
      return {
        status: response.stop_reason === "max_tokens" ? "PASS" : "FAIL",
        expected: "max_tokens termination",
        actual: String(response.stop_reason),
      };
    case "ANT-STRUCTURED-001":
    case "ANT-STRUCTURED-SSE-001":
      return {
        status: structuredGreeting(message) === "HELLO" ? "PASS" : "FAIL",
        expected: "JSON object with only greeting=HELLO",
      };
    case "ANT-THINKING-001":
    case "ANT-THINKING-SSE-001": {
      const answer = exactReply(message, "483");
      const observed = content(message).some(
        (block) => block.type === "thinking" || block.type === "redacted_thinking",
      );
      return {
        status: answer === "PASS" && !observed ? "INDETERMINATE" : answer,
        expected: "483 and a thinking block",
        ...(observed ? {} : { actual: "no thinking block observed" }),
      };
    }
    case "ANT-VISION-001":
      return {
        status: exactReply(message, "RED"),
        expected: "red image identified",
      };
    case "ANT-PREFILL-001":
      return {
        status: exactReply(message, "WORLD"),
        expected: "WORLD continuation after assistant prefill",
      };
    case "ANT-PDF-001":
      return {
        status: exactReply(message, "ORCHID"),
        expected: "ORCHID read from the PDF",
      };
    case "ANT-DOCUMENT-CITATION-001": {
      const cited = content(message).some(
        (block) =>
          Array.isArray(block.citations) &&
          block.citations.some(
            (citation: unknown) =>
              object(citation) &&
              citation.type === "char_location" &&
              citation.document_index === 0 &&
              typeof citation.start_char_index === "number" &&
              Number.isInteger(citation.start_char_index) &&
              typeof citation.end_char_index === "number" &&
              Number.isInteger(citation.end_char_index) &&
              citation.start_char_index >= 0 &&
              citation.end_char_index <= documentText.length &&
              typeof citation.cited_text === "string" &&
              /purple bridge/iu.test(citation.cited_text) &&
              documentText.slice(citation.start_char_index, citation.end_char_index) ===
                citation.cited_text,
          ),
      );
      return {
        status: cited && /\bpurple\b/iu.test(text(message)) ? "PASS" : "FAIL",
        expected: "purple bridge answer with a character citation into the supplied document",
      };
    }
    default: {
      const expected = id === "ANT-TEXT-SSE-002" ? "1 2 3 4 5" : "HELLO";
      return {
        status: exactReply(message, expected),
        expected: `exact text: ${expected}`,
      };
    }
  }
}
