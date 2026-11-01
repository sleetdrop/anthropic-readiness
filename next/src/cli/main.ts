/** Local CLI adapter; execution and judgments belong to the shared engine. */
import { parseArgs } from "node:util";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { createPlan, executePlan, type RunResult } from "../runner/assessment.ts";

const allProfiles = ["anthropic-basic", "anthropic-tools-smoke", "anthropic-tool-loop"];
function escape(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replace(/[\\`*_\[\]|]/gu, "\\$&")
    .replace(/[\r\n]+/gu, " ");
}
export function markdown(report: RunResult, language: "zh" | "en"): string {
  const zh = language === "zh";
  const rows = report.cases.map(
    (item) =>
      `| ${escape(item.id)} | ${item.protocolStatus} | ${item.behaviorStatus} | ${item.attemptsStarted} / ${report.plan.cases.find((c) => c.id === item.id)?.maxRequests ?? "?"} |`,
  );
  const details = report.cases.flatMap((item) =>
    item.observations
      .filter((obs) => obs.status !== "PASS")
      .map(
        (obs) =>
          `- ${escape(item.id)} / ${escape(obs.ruleId)}: ${obs.status} — ${escape(obs.reason)}; ${escape(obs.expected)} → ${escape(obs.actual)}.`,
      ),
  );
  return [
    zh ? "# Anthropic 端点诊断" : "# Anthropic endpoint diagnosis",
    "",
    `${zh ? "所选检查结果" : "Selected-check outcome"}: **${report.status}**`,
    `${zh ? "请求模型" : "Requested model"}: ${escape(report.plan.model)}`,
    `${zh ? "发起的请求尝试 / 计划上限" : "Started request attempts / planned allowance"}: ${report.attemptsStarted} / ${report.plan.plannedRequests}`,
    `${zh ? "API / 规则快照" : "API / rule snapshot"}: ${report.plan.apiVersion} / ${report.plan.contract}`,
    `${zh ? "SDK / Claude Code" : "SDK / Claude Code"}: ${zh ? "未实测" : "not tested"}`,
    "",
    zh
      ? "| 场景 | 协议检查 | 任务行为 | 请求尝试 |"
      : "| Scenario | Protocol checks | Task behavior | Request attempts |",
    "| --- | --- | --- | --- |",
    ...rows,
    "",
    zh ? "## 需要查看的观测" : "## Observations to inspect",
    "",
    ...(details.length
      ? details
      : [
          zh ? "所选检查中没有非通过观测。" : "No non-passing observations in the selected checks.",
        ]),
    "",
    zh ? "## 范围与证据" : "## Scope and evidence",
    "",
    zh
      ? "结果仅适用于本次选择与捕获，不是完整兼容性认证。result.json 保留响应字节、SHA-256、事件和派生消息；派生消息不是原始 SSE 节点。分享前审阅端点、模型和捕获内容。"
      : "Results apply only to this selection and capture, not complete compatibility certification. result.json retains response bytes, SHA-256, events and derived messages. Derived messages are not original SSE nodes. Review endpoint/model/capture content before sharing.",
    ...report.limitations.map((item) => `- ${escape(item)}`),
    "",
    "[Messages API](https://platform.claude.com/docs/en/api/messages/create) · [Streaming](https://platform.claude.com/docs/en/build-with-claude/streaming)",
    "",
  ].join("\n");
}
export async function main(args: string[]): Promise<number> {
  try {
    const { values, positionals } = parseArgs({
      args,
      allowPositionals: true,
      options: {
        endpoint: { type: "string" },
        model: { type: "string" },
        profile: { type: "string", multiple: true },
        "model-alias": { type: "string", multiple: true },
        "structure-only": { type: "boolean" },
        "max-requests": { type: "string" },
        "run-ms": { type: "string" },
        "attempt-ms": { type: "string" },
        "max-bytes": { type: "string" },
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
        "plan|run --endpoint MESSAGES_URL_OR_BASE --model MODEL [--profile ID ...] [--out NEW_DIR --allow-live] [--auth-env ENV_NAME --auth-mode api_key|bearer] [--language zh|en]",
      );
      return 0;
    }
    const command = positionals[0];
    if (positionals.length !== 1 || !["plan", "run"].includes(command ?? ""))
      throw new Error("expected_plan_or_run");
    if (!values.endpoint || !values.model) throw new Error("endpoint_and_model_required");
    const plan = createPlan({
      endpoint: values.endpoint,
      model: values.model,
      profiles: values.profile ?? allProfiles,
      aliases: values["model-alias"] ?? [],
      checkModelIdentity: !values["structure-only"],
      ...(values["max-requests"] !== undefined
        ? { maxRequests: Number(values["max-requests"]) }
        : {}),
      ...(values["run-ms"] !== undefined ? { runMs: Number(values["run-ms"]) } : {}),
      ...(values["attempt-ms"] !== undefined ? { attemptMs: Number(values["attempt-ms"]) } : {}),
      ...(values["max-bytes"] !== undefined ? { maxBytes: Number(values["max-bytes"]) } : {}),
    });
    if (command === "plan") {
      console.log(JSON.stringify(plan, null, 2));
      return 0;
    }
    if (values["allow-live"] !== true) throw new Error("live_opt_in_required");
    if (!values.out) throw new Error("new_output_directory_required");
    const language = values.language ?? "zh";
    if (language !== "zh" && language !== "en") throw new Error("invalid_language");
    const authMode = values["auth-mode"] ?? "api_key";
    if (authMode !== "api_key" && authMode !== "bearer") throw new Error("invalid_auth_mode");
    const token = values["auth-env"] ? process.env[values["auth-env"]] : undefined;
    if (values["auth-env"] && !token) throw new Error("credential_env_unavailable");
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
    await writeFile(resolve(out, "result.json"), JSON.stringify(report, null, 2) + "\n", {
      flag: "wx",
      mode: 0o600,
    });
    await writeFile(resolve(out, "report.md"), markdown(report, language), {
      flag: "wx",
      mode: 0o600,
    });
    console.log(`${report.status}: ${out}`);
    return report.status === "PASS" ? 0 : report.status === "FAIL" ? 1 : 3;
  } catch (error) {
    const known = new Set([
      "expected_plan_or_run",
      "endpoint_and_model_required",
      "invalid_url",
      "invalid_model",
      "invalid_limits",
      "insufficient_request_budget",
      "empty_scope",
      "unknown_profile",
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
if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url)
  process.exitCode = await main(process.argv.slice(2));
