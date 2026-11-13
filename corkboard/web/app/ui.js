// Small pieces the screens share: icons, chips, avatars and progress bars.
import { html } from "./lib.js";

const ICONS = {
  now: html`<circle cx="12" cy="12" r="8"></circle><circle cx="12" cy="12" r="2.5"></circle>`,
  board: html`<rect x="3" y="4" width="18" height="16" rx="2"></rect><path d="M9 4v16M15 4v16"></path>`,
  releases: html`<path d="M5 21V4"></path><path d="M5 4h12l-2.5 4.5L17 13H5"></path>`,
  up: html`<path d="M12 19V5M5 12l7-7 7 7"></path>`,
  close: html`<path d="M6 6l12 12M18 6 6 18"></path>`,
  expand: html`<path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"></path>`,
  plus: html`<path d="M12 5v14M5 12h14"></path>`,
  check: html`<path d="M5 12.5 10 17 19 7"></path>`,
  chevron: html`<path d="m9 6 6 6-6 6"></path>`,
  copy: html`<rect x="9" y="9" width="11" height="11" rx="2"></rect><path d="M5 15V5a2 2 0 0 1 2-2h8"></path>`,
  edit: html`<path d="M4 20h4L19 9l-4-4L4 16z"></path>`,
};

export function Icon({ name, size = 17, stroke = 2 }) {
  return html`<svg aria-hidden="true" width=${size} height=${size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" stroke-width=${stroke} stroke-linecap="round" stroke-linejoin="round">${ICONS[name]}</svg>`;
}

export function Avatar({ who }) {
  return who === "me"
    ? html`<span class="avatar me" title="Owner: you">You</span>`
    : html`<span class="avatar claude" title="Owner: Claude">C</span>`;
}

export function High({ item }) {
  return item.priority === "high"
    ? html`<span class="high"><${Icon} name="up" size=${12} stroke=${2.5} />High</span>`
    : null;
}

export function Progress({ done, total, small = false }) {
  const percent = total ? Math.round((done / total) * 100) : 0;
  return html`<span class=${small ? "progress small" : "progress"} role="img" aria-label=${`${done} of ${total} done`}>
    <span style=${{ width: `${percent}%` }}></span>
  </span>`;
}

export function subtaskCount(item) {
  if (!item.subtasks.length) return null;
  const done = item.subtasks.filter((subtask) => subtask.done).length;
  return `${done}/${item.subtasks.length}`;
}

export const STATUS_ICON = {
  done: "✓",
  "in-progress": "◐",
  waiting: "?",
  todo: "○",
  backlog: "○",
  cancelled: "✕",
};

export const STATUS_LABEL = {
  backlog: "Backlog",
  todo: "Todo",
  "in-progress": "In progress",
  waiting: "Waiting",
  done: "Done",
  cancelled: "Cancelled",
};

export function itemUrl(id) {
  return `/items/${encodeURIComponent(id)}`;
}

// A link that opens the item in the side panel over the current screen, or, on an item's full
// page, goes to the other item's page.
export function panelHref(id) {
  if (location.pathname.startsWith("/items/")) return itemUrl(id);
  const query = new URLSearchParams(location.search);
  query.set("item", id);
  return `${location.pathname}?${query}`;
}

export function releaseUrl(name) {
  return name ? `/releases/${encodeURIComponent(name)}` : "/releases/none";
}

export function pageTitle(text, project) {
  document.title = project ? `${text} · ${project.name}` : text;
}
