// The Docs screen: the pages in .project/docs/ as a tree, and one page rendered as Markdown with
// item IDs as chips. /docs/<name> shows docs/<name>.md, so a link between pages such as
// [CLI](cli.md) works here the way it does on GitHub.
import { useJson } from "./api.js";
import { html, useState } from "./lib.js";
import { Markdown } from "./markdown.js";
import { STATUS_ICON, STATUS_LABEL, docUrl, pageTitle, panelHref, shortDate } from "./ui.js";

export function DocsPage({ project, route }) {
  const list = useJson("/api/docs", project);
  const page = useJson(route.doc ? `/api${docUrl(route.doc)}` : null, project);
  const docs = list.data?.docs;

  let body;
  if (!route.doc) {
    pageTitle("Docs", project);
    body = html`<div class="page-title"><h1>Docs</h1>
      <p>${docs && !docs.length
        ? "No pages yet. A page is a Markdown file in .project/docs/."
        : "The Markdown pages in .project/docs/. Choose one on the left."}</p>
    </div>`;
  } else if (page.error) {
    pageTitle("Page not found", project);
    body = html`<div class="page-title"><h1>Not found</h1><p>There's no page docs/${route.doc}.md.</p></div>`;
  } else if (!page.data) {
    body = html`<p class="muted">Loading…</p>`;
  } else {
    pageTitle(page.data.title, project);
    body = html`<${Markdown} className="doc-text" text=${page.data.text} items=${project.byId} />
      <${DocFooter} project=${project} doc=${page.data} />`;
  }

  return html`<div class="docs">
    <${DocsTree} docs=${docs} current=${page.data?.name ?? route.doc} />
    <article class="doc">${body}</article>
  </div>`;
}

// The items the page mentions, and when its file last changed.
function DocFooter({ project, doc }) {
  const [date, time] = doc.changed.split(" ");
  const items = doc.mentions.map((id) => project.byId.get(id)).filter(Boolean);
  return html`<footer class="doc-foot small muted">
    ${items.length
      ? html`<p>Mentions: ${items.map(
          (item, index) => html`${index ? ", " : ""}<a href=${panelHref(item.id)}
            title=${`${item.title} · ${STATUS_LABEL[item.status]}`}><span aria-hidden="true">${STATUS_ICON[item.status]} </span>${item.id}</a>`,
        )}</p>`
      : null}
    <p>Changed ${shortDate(date)} ${time} · <span class="mono">${doc.path}</span></p>
  </footer>`;
}

// The docs/ folder: each folder's pages, then its subfolders. Typing in the box lists the pages
// whose title or name has the text instead.
function DocsTree({ docs, current }) {
  const [query, setQuery] = useState("");
  const words = query.trim().toLowerCase();
  let content = null;
  if (docs && words) {
    const found = docs.filter((doc) => `${doc.title}\n${doc.name}`.toLowerCase().includes(words));
    content = found.length
      ? html`<ul class="doc-pages">${found.map((doc) => html`<li key=${doc.name}><${PageLink} doc=${doc} current=${current} /></li>`)}</ul>`
      : html`<p class="empty small">No page matches.</p>`;
  } else if (docs) {
    content = html`<${Folder} folder=${tree(docs)} current=${current} />`;
  }
  return html`<nav class="docs-tree" aria-label="Docs">
    <label class="visually-hidden" for="docs-search">Search docs</label>
    <input id="docs-search" class="input" type="search" placeholder="Search docs…" value=${query}
      onInput=${(event) => setQuery(event.currentTarget.value)} />
    ${content}
  </nav>`;
}

function Folder({ folder, current }) {
  return html`<ul class="doc-pages">
    ${folder.pages.map((doc) => html`<li key=${doc.name}><${PageLink} doc=${doc} current=${current} /></li>`)}
    ${[...folder.folders.values()].map(
      (sub) => html`<li key=${`${sub.name}/`}>
        <details open>
          <summary>${sub.name}</summary>
          <${Folder} folder=${sub} current=${current} />
        </details>
      </li>`,
    )}
  </ul>`;
}

function PageLink({ doc, current }) {
  return html`<a href=${docUrl(doc.name)} title=${`${doc.name}.md`}
    aria-current=${doc.name === current ? "page" : null}>${doc.title}</a>`;
}

// The list of pages as nested folders, each with its own pages and its subfolders by name.
function tree(docs) {
  const root = { name: "", pages: [], folders: new Map() };
  for (const doc of docs) {
    let folder = root;
    for (const part of doc.name.split("/").slice(0, -1)) {
      if (!folder.folders.has(part)) folder.folders.set(part, { name: part, pages: [], folders: new Map() });
      folder = folder.folders.get(part);
    }
    folder.pages.push(doc);
  }
  return root;
}
