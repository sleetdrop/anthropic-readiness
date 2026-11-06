import { constants } from "node:fs";
import { lstat } from "node:fs/promises";
import { resolve } from "node:path";
import { readBoundedFile } from "./local-file.ts";

const fields = new Set(["endpoint", "model", "apiVersion", "authMode"]);
const inputLimit = 16 * 1024;

async function readTargetText(directory: string, name: string): Promise<string> {
  const path = resolve(directory, name);
  if (!(await lstat(path)).isFile()) throw new Error("expected_regular_file");
  const bytes = await readBoundedFile(
    path,
    inputLimit,
    constants.O_RDONLY | constants.O_NONBLOCK | constants.O_NOFOLLOW,
  );
  return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
}

export async function readTarget(directory: string) {
  let value: unknown;
  try {
    value = JSON.parse(await readTargetText(directory, "target.json"));
  } catch {
    throw new Error("target_config_unreadable_or_invalid");
  }
  if (typeof value !== "object" || value === null || Array.isArray(value))
    throw new Error("target_config_unreadable_or_invalid");
  const target = value as Record<string, unknown>;
  if (Object.keys(target).some((key) => !fields.has(key)))
    throw new Error("target_config_unknown_field");
  const { endpoint, model, apiVersion, authMode } = target;
  if (typeof endpoint !== "string" || !endpoint.trim() || typeof model !== "string" || !model.trim())
    throw new Error("target_endpoint_and_model_required");
  if (typeof apiVersion !== "string") throw new Error("invalid_api_version");
  if (authMode !== "api_key" && authMode !== "bearer" && authMode !== "none")
    throw new Error("invalid_auth_mode");
  return { endpoint, model, apiVersion, authMode };
}

export async function readTargetToken(directory: string): Promise<string> {
  try {
    const token = (await readTargetText(directory, "token.txt")).trim();
    if (!/^[\x21-\x7e]+$/u.test(token)) throw new Error("invalid_token");
    return token;
  } catch {
    throw new Error("target_token_unavailable");
  }
}
