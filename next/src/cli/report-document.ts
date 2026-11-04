import { reportNavigation } from "./report-navigation.ts";

export type ReportLanguage = "zh" | "en";

export function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function reportContents(
  sections: ReadonlyArray<readonly [string, string]>,
  language: ReportLanguage,
): string {
  const label = language === "zh" ? "目录" : "Contents";
  const links = sections
    .map(([id, name]) => `<li><a href="#${escapeHtml(id)}">${escapeHtml(name)}</a></li>`)
    .join("");
  return `<nav class="report-contents" aria-label="${label}" data-top-label="${language === "zh" ? "回到顶部" : "Back to top"}"><strong>${label}</strong><ul>${links}</ul></nav>`;
}

/** The caller supplies trusted markup with dynamic text already escaped. */
export function reportDocument(
  title: string,
  language: ReportLanguage,
  body: string,
  { interactiveContents = false } = {},
): string {
  return `<!doctype html>
<html lang="${language === "zh" ? "zh-CN" : "en"}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'${interactiveContents ? reportNavigation.policy : ""}">
<title>${escapeHtml(title)}</title>
<style>
:root{color-scheme:light dark;--surface:#fcfcfc;--subtle:#f2f2f2;--text:#262626;--muted:#626262;--line:#d7d7d7;--rule:#a4a4a4;--accent:#416b7b;--fail:#984c57;--pass:#397052}
@media(prefers-color-scheme:dark){:root{--surface:#1c1c1c;--subtle:#242424;--text:#dedede;--muted:#a8a8a8;--line:#3b3b3b;--rule:#747474;--accent:#93b6c5;--fail:#d1949e;--pass:#9bbda9}}
*{box-sizing:border-box}
html{background:var(--surface);color:var(--text)}
body{max-width:65rem;margin:auto;padding:2rem clamp(.85rem,4vw,2.25rem) 3rem;font:15px/1.65 system-ui,-apple-system,"PingFang SC",sans-serif;overflow-wrap:anywhere}
h1,h2,h3{line-height:1.3;margin:0 0 .55rem;font-weight:650}
h1{font-size:clamp(1.75rem,4vw,2.35rem);line-height:1.16}
html[lang="en"] .report-header h1{font-family:Georgia,serif;font-weight:600}
.report-header{border-top:2px solid var(--accent);padding-top:.85rem}
.report-type{margin:0 0 .45rem;color:var(--muted);font-size:.85rem}
.report-meta{display:flex;flex-wrap:wrap;gap:.4rem 2rem;margin:.8rem 0 0}
.report-meta dt{font-size:.77rem;font-weight:500;color:var(--muted)}
.report-meta dd{margin:0;font-size:.91rem;font-variant-numeric:tabular-nums}
h2{font-size:1.27rem}
h3{font-size:1.05rem}
section{margin-top:1.7rem;padding-top:.9rem;border-top:1px solid var(--line)}
article{padding:1rem 0;border-top:1px solid var(--line)}
article h3 .finding-id{display:inline-block;min-width:2.4em;font:500 .83rem ui-monospace,monospace}
p,ol,ul,dl{margin:.55rem 0}
main p:not(.meta){max-inline-size:76ch}
figure{margin:1rem 0;break-inside:avoid}
figure svg{max-inline-size:100%;height:auto}
figcaption{margin-top:.4rem;color:var(--muted);font-size:.89rem}
a{color:var(--accent);text-underline-offset:.2em}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
nav{display:flex;flex-wrap:wrap;gap:.25rem 1.2rem;margin-top:.9rem;font-size:.88rem}
nav a{display:inline-block;padding:.2rem 0}
.report-overview{display:grid;grid-template-columns:minmax(0,1fr) minmax(11rem,14rem);align-items:start;gap:1rem 2rem}
.report-contents{display:block;margin:.1rem 0 0;padding-left:1rem;border-left:1px solid var(--line)}
.report-contents strong{color:var(--muted);font-size:.81rem;font-weight:600}
.report-contents ul{margin:.2rem 0 0;padding:0;list-style:none}
.report-contents a{padding:.15rem 0}
.report-contents a[aria-current],.report-jump a[aria-current]{font-weight:650}
.report-jump{position:fixed;z-index:1;inset:auto max(1rem,env(safe-area-inset-right)) max(1rem,env(safe-area-inset-bottom)) auto;margin:0;max-width:calc(100vw - 2rem)}
.report-jump[hidden]{display:none}
.report-jump summary,.report-jump nav{background:var(--surface);border:1px solid var(--rule);border-radius:3px}
.report-jump summary{padding:.4rem .7rem;font-size:.86rem}
.report-jump nav{display:block;position:absolute;right:0;bottom:calc(100% + .35rem);width:max-content;min-width:100%;max-width:calc(100vw - 2rem);margin:0;padding:.35rem .75rem}
.report-jump ul{margin:0;padding:0;list-style:none}
.report-jump a{padding:.25rem 0}
.report-jump li:last-child{border-top:1px solid var(--line);margin-top:.2rem;padding-top:.2rem}
@media(max-width:46rem){
 .report-overview{grid-template-columns:1fr}
 .report-contents{margin:0;padding:.65rem 0 0;border-left:0;border-top:1px solid var(--line)}
 .report-contents ul{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.15rem 1rem}
}
.muted,.finding-id,.meta{color:var(--muted)}
.meta{font-size:.89rem}
.status-fail{color:var(--fail)}
.status-pass{color:var(--pass)}
code{font-size:.92em}
.json-source{margin:1.25rem 0 0;padding:.8rem 1rem;overflow:auto;border:1px solid var(--line);background:var(--subtle);white-space:pre;font:13px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;tab-size:2}
.json-source code{font-size:inherit}
.json-key{color:var(--accent);font-weight:600}
.json-string{color:var(--pass)}
.json-number{color:#824f36}
.json-literal{color:#734e88}
@media(prefers-color-scheme:dark){.json-number{color:#dfae8c}.json-literal{color:#d2acd9}}
dt{font-weight:600}
dd{margin:0 0 .35rem}
.comparison{display:grid;grid-template-columns:1fr 1fr;gap:.65rem 1.25rem}
.table-scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;border-top:1px solid var(--rule);font-size:.92rem;margin:.6rem 0}
caption{text-align:left;color:var(--muted);padding:.25rem 0}
th,td{border-bottom:1px solid var(--line);padding:.5rem .65rem;text-align:left;vertical-align:top}
thead th{font-size:.83rem;border-bottom-color:var(--rule)}
.capability-table th:first-child{width:17%}
.capability-table th:nth-child(2){width:16%}
tbody th{font-weight:550}
.number{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
.matrix{min-width:39rem}
summary{cursor:pointer;color:var(--accent);font-weight:550}
details{margin:.6rem 0}
.occurrences{list-style:none;padding:0;margin:.45rem 0;font-size:.87rem}
.occurrences li{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.65fr) max-content;gap:.25rem 1rem;padding:.45rem .1rem;border-top:1px solid var(--line)}
.occurrences li > span:last-child{text-align:right}
:target{scroll-margin-top:1rem}
#report-top{scroll-margin-top:6rem}
article:target{border-top-color:var(--accent)}
@media(max-width:34rem){
 .comparison{grid-template-columns:1fr}th,td{padding:.45rem .4rem}
 .report-meta{gap:.4rem 1rem}
 .capability-table th:first-child,.capability-table th:nth-child(2){width:25%}
 .capability-table thead th{white-space:nowrap}
 .occurrences li{grid-template-columns:minmax(0,1fr) max-content}
 .occurrence-location{grid-column:1/-1;grid-row:2}
}
@media print{
 :root{color-scheme:light;--surface:#fff;--text:#222;--muted:#555;--subtle:#f4f4f4;--line:#ccc;--rule:#777;--accent:#222;--fail:#222;--pass:#222}
 body{max-width:none;padding:0}
 .report-overview{display:block}
 h2,h3{break-after:avoid}
 tr{break-inside:avoid}
 .table-scroll{overflow:visible}
 .matrix{min-width:0}
 .json-source{white-space:pre-wrap;overflow-wrap:anywhere}
 .json-number,.json-literal{color:inherit}
 nav,.report-contents,.report-jump{display:none}
}
</style>
</head>
<body>
${body}
${interactiveContents ? reportNavigation.markup : ""}
</body>
</html>
`;
}
