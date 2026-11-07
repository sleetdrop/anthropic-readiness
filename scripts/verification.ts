/** Require real executed tests; a successful process alone is insufficient. */
export function verifyTests(output: string, exitCode: number | null) {
  const names = ["tests", "pass", "fail", "cancelled", "skipped", "todo"] as const;
  const counts: Record<string, number> = {};
  for (const name of names) {
    const match = output.match(new RegExp(`^# ${name} (\\d+)\\r?$`, "mu"));
    if (!match) return { passed: false, reason: "missing_test_summary", counts: null };
    counts[name] = Number(match[1]);
    if (!Number.isSafeInteger(counts[name]))
      return { passed: false, reason: "invalid_test_summary", counts: null };
  }
  const complete =
    exitCode === 0 &&
    (counts.tests ?? 0) > 0 &&
    counts.pass === counts.tests &&
    counts.fail === 0 &&
    counts.cancelled === 0 &&
    counts.skipped === 0 &&
    counts.todo === 0;
  return {
    passed: complete,
    reason: complete ? "completed" : "incomplete_or_failed_tests",
    counts,
  };
}
