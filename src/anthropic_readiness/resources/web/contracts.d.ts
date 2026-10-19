/** JSON values shared by JSDoc modules; runtime documents are schema checked by the server. */
export type JsonValue = null | boolean | number | string | JsonValue[] | JsonObject;
export interface JsonObject {
  [key: string]: JsonValue;
}

export type PresentationLocale = "zh-CN" | "en";
export type PresentationTheme = "light" | "dark" | "system";
export interface PresentationOptions extends JsonObject {
  schema_version: "1.0";
  locale: PresentationLocale;
  theme: PresentationTheme;
}
export interface DiagnosticReference extends JsonObject {
  kind: "run" | "baseline";
  id: string;
}
export interface DiagnosticEligibility extends JsonObject {
  read: boolean;
  retest: boolean;
  compare: boolean;
  reasons: string[];
}
export interface DiagnosticImportPreview extends JsonObject {
  schema_version: "1.0";
  preview_id: string;
  expires_at: string;
  source: JsonObject;
  eligibility: DiagnosticEligibility;
  evidence_verification: JsonObject;
  disclosures: string[];
  relationship: JsonObject;
}
export interface DiagnosticRetestRequest extends JsonObject {
  baseline_id: string;
  target: JsonObject;
}
export interface DiagnosticRetestResponse extends JsonObject {
  plan: JsonObject;
  conditions: JsonObject;
}
export interface DiagnosticComparisonRequest extends JsonObject {
  before: DiagnosticReference;
  after: DiagnosticReference;
}
export interface DiagnosticExportRequest extends JsonObject {
  schema_version: "2.0";
  formats: ("html" | "markdown" | "json" | "zip")[];
  include_evidence: boolean;
  presentation: PresentationOptions;
}
