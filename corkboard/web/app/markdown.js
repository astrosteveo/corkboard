// Markdown with raw HTML turned off. Item descriptions and docs come from the repo, and a doc in
// a cloned repo must never be able to run a script in this page, which can write files.
import { Marked } from "../vendor/marked.esm.js";
import { html, useMemo } from "./lib.js";
import { STATUS_LABEL, panelHref } from "./ui.js";

const SAFE_PROTOCOLS = new Set(["http:", "https:", "mailto:"]);

// An item ID on its own, as the server finds mentions: EX-12, but not inside EX-120 or XEX-12.
const ITEM_ID = /(?<![A-Za-z0-9])[A-Z][A-Z0-9]*-[0-9]+(?![0-9])/g;

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
// "jav&#x61;script:" or a leading space don't get through. Given the project's items by ID, item
// IDs become chips.
export function renderMarkdown(text, items = null) {
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
  if (items) addChips(template.content, items);
  return template.innerHTML;
}

// Each ID of an item in the project becomes a chip with the item's current title and status,
// linking to it. IDs inside links and code stay as they are, and so do IDs with no item.
function addChips(root, items) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const texts = [];
  while (walker.nextNode()) texts.push(walker.currentNode);
  for (const node of texts) {
    if (node.parentElement?.closest("a, code, pre")) continue;
    const text = node.nodeValue;
    const parts = [];
    let last = 0;
    for (const match of text.matchAll(ITEM_ID)) {
      const item = items.get(match[0]);
      if (!item) continue;
      parts.push(text.slice(last, match.index), chip(item));
      last = match.index + match[0].length;
    }
    if (parts.length) node.replaceWith(...parts, text.slice(last));
  }
}

// Built from elements and textContent, so a title can't add markup.
function chip(item) {
  const status = STATUS_LABEL[item.status] ?? item.status;
  const link = document.createElement("a");
  link.className = `id-chip status-${item.status}`;
  link.href = panelHref(item.id);
  link.title = `${item.id} ${item.title} · ${status}`;
  const parts = [
    ["id", item.id],
    ["chip-title", item.title],
    ["chip-status", status],
  ];
  for (const [className, text] of parts) {
    const span = document.createElement("span");
    span.className = className;
    span.textContent = text;
    link.append(span);
  }
  return link;
}

// The rendered Markdown. Chips link to the item's panel over the current screen, so they're built
// again when the URL changes, as well as when the project does.
export function Markdown({ text, items = null, className = "" }) {
  const where = location.pathname + location.search;
  const rendered = useMemo(() => renderMarkdown(text, items), [text, items, where]);
  return html`<div class=${`markdown ${className}`} dangerouslySetInnerHTML=${{ __html: rendered }}></div>`;
}
