// The Now screen. It's filled in by its own item; for now it shows where it will be.
import { html } from "./lib.js";
import { pageTitle } from "./ui.js";

export function NowPage({ project }) {
  pageTitle("Now", project);
  return html`<header class="page-head"><div class="page-title">
    <h1>Now</h1>
    <p>Where things stand, what Claude needs from you, and what changed.</p>
  </div></header>
  <p class="muted">This screen isn't built yet.</p>`;
}
