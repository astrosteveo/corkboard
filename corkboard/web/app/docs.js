// The Docs screen: the pages in .project/docs/ as a tree, and one page rendered as Markdown with
// item IDs as chips. /docs/<name> shows docs/<name>.md, so a link between pages such as
// [CLI](cli.md) works here the way it does on GitHub. Edit changes the page's file, with the same
// conflict check as item descriptions, and + New page creates one.
import { useJson, write } from "./api.js";
import { MarkdownEditor } from "./editor.js";
import { html, useEffect, useState } from "./lib.js";
import { Markdown } from "./markdown.js";
import { navigate } from "./router.js";
import { Icon, STATUS_ICON, STATUS_LABEL, docUrl, pageTitle, panelHref, shortDate } from "./ui.js";

export function DocsPage({ project, route }) {
  const list = useJson("/api/docs", project);
  const page = useJson(route.doc ? `/api${docUrl(route.doc)}` : null, project);
  const docs = list.data?.docs;
  const [editing, setEditing] = useState(null); // the name of the page being edited
  const [creating, setCreating] = useState(false);
  useEffect(() => {
    setEditing((name) => (name === route.doc ? name : null));
    setCreating(false);
  }, [route.doc]);

  // A new page opens in the editor, since it's only a heading so far.
  async function created(name) {
    await list.reload();
    setEditing(name);
    navigate(docUrl(name));
  }

  let body;
  if (creating) {
    pageTitle("New page", project);
    const folder = route.doc?.includes("/") ? route.doc.slice(0, route.doc.lastIndexOf("/")) : "";
    body = html`<${NewPage} docs=${docs ?? []} folder=${folder} created=${created} cancel=${() => setCreating(false)} />`;
  } else if (!route.doc) {
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
  } else if (editing === page.data.name) {
    pageTitle(`Editing ${page.data.title}`, project);
    const save = async (text, base) => {
      await write(`/api${docUrl(page.data.name)}`, { text, base });
      await Promise.all([page.reload(), list.reload()]);
    };
    // Closing loads the page first, so "Use the one on disk" never shows the old text.
    const close = async () => {
      await page.reload();
      setEditing(null);
    };
    body = html`<${MarkdownEditor} key=${page.data.name} id="doc-edit" className="doc-editor" noun="page"
      text=${page.data.text} items=${project.byId} save=${save} close=${close} />`;
  } else {
    pageTitle(page.data.title, project);
    body = html`<div class="doc-bar">
        <button class="btn small-btn edit-btn" type="button" onClick=${() => setEditing(page.data.name)}>
          <${Icon} name="edit" size=${14} /> Edit
        </button>
      </div>
      <${Markdown} className="doc-text" text=${page.data.text} items=${project.byId} />
      <${DocFooter} project=${project} doc=${page.data} />`;
  }

  return html`<div class="docs">
    <${DocsTree} docs=${docs} current=${page.data?.name ?? route.doc} newPage=${() => setCreating(true)} />
    <article class="doc">${body}</article>
  </div>`;
}

// + New page: a title and a folder, and the server makes the file, refusing a name that's taken.
function NewPage({ docs, folder: start, created, cancel }) {
  const [title, setTitle] = useState("");
  const [folder, setFolder] = useState(start);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  // Every folder that has a page, with the folders above it.
  const folders = [
    ...new Set(
      docs.flatMap((doc) => {
        const parts = doc.name.split("/").slice(0, -1);
        return parts.map((_, index) => parts.slice(0, index + 1).join("/"));
      }),
    ),
  ].sort();
  const isDecision = folder.trim().replace(/^\/+|\/+$/g, "") === "decisions";

  async function submit(event) {
    event.preventDefault();
    if (!title.trim() || saving) return;
    setSaving(true);
    setError("");
    try {
      const answer = await write("/api/docs", { title, folder });
      await created(answer.name);
    } catch (problem) {
      setError(problem.message);
      setSaving(false);
    }
  }

  return html`<form class="new-page" onSubmit=${submit}
    onKeyDown=${(event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        cancel();
      }
    }}>
    <div class="page-title"><h1>New page</h1>
      <p>A Markdown file in .project/docs/, starting with the title as its heading.</p>
    </div>
    <div class="form-field">
      <label for="page-title">Title</label>
      <input id="page-title" class="input tall" value=${title} disabled=${saving} autocomplete="off"
        ref=${(element) => element && !element.dataset.focused && ((element.dataset.focused = "1"), element.focus())}
        onInput=${(event) => setTitle(event.currentTarget.value)} />
    </div>
    <div class="form-field">
      <label for="page-folder">Folder <span class="muted small">(empty for docs/ itself; a new name makes a new folder)</span></label>
      <input id="page-folder" class="input tall" list="page-folders" placeholder="docs/" value=${folder}
        disabled=${saving} autocomplete="off" onInput=${(event) => setFolder(event.currentTarget.value)} />
      <datalist id="page-folders">${folders.map((name) => html`<option value=${name}></option>`)}</datalist>
    </div>
    ${isDecision
      ? html`<p class="small muted">Decision records are numbered, so the file name starts with the next number, such as 0002-.</p>`
      : null}
    ${error ? html`<p class="notice error" role="alert">${error}</p>` : null}
    <div class="edit-buttons">
      <button class="btn primary" type="submit" disabled=${saving || !title.trim()}>${saving ? "Creating…" : "Create page"}</button>
      <button class="btn" type="button" disabled=${saving} onClick=${cancel}>Cancel</button>
    </div>
  </form>`;
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

// The docs/ folder: each folder's pages by file name, then its subfolders. Typing in the box lists
// the pages whose path has the text instead.
function DocsTree({ docs, current, newPage }) {
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
    <button class="btn small-btn new-page-btn" type="button" onClick=${newPage}>
      <${Icon} name="plus" size=${14} /> New page
    </button>
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
