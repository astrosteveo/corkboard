// The Board screen. It's filled in by its own item; for now it shows where it will be.
import { html } from "./lib.js";
import { pageTitle } from "./ui.js";

export function BoardPage({ project }) {
  pageTitle("Board", project);
  return html`<header class="page-head"><div class="page-title">
    <h1>Board</h1>
    <p>Tasks and bugs in a release, in columns by status.</p>
  </div></header>
  <p class="muted">This screen isn't built yet.</p>`;
}
