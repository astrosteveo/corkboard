// Markdown with raw HTML turned off. Item descriptions and docs come from the repo, and a doc in
// a cloned repo must never be able to run a script in this page, which can write files.
import { Marked } from "../vendor/marked.esm.js";
import { html, useMemo } from "./lib.js";

const SAFE_PROTOCOLS = new Set(["http:", "https:", "mailto:"]);

const marked = new Marked({ gfm: true, async: false });
marked.use({
  renderer: {
    // Raw HTML in the Markdown shows as text instead of becoming elements.
    html: ({ text }) => escapeHtml(text),
  },
});

export function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

// The Markdown as HTML, with any link or image whose URL isn't http, https, mailto or a path on
// this site left without one. The browser's own URL parser decides, so tricks like
// "jav&#x61;script:" or a leading space don't get through.
export function renderMarkdown(text) {
  const template = document.createElement("template");
  template.innerHTML = marked.parse(text ?? "");
  for (const element of template.content.querySelectorAll("a[href], img[src]")) {
    const attribute = element.tagName === "A" ? "href" : "src";
    let url = null;
    try {
      url = new URL(element.getAttribute(attribute), location.href);
    } catch {
      url = null;
    }
    if (!url || !SAFE_PROTOCOLS.has(url.protocol)) {
      element.removeAttribute(attribute);
    } else if (element.tagName === "A" && url.origin !== location.origin) {
      element.setAttribute("target", "_blank");
      element.setAttribute("rel", "noopener noreferrer");
    }
  }
  return template.innerHTML;
}

export function Markdown({ text, className = "" }) {
  const rendered = useMemo(() => renderMarkdown(text), [text]);
  return html`<div class=${`markdown ${className}`} dangerouslySetInnerHTML=${{ __html: rendered }}></div>`;
}
