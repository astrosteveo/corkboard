// One item, as a full page at /items/<ID> or in the side panel over another screen (?item=<ID>).
// Every change goes through the write API, which makes the same file change as the matching
// corkboard command, logged as you.
import { write } from "./api.js";
import { MarkdownEditor } from "./editor.js";
import { html, useEffect, useRef, useState } from "./lib.js";
import { Markdown } from "./markdown.js";
import { navigate } from "./router.js";
import {
  Icon,
  PrState,
  Progress,
  STATUS_ICON,
  STATUS_LABEL,
  docUrl,
  itemUrl,
  pageTitle,
  panelHref,
  releaseUrl,
  shortDate,
  subtaskCount,
} from "./ui.js";

const STATUSES = ["backlog", "todo", "in-progress", "waiting", "done", "cancelled"];

export function ItemPage({ project, id, refresh }) {
  const item = project.byId.get(id);
  if (!item) {
    pageTitle(`${id} not found`, project);
    return html`<div class="page-title"><h1>${id}</h1><p>There's no item ${id} in this project.</p></div>`;
  }
  pageTitle(`${item.id} ${item.title}`, project);
  return html`<article class="item-page">
    <${ItemView} key=${item.id} project=${project} item=${item} refresh=${refresh} />
  </article>`;
}

// The side panel: the item over the screen you came from. Esc or × closes it.
export function ItemPanel({ project, id, refresh }) {
  const item = project.byId.get(id);
  const panel = useRef(null);
  const close = () => {
    const query = new URLSearchParams(location.search);
    query.delete("item");
    const search = query.toString();
    navigate(`${location.pathname}${search ? `?${search}` : ""}`);
  };
  useEffect(() => {
    panel.current?.focus();
  }, [id]);
  useEffect(() => {
    const onKey = (event) => {
      // An editor with unsaved text marks itself; its Cancel is the way to throw the text away.
      const unsaved = panel.current?.querySelector("[data-unsaved]");
      if (event.key === "Escape" && !event.defaultPrevented && !unsaved) close();
    };
    addEventListener("keydown", onKey);
    return () => removeEventListener("keydown", onKey);
  }, []);
  return html`<div class="panel-layer">
    <div class="panel-backdrop" onClick=${close}></div>
    <aside class="panel" role="dialog" aria-label=${item ? `${item.id} ${item.title}` : id} tabindex="-1" ref=${panel}>
      <div class="panel-bar">
        <a class="btn small-btn" href=${itemUrl(id)}><${Icon} name="expand" size=${14} /> Full page</a>
        <button class="icon-btn" type="button" aria-label="Close" onClick=${close}><${Icon} name="close" /></button>
      </div>
      ${item
        ? html`<${ItemView} key=${item.id} project=${project} item=${item} refresh=${refresh} />`
        : html`<p class="empty">There's no item ${id} in this project.</p>`}
    </aside>
  </div>`;
}

// Runs changes for one item, keeping the last error and any warnings to show. While a change
// is saving, `shown` gives the new value for the fields it changes, so a select or checkbox
// doesn't flip back until the project reloads.
function useChanges(item, refresh) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [warnings, setWarnings] = useState([]);
  const [pending, setPending] = useState({});
  async function change(action, data, preview = {}) {
    setPending(preview);
    setBusy(true);
    setError("");
    try {
      const answer = await write(`/api/items/${encodeURIComponent(item.id)}/${action}`, data);
      setWarnings(answer.warnings ?? []);
      await refresh();
      return true;
    } catch (problem) {
      setError(problem.message);
      return false;
    } finally {
      setBusy(false);
      setPending({});
    }
  }
  const shown = (key, actual) => (key in pending ? pending[key] : actual);
  return { busy, error, warnings, change, shown, refresh };
}

// What /api/items/<ID> adds to the project view: the docs and items that mention the item, and
// its development. The server runs git and gh for it, so it arrives after the rest of the panel,
// and loads again when the project changes.
function useExtras(item, project) {
  const [extras, setExtras] = useState(null);
  useEffect(() => {
    let current = true;
    fetch(`/api/items/${encodeURIComponent(item.id)}`, { cache: "no-store" })
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => current && setExtras(data))
      .catch(() => current && setExtras(null));
    return () => {
      current = false;
    };
  }, [item.id, project]);
  return extras?.id === item.id ? extras : null;
}

// Rendered with key=${item.id}, so moving to another item starts fresh: no unsent text carries over.
export function ItemView({ project, item, refresh }) {
  const changes = useChanges(item, refresh);
  const extras = useExtras(item, project);
  const epic = item.parent ? project.byId.get(item.parent) : null;
  return html`<div class="item">
    <div class="crumbs small muted">
      ${epic ? html`<a href=${panelHref(epic.id)}>${epic.title}</a><span aria-hidden="true"> › </span>` : null}
      <span class="id">${item.id}</span>
      ${item.type === "epic" ? html`<span class="chip">Epic</span>` : null}
    </div>
    <${Title} item=${item} changes=${changes} />
    <${Fields} project=${project} item=${item} changes=${changes} />
    <${Labels} item=${item} changes=${changes} />
    ${changes.error ? html`<p class="notice error" role="alert">${changes.error}</p>` : null}
    ${changes.warnings.map((warning) => html`<p class="notice warn-note" role="status">${warning}</p>`)}
    ${item.status === "waiting" && item.waiting_message
      ? html`<p class="notice waiting-note"><strong>Waiting on you:</strong> ${item.waiting_message}</p>`
      : null}
    ${item.open_blockers.length
      ? html`<p class="small blocked-note">Blocked by ${item.open_blockers.map(
          (blocker, index) => html`${index ? ", " : ""}<a href=${panelHref(blocker)}>${blocker}</a>`,
        )}</p>`
      : null}
    <${Description} item=${item} items=${project.byId} refresh=${refresh} />
    ${item.type === "epic"
      ? html`<${EpicTasks} project=${project} epic=${item} />`
      : html`<${Subtasks} item=${item} changes=${changes} />`}
    <${Links} project=${project} item=${item} refresh=${refresh} />
    <${Development} development=${extras?.development} />
    <${Activity} item=${item} changes=${changes} />
    <${Mentions} mentions=${extras?.mentions} />
  </div>`;
}

function Title({ item, changes }) {
  const [text, setText] = useState(item.title);
  useEffect(() => setText(item.title), [item.title]);
  // Blur saves what the input holds, not `text`: Esc resets the input and blurs in one handler,
  // before Preact re-renders, so `text` would still be the typed title.
  const save = (value) => {
    const title = value.trim().replace(/\s+/g, " ");
    if (!title) setText(item.title);
    else if (title !== item.title) changes.change("set", { fields: { title } });
  };
  // The heading's text is the title, for screen readers; the field shows it and edits it in place.
  return html`<h1 class="title-field">
    <span class="visually-hidden">${item.title}</span>
    <input class="item-title" aria-label="Title" value=${text} disabled=${changes.busy}
      onInput=${(event) => setText(event.currentTarget.value)}
      onBlur=${(event) => save(event.currentTarget.value)}
      onKeyDown=${(event) => {
        if (event.key === "Enter") event.currentTarget.blur();
        if (event.key === "Escape") {
          event.preventDefault();
          event.currentTarget.value = item.title;
          setText(item.title);
          event.currentTarget.blur();
        }
      }} />
  </h1>`;
}

function Fields({ project, item, changes }) {
  const [asking, setAsking] = useState(false);
  const [question, setQuestion] = useState("");
  const set = (field, value) => changes.change("set", { fields: { [field]: value } }, { [field]: value });
  const epics = project.items.filter((other) => other.type === "epic");
  const isWork = item.type !== "epic";
  const inheritsRelease = isWork && project.byId.get(item.parent)?.type === "epic";

  return html`<div class="fields">
    <${Field} label="Status">
      <select id="field-status" class=${`field-select status-${changes.shown("status", item.status)}`}
        value=${changes.shown("status", item.status)} disabled=${changes.busy}
        onChange=${(event) => {
          const status = event.currentTarget.value;
          if (status === "waiting") {
            event.currentTarget.value = item.status;
            setAsking(true);
          } else {
            changes.change("move", { status, message: "" }, { status });
          }
        }}>
        ${STATUSES.map((status) => html`<option value=${status}>${STATUS_ICON[status]} ${STATUS_LABEL[status]}</option>`)}
      </select>
    <//>
    <${Field} label="Priority">
      <select id="field-priority" class="field-select" value=${changes.shown("priority", item.priority)} disabled=${changes.busy}
        onChange=${(event) => set("priority", event.currentTarget.value)}>
        <option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
      </select>
    <//>
    <${Field} label="Owner">
      <select id="field-owner" class="field-select" value=${changes.shown("owner", item.owner)} disabled=${changes.busy}
        onChange=${(event) => set("owner", event.currentTarget.value)}>
        <option value="claude">Claude</option><option value="me">You</option>
      </select>
    <//>
    ${isWork
      ? html`<${Field} label="Type">
          <select id="field-type" class="field-select" value=${changes.shown("type", item.type)} disabled=${changes.busy}
            onChange=${(event) => set("type", event.currentTarget.value)}>
            <option value="task">Task</option><option value="bug">Bug</option>
          </select>
        <//>
        <${Field} label="Epic">
          <select id="field-epic" class="field-select" value=${changes.shown("parent", item.parent ?? "")} disabled=${changes.busy}
            onChange=${(event) => set("parent", event.currentTarget.value)}>
            <option value="">No epic</option>
            ${epics.map((epic) => html`<option value=${epic.id}>${epic.id} ${epic.title}</option>`)}
          </select>
        <//>`
      : null}
    <${Field} label="Release">
      ${inheritsRelease
        ? html`<a class="field-static" href=${releaseUrl(item.release)}>${item.release ?? "No release"} (from epic)</a>`
        : html`<select id="field-release" class="field-select" value=${changes.shown("release", item.release ?? "")} disabled=${changes.busy}
            onChange=${(event) => set("release", event.currentTarget.value)}>
            <option value="">No release</option>
            ${project.releases.map((release) => html`<option value=${release.name}>${release.name}</option>`)}
          </select>`}
    <//>
    ${asking
      ? html`<form class="ask" onSubmit=${async (event) => {
          event.preventDefault();
          const message = question.trim();
          if (message && (await changes.change("move", { status: "waiting", message }))) {
            setAsking(false);
            setQuestion("");
          }
        }}>
          <label class="visually-hidden" for="waiting-message">What is it waiting for?</label>
          <input id="waiting-message" class="input" placeholder="What is it waiting for? Moving to waiting needs a message."
            value=${question} onInput=${(event) => setQuestion(event.currentTarget.value)}
            onKeyDown=${(event) => {
              if (event.key === "Escape") {
                event.preventDefault();
                setAsking(false);
              }
            }} ref=${(element) => element && !element.dataset.focused && ((element.dataset.focused = "1"), element.focus())} />
          <button class="btn primary" type="submit" disabled=${!question.trim() || changes.busy}>Move to waiting</button>
          <button class="btn" type="button" onClick=${() => setAsking(false)}>Cancel</button>
        </form>`
      : null}
  </div>`;
}

// The description, and Edit: a Markdown text box with a preview, with the conflict check that
// shows both versions if Claude changed the description while you were editing it.
function Description({ item, items, refresh }) {
  const [editing, setEditing] = useState(false);
  if (editing) {
    const save = async (description, base) => {
      await write(`/api/items/${encodeURIComponent(item.id)}/describe`, { description, base });
      await refresh();
    };
    // Closing loads the project first, so "Use the one on disk" never shows the old text.
    const close = async () => {
      await refresh();
      setEditing(false);
    };
    return html`<${MarkdownEditor} id="description-edit" text=${item.description} noun="description"
      items=${items} save=${save} close=${close} />`;
  }
  return html`<section class="item-section description">
    <div class="section-head">
      <span class="visually-hidden">Description</span>
      <button class="btn small-btn edit-btn" type="button" onClick=${() => setEditing(true)}>
        <${Icon} name="edit" size=${14} /> Edit
      </button>
    </div>
    ${item.description
      ? html`<${Markdown} text=${item.description} items=${items} />`
      : html`<p class="empty">No description.</p>`}
  </section>`;
}

// A labelled field: the control inside has id="field-<label>", so its name is the label alone.
function Field({ label, children }) {
  return html`<div class="field">
    <label class="field-label" for=${`field-${label.toLowerCase()}`}>${label}</label>${children}
  </div>`;
}

function Labels({ item, changes }) {
  const [adding, setAdding] = useState("");
  const save = (labels) => changes.change("set", { fields: { labels } });
  return html`<div class="labels" role="group" aria-label="Labels">
    <span class="field-label">Labels</span>
    ${item.labels.map(
      (label) => html`<span class="chip label">${label}
        <button class="chip-x" type="button" aria-label=${`Remove label ${label}`} disabled=${changes.busy}
          onClick=${() => save(item.labels.filter((other) => other !== label))}>×</button>
      </span>`,
    )}
    <form class="label-add" onSubmit=${async (event) => {
      event.preventDefault();
      const added = adding.split(",").map((label) => label.trim()).filter(Boolean);
      if (!added.length) return;
      if (await save([...new Set([...item.labels, ...added])])) setAdding("");
    }}>
      <label class="visually-hidden" for="label-add">Add a label</label>
      <input id="label-add" class="input small-input" placeholder="+ label" value=${adding}
        onInput=${(event) => setAdding(event.currentTarget.value)} disabled=${changes.busy} />
    </form>
  </div>`;
}

function Subtasks({ item, changes }) {
  const [text, setText] = useState("");
  return html`<section class="item-section">
    <h2 class="section-label">Subtasks ${subtaskCount(item) ?? ""}</h2>
    ${item.subtasks.length
      ? html`<ul class="subtasks">
          ${item.subtasks.map(
            (subtask, index) => html`<li class=${subtask.done ? "done" : ""}>
              <label>
                <input type="checkbox" checked=${changes.shown(`sub${index}`, subtask.done)} disabled=${changes.busy}
                  onChange=${() =>
                    changes.change(
                      "sub",
                      { action: subtask.done ? "undo" : "done", value: String(index + 1) },
                      { [`sub${index}`]: !subtask.done },
                    )} />
                <span>${subtask.text}</span>
              </label>
            </li>`,
          )}
        </ul>`
      : null}
    <form class="inline-add" onSubmit=${async (event) => {
      event.preventDefault();
      if (text.trim() && (await changes.change("sub", { action: "add", value: text.trim() }))) setText("");
    }}>
      <label class="visually-hidden" for="subtask-add">Add a subtask</label>
      <input id="subtask-add" class="input" placeholder="+ Add subtask" value=${text}
        onInput=${(event) => setText(event.currentTarget.value)} disabled=${changes.busy} />
      ${text.trim() ? html`<button class="btn" type="submit" disabled=${changes.busy}>Add</button>` : null}
    </form>
  </section>`;
}

function EpicTasks({ project, epic }) {
  const children = project.children.get(epic.id) ?? [];
  return html`<section class="item-section">
    <h2 class="section-label">Tasks ${epic.progress.done}/${epic.progress.total}
      <${Progress} done=${epic.progress.done} total=${epic.progress.total} small />
    </h2>
    ${children.length
      ? html`<div class="rows">
          ${children.map(
            (child) => html`<a class="row-link" href=${panelHref(child.id)}>
              <span class="status-icon" aria-hidden="true">${STATUS_ICON[child.status]}</span>
              <span class="id">${child.id}</span>
              <span class="title">${child.title}</span>
              ${subtaskCount(child) ? html`<span class="small muted num">${subtaskCount(child)}</span>` : null}
              <span class="small muted">${STATUS_LABEL[child.status]}</span>
            </a>`,
          )}
        </div>`
      : html`<p class="empty">No tasks yet.</p>`}
  </section>`;
}

// Both sides of every link, in the order of the file format's table. Each link is stored on one
// item: the ones this item stores, and the ones other items store that name it.
const LINK_ROWS = [
  ["blocked_by", "Blocked by"],
  ["blocks", "Blocks"],
  ["related_to", "Related to"],
  ["duplicate_of", "Duplicate of"],
  ["duplicated_by", "Duplicated by"],
];

// What + Add link can add: the links an item stores itself, so adding one changes only its file.
const LINK_TYPES = [
  ["blocked_by", "Blocked by"],
  ["related", "Related to"],
  ["duplicate_of", "Duplicate of"],
];

// The changes that remove one link, as [item ID, fields] for each item that stores it. A related
// link can be stored on both items.
function removals(project, item, key, id) {
  const without = (list, gone) => list.filter((other) => other !== gone);
  const other = project.byId.get(id);
  switch (key) {
    case "blocked_by":
      return [[item.id, { blocked_by: without(item.blocked_by, id) }]];
    case "blocks":
      return [[id, { blocked_by: without(other.blocked_by, item.id) }]];
    case "duplicate_of":
      return [[item.id, { duplicate_of: "" }]];
    case "duplicated_by":
      return [[id, { duplicate_of: "" }]];
    default: // related_to
      return [
        ...(item.related.includes(id) ? [[item.id, { related: without(item.related, id) }]] : []),
        ...(other?.related.includes(item.id) ? [[id, { related: without(other.related, item.id) }]] : []),
      ];
  }
}

function Links({ project, item, refresh }) {
  const [type, setType] = useState("blocked_by");
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  // An item is a duplicate of one item at most, so that type is offered only while it has none.
  const types = LINK_TYPES.filter(([field]) => field !== "duplicate_of" || !item.duplicate_of);
  const chosen = types.some(([field]) => field === type) ? type : "blocked_by";
  const rows = LINK_ROWS.flatMap(([key, label]) => {
    const ids = key === "duplicate_of" ? (item.duplicate_of ? [item.duplicate_of] : []) : item[key];
    return ids.map((id) => ({ key, label, id }));
  });

  // What's wrong with linking to this ID, or "" if nothing is.
  function problem(id) {
    if (id === item.id) return "An item can't link to itself.";
    if (!project.byId.has(id)) return `There's no item ${id}.`;
    if (chosen === "blocked_by" && item.blocked_by.includes(id)) return `${item.id} is already blocked by ${id}.`;
    if (chosen === "related" && item.related_to.includes(id)) return `${item.id} is already related to ${id}.`;
    return "";
  }

  async function remove(key, id) {
    setSaving(true);
    setError("");
    try {
      for (const [owner, fields] of removals(project, item, key, id)) {
        await write(`/api/items/${encodeURIComponent(owner)}/set`, { fields });
      }
      await refresh();
    } catch (failure) {
      setError(failure.message);
      await refresh();
    } finally {
      setSaving(false);
    }
  }

  async function add(event) {
    event.preventDefault();
    const typed = text.trim().toUpperCase();
    if (!typed) return;
    const id = /^\d+$/.test(typed) ? `${project.prefix}-${typed}` : typed;
    const wrong = problem(id);
    if (wrong) return setError(wrong);
    const value = chosen === "duplicate_of" ? id : [...item[chosen], id];
    setSaving(true);
    setError("");
    try {
      await write(`/api/items/${encodeURIComponent(item.id)}/set`, { fields: { [chosen]: value } });
      await refresh();
      setText("");
      setType("blocked_by");
    } catch (failure) {
      setError(failure.message);
    } finally {
      setSaving(false);
    }
  }

  return html`<section class="item-section">
    <h2 class="section-label">Links</h2>
    ${rows.length
      ? html`<div class="links">
          ${rows.map(({ key, label, id }) => {
            const other = project.byId.get(id);
            return html`<div class="link-row" key=${`${key}-${id}`}>
              <span class="link-kind small muted">${label}</span>
              ${other
                ? html`<a class="row-link" href=${panelHref(id)}>
                    <span class="status-icon" aria-hidden="true">${STATUS_ICON[other.status]}</span>
                    <span class="id">${id}</span>
                    <span class="title">${other.title}</span>
                    <span class="small muted">${STATUS_LABEL[other.status]}</span>
                  </a>`
                : html`<span class="row-link">
                    <span class="status-icon" aria-hidden="true"></span>
                    <span class="id">${id}</span>
                    <span class="title muted">No such item</span>
                  </span>`}
              <button class="icon-btn link-remove" type="button" disabled=${saving}
                aria-label=${`Remove link: ${label} ${id}`} title="Remove this link"
                onClick=${() => remove(key, id)}><${Icon} name="close" size=${14} /></button>
            </div>`;
          })}
        </div>`
      : null}
    <form class="inline-add link-add" onSubmit=${add}>
      <label class="visually-hidden" for="link-type">Link type</label>
      <select id="link-type" class="select" value=${chosen} disabled=${saving}
        onChange=${(event) => setType(event.currentTarget.value)}>
        ${types.map(([field, label]) => html`<option value=${field}>${label}</option>`)}
      </select>
      <label class="visually-hidden" for="link-add">Item ID to link to</label>
      <input id="link-add" class="input" list="link-ids"
        placeholder=${`+ Add link: item ID, such as ${project.prefix}-12`}
        value=${text} disabled=${saving} autocomplete="off"
        onInput=${(event) => {
          setText(event.currentTarget.value);
          setError("");
        }}
        onKeyDown=${(event) => {
          if (event.key === "Escape" && text) {
            event.preventDefault(); // clear the box first; a second Esc closes the panel
            setText("");
            setError("");
          }
        }} />
      <datalist id="link-ids">
        ${project.items
          .filter((other) => other.id !== item.id)
          .map((other) => html`<option value=${other.id}>${other.title}</option>`)}
      </datalist>
      ${text.trim() ? html`<button class="btn" type="submit" disabled=${saving}>Add link</button>` : null}
    </form>
    ${error ? html`<p class="notice error" role="alert">${error}</p>` : null}
  </section>`;
}

function Activity({ item, changes }) {
  const [note, setNote] = useState("");
  return html`<section class="item-section">
    <h2 class="section-label">Activity</h2>
    <ol class="activity">
      ${item.log.map(
        (entry) => html`<li>
          <span class="when mono small muted">${shortDate(entry.date)} ${entry.time}</span>
          <span class=${`who ${entry.who}`}>${entry.who === "me" ? "you" : "Claude"}</span>
          <span class="what">${entry.text}</span>
        </li>`,
      )}
    </ol>
    <form class="inline-add" onSubmit=${async (event) => {
      event.preventDefault();
      if (note.trim() && (await changes.change("log", { text: note.trim() }))) setNote("");
    }}>
      <label class="visually-hidden" for="note-add">Add a note</label>
      <input id="note-add" class="input" placeholder="Add a note…" value=${note}
        onInput=${(event) => setNote(event.currentTarget.value)} disabled=${changes.busy} />
      ${note.trim() ? html`<button class="btn" type="submit" disabled=${changes.busy}>Add note</button>` : null}
    </form>
  </section>`;
}

// The branches, pull requests and commits that mention the item, as corkboard show lists them.
// Hidden when there are none.
function Development({ development }) {
  if (!development) return null;
  const { branches, pull_requests: pulls, commits } = development;
  if (!branches.length && !pulls.length && !commits.length) return null;
  return html`<section class="item-section">
    <h2 class="section-label">Development</h2>
    <ul class="development">
      ${branches.map(
        (name) => html`<li>
          <span class="dev-kind small muted">Branch</span>
          <span class="what mono small">${name}</span>
        </li>`,
      )}
      ${pulls.map(
        (pr) => html`<li>
          <span class="dev-kind small muted">PR</span>
          <span class="what">
            ${pr.url.startsWith("https://")
              ? html`<a href=${pr.url} target="_blank" rel="noopener noreferrer">#${pr.number} ${pr.title}</a>`
              : html`#${pr.number} ${pr.title}`}
          </span>
          <${PrState} pr=${pr} />
        </li>`,
      )}
      ${commits.map(
        (commit) => html`<li>
          <span class="dev-kind mono small muted">${commit.hash}</span>
          <span class="what">${commit.subject}</span>
          <span class="small muted nowrap">${shortDate(commit.date)}</span>
        </li>`,
      )}
    </ul>
  </section>`;
}

// The docs and items that mention this item, each linking to its page or panel.
function Mentions({ mentions }) {
  if (!mentions?.length) return null;
  return html`<p class="small muted mentions">Mentioned in ${mentions.map(
    (mention, index) => html`${index ? " · " : ""}${
      mention.item
        ? html`<a href=${panelHref(mention.item)}>${mention.item}</a>`
        : html`<a href=${docUrl(mention.doc)}>${mention.title}</a> (doc)`
    }`,
  )}</p>`;
}
