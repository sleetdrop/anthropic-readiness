export type ReportLanguage = "zh" | "en";

export function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

/** The caller supplies trusted markup with dynamic text already escaped. */
export function reportDocument(title: string, language: ReportLanguage, body: string): string {
  return `<!doctype html>
<html lang="${language === "zh" ? "zh-CN" : "en"}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>${escapeHtml(title)}</title>
<style>
:root{color-scheme:light dark;--surface:#fcfcfc;--subtle:#f2f2f2;--text:#262626;--muted:#626262;--line:#d7d7d7;--accent:#416b7b;--fail:#984c57;--pass:#397052}
@media(prefers-color-scheme:dark){:root{--surface:#1c1c1c;--subtle:#242424;--text:#dedede;--muted:#a8a8a8;--line:#3b3b3b;--accent:#93b6c5;--fail:#d1949e;--pass:#9bbda9}}
*{box-sizing:border-box}
html{background:var(--surface);color:var(--text)}
body{max-width:65rem;margin:auto;padding:2rem clamp(.85rem,4vw,2.25rem) 3rem;font:15px/1.65 system-ui,-apple-system,"PingFang SC",sans-serif;overflow-wrap:anywhere}
h1,h2,h3{line-height:1.3;margin:0 0 .55rem;font-weight:650}
h1{font-size:clamp(1.55rem,4vw,2rem)}
h2{font-size:1.27rem}
h3{font-size:1.05rem}
section{margin-top:1.7rem;padding-top:1rem;border-top:1px solid var(--line)}
article{padding:1rem 0;border-top:1px solid var(--line)}
p,ol,ul,dl{margin:.55rem 0}
a{color:var(--accent);text-underline-offset:.2em}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
nav{display:flex;flex-wrap:wrap;gap:.35rem 1.15rem;margin-top:1rem;font-size:.9rem}
.muted,.finding-id,.meta{color:var(--muted)}
.meta{font-size:.89rem}
.status-fail{color:var(--fail)}
.status-pass{color:var(--pass)}
code{font-size:.92em}
dt{font-weight:600}
dd{margin:0 0 .35rem}
.comparison{display:grid;grid-template-columns:1fr 1fr;gap:.65rem 1.25rem}
.table-scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.92rem;margin:.6rem 0}
caption{text-align:left;color:var(--muted);padding:.25rem 0}
th,td{border-bottom:1px solid var(--line);padding:.5rem .65rem;text-align:left;vertical-align:top}
thead th{background:var(--subtle)}
tbody th{font-weight:550}
.number{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
.matrix{min-width:39rem}
summary{cursor:pointer;color:var(--accent);font-weight:550}
details{margin:.6rem 0}
:target{scroll-margin-top:1rem}
article:target{border-top-color:var(--accent)}
@media(max-width:34rem){
 .comparison{grid-template-columns:1fr}th,td{padding:.45rem .4rem}
 .capability-table thead th:nth-child(-n+2){width:22%}
}
@media print{body{max-width:none;padding:0}h2,h3{break-after:avoid}article,tr{break-inside:avoid}nav{display:none}}
</style>
</head>
<body>
${body}
</body>
</html>
`;
}
