/** Shared diagnostic values. No network, filesystem, SDK or browser dependencies. */
export type Status = "PASS" | "FAIL" | "INDETERMINATE" | "BLOCKED" | "SKIP";
export type Dimension = "protocol" | "behavior" | "client" | "environment";

export interface EvidenceLocation {
  readonly captureId: string;
  /** RFC 6901 pointer into a real JSON object; empty string denotes its root. */
  readonly pointer: string;
  /** A missing member is annotated at its existing parent, never fabricated. */
  readonly missingKey?: string;
  /** Zero-based event index for SSE captures, when applicable. */
  readonly eventIndex?: number;
}

export interface Observation {
  readonly ruleId: string;
  readonly ruleVersion: number;
  readonly dimension: Dimension;
  readonly status: Status;
  readonly required: boolean;
  readonly reason: string;
  readonly expected: string;
  readonly actual: string;
  readonly location?: EvidenceLocation;
}

export interface MessageValidationContext {
  readonly captureId: string;
  readonly requestedModel: string;
  readonly modelAliases: readonly string[];
  readonly checkModelIdentity: boolean;
  /** Known stop reasons are supplied by the selected protocol snapshot. */
  readonly stopReasons: readonly string[];
}

/** Aggregate only required checks; uncertainty never becomes a successful result. */
export function summarize(observations: readonly Observation[]): Status {
  const states = new Set(observations.filter((item) => item.required).map((item) => item.status));
  const priority: readonly Status[] = ["FAIL", "BLOCKED", "INDETERMINATE", "SKIP", "PASS"];
  return priority.find((status) => states.has(status)) ?? "INDETERMINATE";
}
