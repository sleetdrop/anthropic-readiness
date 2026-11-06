import {
  escapeHtml,
  reportDocument,
  type ReportLanguage,
} from "../../report-document.mts";

function highlightedJson(json: string): string {
  const tokens =
    /"[^"\\]*(?:\\.[^"\\]*)*"|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null/gu;
  const colon = /\s*:/y;
  const output: string[] = [];
  let end = 0;
  for (const { 0: token, index } of json.matchAll(tokens)) {
    colon.lastIndex = index + token.length;
    const kind = token.startsWith('"')
      ? colon.test(json)
        ? "key"
        : "string"
      : /^[\d-]/u.test(token)
        ? "number"
        : "literal";
    output.push(
      escapeHtml(json.slice(end, index)),
      `<span class="json-${kind}">${escapeHtml(token)}</span>`,
    );
    end = index + token.length;
  }
  output.push(escapeHtml(json.slice(end)));
  return output.join("");
}

/** Show the exact retained JSON as inert text. The source remains the raw attachment. */
export function renderJsonView(json: string, filename: string, language: ReportLanguage): string {
  const zh = language === "zh";
  const title = zh ? "JSON 证据" : "JSON evidence";
  return reportDocument(
    title,
    language,
    `<header>
<h1>${title}</h1>
<p class="meta"><code>${escapeHtml(filename)}</code></p>
<nav aria-label="${zh ? "证据操作" : "Evidence actions"}">
<a href="report.html">${zh ? "返回检查记录" : "Back to the check record"}</a>
<a href="${escapeHtml(encodeURIComponent(filename))}">${zh ? "打开原始 JSON" : "Open raw JSON"}</a>
</nav>
</header>
<main><pre class="json-source" tabindex="0" role="region" aria-label="${title}"><code>${highlightedJson(json)}</code></pre></main>`,
  );
}
