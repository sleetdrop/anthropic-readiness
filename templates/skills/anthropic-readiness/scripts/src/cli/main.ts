/** Local CLI adapter; execution and judgments belong to the shared engine. */
import { parseArgs } from "node:util";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { apiVersions } from "../catalog.ts";
import { createPlan, executePlan, type RunResult } from "../runner/assessment.ts";

import { renderJsonView } from "./json-view.ts";
import { renderReport } from "./report.ts";
import { readTarget, readTargetToken } from "./target-directory.ts";

const defaultProfiles = ["anthropic-core"];
export async function main(args: string[]): Promise<number> {
  try {
    const { values, positionals } = parseArgs({
      args,
      allowPositionals: true,
      options: {
        endpoint: { type: "string" },
        "target-dir": { type: "string" },
        "use-env": { type: "boolean" },
        model: { type: "string" },
        "api-version": { type: "string" },
        profile: { type: "string", multiple: true },
        "model-alias": { type: "string", multiple: true },
        "structure-only": { type: "boolean" },
        "max-requests": { type: "string" },
        "run-ms": { type: "string" },
        "attempt-ms": { type: "string" },
        "max-bytes": { type: "string" },
        "max-tokens": { type: "string" },
        "read-ms": { type: "string" },
        "connect-ms": { type: "string" },
        "allow-live": { type: "boolean" },
        "auth-env": { type: "string" },
        "auth-mode": { type: "string" },
        out: { type: "string" },
        language: { type: "string" },
        help: { type: "boolean" },
      },
    });
    if (values.help) {
      console.log(
        "plan|run [--target-dir DIR | --use-env | --endpoint MESSAGES_URL_OR_BASE --model MODEL] [--profile ID ...] [--api-version 2023-06-01|2026-10-21] [--out NEW_DIR --allow-live] [--auth-env ENV_NAME --auth-mode api_key|bearer|none] [--language en|zh (default: en)] [--max-requests N --max-tokens N --run-ms N --attempt-ms N --read-ms N --connect-ms N --max-bytes N]",
      );
      return 0;
    }
    const command = positionals[0];
    if (positionals.length !== 1 || !["plan", "run"].includes(command ?? ""))
      throw new Error("expected_plan_or_run");
    const targetDirectory = values["target-dir"];
    const useEnv = values["use-env"] === true;
    if (targetDirectory !== undefined) {
      if (!targetDirectory) throw new Error("target_directory_required");
      if (useEnv || ["endpoint", "model", "api-version", "auth-mode", "auth-env"].some(
        (key) => Object.hasOwn(values, key),
      )) throw new Error("conflicting_target_options");
    }
    const target = targetDirectory === undefined ? undefined : await readTarget(targetDirectory);
    const endpoint = target?.endpoint ?? values.endpoint ?? (useEnv ? process.env.AR_DIAG_ENDPOINT_URL : undefined);
    const model = target?.model ?? values.model ?? (useEnv ? process.env.AR_DIAG_MODEL : undefined);
    const requestedVersion =
      target?.apiVersion ?? values["api-version"] ?? (useEnv ? process.env.AR_DIAG_API_VERSION : undefined);
    const authMode =
      target?.authMode ?? values["auth-mode"] ?? (useEnv ? process.env.AR_DIAG_AUTH_MODE : undefined) ?? "api_key";
    if (!endpoint || !model) throw new Error("endpoint_and_model_required");
    if (authMode !== "api_key" && authMode !== "bearer" && authMode !== "none")
      throw new Error("invalid_auth_mode");
    const apiVersion = apiVersions.find((version) => version === requestedVersion);
    if (requestedVersion !== undefined && apiVersion === undefined)
      throw new Error("invalid_api_version");
    const plan = createPlan({
      endpoint,
      model,
      profiles: values.profile ?? defaultProfiles,
      ...(apiVersion ? { apiVersion } : {}),
      aliases: values["model-alias"] ?? [],
      checkModelIdentity: !values["structure-only"],
      ...(values["max-requests"] !== undefined
        ? { maxRequests: Number(values["max-requests"]) }
        : {}),
      ...(values["run-ms"] !== undefined ? { runMs: Number(values["run-ms"]) } : {}),
      ...(values["attempt-ms"] !== undefined ? { attemptMs: Number(values["attempt-ms"]) } : {}),
      ...(values["max-bytes"] !== undefined ? { maxBytes: Number(values["max-bytes"]) } : {}),
      ...(values["max-tokens"] !== undefined ? { maxTokens: Number(values["max-tokens"]) } : {}),
      ...(values["read-ms"] !== undefined ? { readMs: Number(values["read-ms"]) } : {}),
      ...(values["connect-ms"] !== undefined ? { connectMs: Number(values["connect-ms"]) } : {}),
    });
    if (command === "plan") {
      console.log(JSON.stringify(plan, null, 2));
      return 0;
    }
    if (values["allow-live"] !== true) throw new Error("live_opt_in_required");
    if (targetDirectory !== undefined && (values["max-requests"] === undefined || values["run-ms"] === undefined))
      throw new Error("target_run_limits_required");
    if (!values.out) throw new Error("new_output_directory_required");
    const language = values.language ?? "en";
    if (language !== "zh" && language !== "en") throw new Error("invalid_language");
    const credentialEnv =
      authMode === "none"
        ? undefined
        : (values["auth-env"] ?? (useEnv ? "AR_DIAG_AUTH_TOKEN" : undefined));
    const token = targetDirectory !== undefined && authMode !== "none"
      ? await readTargetToken(targetDirectory)
      : credentialEnv ? process.env[credentialEnv] : undefined;
    if (credentialEnv !== undefined && !token) throw new Error("credential_env_unavailable");
    const out = resolve(values.out);
    try {
      await mkdir(out, { mode: 0o700 });
    } catch {
      throw new Error("output_directory_must_be_new_and_parent_must_exist");
    }
    const abort = new AbortController();
    const cancel = () => abort.abort();
    process.once("SIGINT", cancel);
    process.once("SIGTERM", cancel);
    let report: RunResult;
    try {
      report = await executePlan(plan, {
        allowLive: true,
        authMode,
        ...(token ? { token } : {}),
        signal: abort.signal,
        onCaseComplete: (item) => process.stderr.write(`${item.id}: ${item.status}\n`),
        onCapture: (capture) =>
          writeFile(
            resolve(out, `response-${capture.id}.json`),
            JSON.stringify(capture, null, 2) + "\n",
            { flag: "wx", mode: 0o600 },
          ),
      });
    } finally {
      process.removeListener("SIGINT", cancel);
      process.removeListener("SIGTERM", cancel);
    }
    const resultJson = JSON.stringify(report, null, 2) + "\n";
    const writeJsonView = (name: string, json: string) =>
      writeFile(resolve(out, `${name}.html`), renderJsonView(json, name, language), {
        flag: "wx",
        mode: 0o600,
      });
    await writeFile(resolve(out, "result.json"), resultJson, {
      flag: "wx",
      mode: 0o600,
    });
    await writeJsonView("result.json", resultJson);
    for (const item of report.cases) {
      for (const capture of item.captures) {
        const name = `response-${capture.id}.json`;
        await writeJsonView(name, await readFile(resolve(out, name), "utf8"));
      }
    }
    await writeFile(resolve(out, "report.html"), renderReport(report, language), {
      flag: "wx",
      mode: 0o600,
    });
    console.log(`${report.status}: ${out}`);
    return report.status === "PASS" ? 0 : report.status === "FAIL" ? 1 : 3;
  } catch (error) {
    const known = new Set([
      "expected_plan_or_run",
      "target_directory_required",
      "conflicting_target_options",
      "target_config_unreadable_or_invalid",
      "target_config_unknown_field",
      "target_endpoint_and_model_required",
      "target_run_limits_required",
      "target_token_unavailable",
      "endpoint_and_model_required",
      "invalid_url",
      "invalid_model",
      "invalid_limits",
      "insufficient_request_budget",
      "empty_scope",
      "unknown_profile",
      "invalid_api_version",
      "profile_requires_api_version",
      "live_opt_in_required",
      "new_output_directory_required",
      "invalid_language",
      "invalid_auth_mode",
      "credential_env_unavailable",
      "output_directory_must_be_new_and_parent_must_exist",
    ]);
    if (error instanceof Error && known.has(error.message)) {
      process.stderr.write(error.message + "\n");
      return 2;
    }
    if (
      error instanceof Error &&
      "code" in error &&
      String(error.code).startsWith("ERR_PARSE_ARGS_")
    ) {
      process.stderr.write("invalid_arguments\n");
      return 2;
    }
    process.stderr.write("internal_error; inspect retained response files\n");
    return 4;
  }
}
if (import.meta.main) process.exitCode = await main(process.argv.slice(2));
