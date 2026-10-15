# Stage A report visual review

The synthetic mixed result was rendered with the package's HTML and Markdown
renderers. It contains three cases, three synthetic transport calls and 39
assertions; the deliberate duplicate start fails `STR-START`. It is not a real
endpoint assessment. Its evidence files are intentionally not bundled, and the
report visibly says independent verification is unavailable.

Observed views:

- In-app browser: 1280 x 900 desktop layout and 390 x 844 narrow layout.
  Document widths were 1265 and 375 pixels respectively, with no horizontal
  document overflow. Header conclusion, narrow failure table and references
  were visually inspected; Chinese text and long IDs remained readable.
- A4 print CSS: isolated static HTML-to-PDF rendering, with scripts disabled and
  network requests blocked. All four resulting pages were rasterized and
  inspected. No missing Chinese glyphs, clipped text, overlapping rows or
  broken reference/footer layout were observed.
- The first verbose draft produced seven pages. The final presentation lists
  PASS assertion IDs/versions compactly and details every non-PASS assertion;
  JSON retains all assertion conditions, summaries and evidence references.

Local preview artifacts: `artifacts/report-visual-v3/` contains HTML, Markdown,
JSON, the print PDF and four page PNGs. These are ignored development artifacts,
not compatibility certificates. The native in-app print command was unavailable;
print acceptance used the separate static-document renderer. Product tests and
wheel verification ran in Linux, independently of this optional visual tooling.
