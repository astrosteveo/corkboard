// The Releases screen. It's filled in by its own item; for now it shows where it will be.
import { html } from "./lib.js";
import { pageTitle } from "./ui.js";

export function ReleasesPage({ project }) {
  pageTitle("Releases", project);
  return html`<header class="page-head"><div class="page-title">
    <h1>Releases</h1>
    <p>A release and everything in it.</p>
  </div></header>
  <p class="muted">This screen isn't built yet.</p>`;
}
