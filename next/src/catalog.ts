/** Versioned selection inventory. Execution and endpoint outcomes are verified separately. */
export const apiVersions = ["2023-06-01", "2026-10-21"] as const;
export type ApiVersion = (typeof apiVersions)[number];

export interface CaseDefinition {
  readonly id: string;
  readonly revision: number;
  readonly profile: string;
  readonly response: "json" | "sse";
  readonly maxRequests: number;
  readonly capabilities: readonly ("streaming" | "tools")[];
  readonly route?: "count_tokens";
  readonly expectedStatus?: 400;
}

function probe(
  id: string,
  profile: string,
  options: Omit<Partial<CaseDefinition>, "id" | "profile"> = {},
): CaseDefinition {
  return {
    id,
    profile,
    revision: 1,
    response: "json",
    maxRequests: 1,
    capabilities: [],
    ...options,
  };
}

const tools = { capabilities: ["tools"] } as const;
const stream = { response: "sse", capabilities: ["streaming"] } as const;
const invalid = { expectedStatus: 400 } as const;
const count = { route: "count_tokens" } as const;
const coreProfiles = [
  "anthropic-basic",
  "anthropic-tools-smoke",
  "anthropic-tool-loop",
  "anthropic-text",
  "anthropic-tools",
  "anthropic-count",
  "anthropic-errors",
];

export const cases: readonly CaseDefinition[] = [
  {
    id: "ANT-MESSAGE-001",
    revision: 2,
    profile: "anthropic-basic",
    response: "json",
    maxRequests: 1,
    capabilities: [],
  },
  {
    id: "ANT-TEXT-SSE-001",
    revision: 2,
    profile: "anthropic-basic",
    response: "sse",
    maxRequests: 1,
    capabilities: ["streaming"],
  },
  {
    id: "ANT-TEXT-SSE-002",
    revision: 2,
    profile: "anthropic-basic",
    response: "sse",
    maxRequests: 1,
    capabilities: ["streaming"],
  },
  {
    id: "ANT-TOOL-FORCED-001",
    revision: 1,
    profile: "anthropic-tools-smoke",
    response: "json",
    maxRequests: 1,
    capabilities: ["tools"],
  },
  {
    id: "ANT-TOOL-LOOP-001",
    revision: 2,
    profile: "anthropic-tool-loop",
    response: "json",
    maxRequests: 2,
    capabilities: ["tools"],
  },
  probe("ANT-SYSTEM-BLOCKS-001", "anthropic-text"),
  probe("ANT-HISTORY-001", "anthropic-text", { maxRequests: 2 }),
  probe("ANT-STOP-SEQUENCE-001", "anthropic-text"),
  probe("ANT-STOP-SEQUENCE-SSE-001", "anthropic-text", stream),
  probe("ANT-MAX-TOKENS-001", "anthropic-text"),
  probe("ANT-MAX-TOKENS-SSE-001", "anthropic-text", stream),
  probe("ANT-TOOL-NONE-001", "anthropic-tools", tools),
  probe("ANT-TOOL-ANY-001", "anthropic-tools", tools),
  probe("ANT-TOOL-SSE-LOOP-001", "anthropic-tools", {
    response: "sse",
    maxRequests: 2,
    capabilities: ["tools", "streaming"],
  }),
  probe("ANT-TOOL-PARALLEL-001", "anthropic-tools", {
    ...tools,
    maxRequests: 2,
  }),
  probe("ANT-TOOL-RESULT-ERROR-001", "anthropic-tools", {
    ...tools,
    maxRequests: 2,
  }),
  probe("ANT-COUNT-001", "anthropic-count", count),
  probe("ANT-COUNT-TOOLS-001", "anthropic-count", { ...tools, ...count }),
  probe("ANT-ERROR-MISSING-001", "anthropic-errors", invalid),
  probe("ANT-ERROR-ROLE-001", "anthropic-errors", invalid),
  probe("ANT-ERROR-TOOL-ID-001", "anthropic-errors", { ...tools, ...invalid }),
  probe("ANT-COUNT-ERROR-001", "anthropic-errors", { ...count, ...invalid }),
  probe("ANT-ERROR-SAMPLING-001", "anthropic-version-2026", invalid),
  probe("ANT-ERROR-ASSISTANT-DOCUMENT-001", "anthropic-version-2026", invalid),
  probe("ANT-ERROR-USER-CITATION-001", "anthropic-version-2026", invalid),
  probe("ANT-PREFILL-001", "anthropic-prefill"),
  probe("ANT-TOOL-STRICT-001", "anthropic-structured", tools),
  probe("ANT-STRUCTURED-001", "anthropic-structured"),
  probe("ANT-STRUCTURED-SSE-001", "anthropic-structured", stream),
  probe("ANT-THINKING-001", "anthropic-thinking"),
  probe("ANT-THINKING-SSE-001", "anthropic-thinking", stream),
  probe("ANT-VISION-001", "anthropic-vision"),
  probe("ANT-PDF-001", "anthropic-pdf"),
  probe("ANT-DOCUMENT-CITATION-001", "anthropic-citations"),
  probe("ANT-CACHE-001", "anthropic-cache", { maxRequests: 2 }),
];

/** Reject bad selections; deduplicate profiles without dropping required scenarios. */
export function selectCases(profiles: readonly string[]): readonly CaseDefinition[] {
  if (profiles.length === 0) throw new Error("empty_scope");
  const known = new Set(["anthropic-core", ...cases.map((item) => item.profile)]);
  if (profiles.some((profile) => !known.has(profile))) throw new Error("unknown_profile");
  const selected = new Set(
    profiles.flatMap((profile) => (profile === "anthropic-core" ? coreProfiles : [profile])),
  );
  return cases.filter((item) => selected.has(item.profile));
}
