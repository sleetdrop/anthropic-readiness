/** Migration inventory only: a catalog entry does not establish an implemented runner. */
export interface CaseDefinition {
  readonly id: string;
  readonly revision: number;
  readonly profile: string;
  readonly response: "json" | "sse";
  readonly maxRequests: number;
  readonly capabilities: readonly ("streaming" | "tools")[];
}

export const cases: readonly CaseDefinition[] = [
  {
    id: "ANT-MESSAGE-001",
    revision: 1,
    profile: "anthropic-basic",
    response: "json",
    maxRequests: 1,
    capabilities: [],
  },
  {
    id: "ANT-TEXT-SSE-001",
    revision: 1,
    profile: "anthropic-basic",
    response: "sse",
    maxRequests: 1,
    capabilities: ["streaming"],
  },
  {
    id: "ANT-TEXT-SSE-002",
    revision: 1,
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
    revision: 1,
    profile: "anthropic-tool-loop",
    response: "json",
    maxRequests: 2,
    capabilities: ["tools"],
  },
];

/** Reject bad selections; deduplicate profiles without dropping required scenarios. */
export function selectCases(profiles: readonly string[]): readonly CaseDefinition[] {
  if (profiles.length === 0) throw new Error("empty_scope");
  const known = new Set(cases.map((item) => item.profile));
  if (profiles.some((profile) => !known.has(profile))) throw new Error("unknown_profile");
  return cases.filter((item) => profiles.includes(item.profile));
}
