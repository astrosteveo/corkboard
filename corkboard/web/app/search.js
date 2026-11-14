// Ctrl-K search: jump to an item or doc, or run an action such as New task or Go to v0.3.
// Items and docs come from /api/search, which ranks them (search.py). Actions are matched here and
// come first. The arrow keys move through the results, Enter opens one, and Esc closes the box.
import { html, useEffect, useRef, useState } from "./lib.js";
import { openNewItem } from "./newitem.js";
import { navigate } from "./router.js";
import { Icon, STATUS_LABEL, docUrl, panelHref, releaseUrl } from "./ui.js";

const OPEN = "corkboard:search";

export function openSearch() {
  dispatchEvent(new Event(OPEN));
}

// Listens for openSearch and Ctrl-K, and shows the box. Ctrl-K again closes it.
export function Search({ project }) {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const onOpen = () => setOpen(true);
    const onKey = (event) => {
      if (event.key.toLowerCase() !== "k" || !(event.ctrlKey || event.metaKey) || event.altKey || event.shiftKey) return;
      event.preventDefault();
      // Not over another dialog, such as the new item form.
      setOpen((current) => !current && !document.querySelector("dialog[open]"));
    };
    addEventListener(OPEN, onOpen);
    addEventListener("keydown", onKey);
    return () => {
      removeEventListener(OPEN, onOpen);
      removeEventListener("keydown", onKey);
    };
  }, []);
  if (!open || !project) return null;
  return html`<${SearchDialog} project=${project} close=${() => setOpen(false)} />`;
}

function SearchDialog({ project, close }) {
  const dialog = useRef(null);
  const [query, setQuery] = useState("");
  const [found, setFound] = useState({ text: "", results: [] });
  const [active, setActive] = useState(0);
  const pending = useRef(Promise.resolve([]));
  const latest = useRef(0);
  const text = query.trim();

  useEffect(() => {
    dialog.current?.showModal();
  }, []);

  // Ask the server for each new text. Only the latest answer counts, so a slow one can't replace it.
  useEffect(() => {
    setActive(0);
    const ticket = ++latest.current;
    pending.current = text
      ? fetch(`/api/search?q=${encodeURIComponent(text)}`, { cache: "no-store" })
          .then((response) => (response.ok ? response.json() : { results: [] }))
          .then((data) => data.results)
          .catch(() => [])
      : Promise.resolve([]);
    pending.current.then((results) => {
      if (ticket === latest.current) setFound({ text, results });
    });
  }, [text]);

  const actions = matchActions(project, text);
  const rows = [...actions, ...(text ? found.results : [])];
  const index = Math.min(active, rows.length - 1);

  useEffect(() => {
    document.getElementById(`search-row-${index}`)?.scrollIntoView({ block: "nearest" });
  }, [index]);

  function open(row) {
    if (!row) return;
    close();
    if (row.kind === "item") navigate(panelHref(row.id));
    else if (row.kind === "doc") navigate(docUrl(row.name));
    else row.run();
  }

  // Enter before the answer for the latest text arrives waits for it, so typing fast and pressing
  // Enter still opens the first match.
  async function openActive() {
    if (found.text === text) {
      open(rows[index]);
      return;
    }
    const results = await pending.current;
    open([...actions, ...results][0]);
  }

  function onKeyDown(event) {
    const count = rows.length;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (count) setActive((index + (event.key === "ArrowDown" ? 1 : count - 1)) % count);
    } else if (event.key === "Enter") {
      event.preventDefault();
      openActive();
    } else if (event.key === "Escape") {
      // Handled here, so the item panel under the box doesn't close too.
      event.preventDefault();
      close();
    }
  }

  return html`<dialog class="search-dialog" ref=${dialog} aria-label="Search"
    onCancel=${(event) => {
      event.preventDefault();
      close();
    }}
    onClick=${(event) => {
      if (event.target === dialog.current) close(); // a click on the backdrop
    }}>
    <div class="search-box">
      <${Icon} name="search" />
      <input class="search-input" type="text" role="combobox" aria-label="Search items and docs, or run an action"
        aria-expanded="true" aria-controls="search-results" aria-autocomplete="list"
        aria-activedescendant=${rows.length ? `search-row-${index}` : null}
        placeholder="Search items and docs, or type an action…" autocomplete="off" spellcheck="false"
        value=${query} onInput=${(event) => setQuery(event.currentTarget.value)} onKeyDown=${onKeyDown} />
    </div>
    <ul class="search-results" id="search-results" role="listbox" aria-label="Results">
      ${rows.map(
        (row, i) => html`<li key=${rowKey(row)} id=${`search-row-${i}`} role="option" aria-selected=${i === index ? "true" : "false"}
          class=${i === index ? "search-row active" : "search-row"}
          onMouseMove=${() => i !== index && setActive(i)} onClick=${() => open(row)}>
          <${Row} row=${row} />
        </li>`,
      )}
    </ul>
    ${text && found.text === text && !rows.length ? html`<p class="empty search-empty">Nothing matches “${text}”.</p>` : null}
    <p class="search-foot small muted"><kbd>↑</kbd> <kbd>↓</kbd> to move · <kbd>Enter</kbd> to open · <kbd>Esc</kbd> to close</p>
  </dialog>`;
}

function Row({ row }) {
  if (row.kind === "item") {
    return html`<span class="search-line">
        <span class="id">${row.id}</span>
        <span class="search-title">${row.title}</span>
        ${row.type === "bug" ? html`<span class="chip bug">Bug</span>` : row.type === "epic" ? html`<span class="chip">Epic</span>` : null}
        <span class=${`chip status-${row.status}`}>${STATUS_LABEL[row.status] ?? row.status}</span>
      </span>
      ${row.snippet ? html`<span class="search-snippet">${row.snippet}</span>` : null}`;
  }
  if (row.kind === "doc") {
    return html`<span class="search-line">
        <${Icon} name="docs" size=${15} />
        <span class="search-title">${row.name}.md</span>
        <span class="small muted">doc</span>
      </span>
      ${row.snippet ? html`<span class="search-snippet">${row.snippet}</span>` : null}`;
  }
  return html`<span class="search-line">
    <${Icon} name=${row.icon} size=${15} />
    <span class="search-title">${row.label}</span>
    ${row.detail ? html`<span class="small muted">${row.detail}</span>` : null}
  </span>`;
}

function rowKey(row) {
  return row.kind === "item" ? row.id : row.kind === "doc" ? `doc:${row.name}` : `action:${row.label}`;
}

const SCREENS = [
  ["Now", "/"],
  ["Board", "/board"],
  ["Releases", "/releases"],
  ["List", "/list"],
  ["Docs", "/docs"],
];

// The actions whose label has every word typed. With nothing typed, all of them.
function matchActions(project, text) {
  const actions = [
    ...["task", "bug", "epic"].map((type) => ({
      kind: "action",
      icon: "plus",
      label: `New ${type}`,
      run: () => openNewItem({ type }),
    })),
    ...SCREENS.map(([name, href]) => ({ kind: "action", icon: "chevron", label: `Go to ${name}`, run: () => navigate(href) })),
    ...project.releases.map((release) => ({
      kind: "action",
      icon: "releases",
      label: `Go to ${release.name}`,
      detail: release.status,
      run: () => navigate(releaseUrl(release.name)),
    })),
  ];
  const words = text.toLowerCase().split(/\s+/).filter(Boolean);
  return actions.filter((action) => words.every((word) => action.label.toLowerCase().includes(word)));
}
