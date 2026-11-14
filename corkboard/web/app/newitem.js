// The new item form, opened with + New or the c key. It creates the item the way
// `corkboard new` does, through the write API, then opens it in the side panel.
import { write } from "./api.js";
import { html, useEffect, useRef, useState } from "./lib.js";
import { navigate } from "./router.js";

const OPEN = "corkboard:new-item";

// Open the form from anywhere, optionally with an epic or release already chosen.
export function openNewItem(defaults = {}) {
  dispatchEvent(new CustomEvent(OPEN, { detail: defaults }));
}

// Listens for openNewItem and the c key, and shows the form.
export function NewItem({ project, refresh }) {
  const [defaults, setDefaults] = useState(null);
  useEffect(() => {
    const onOpen = (event) => setDefaults(event.detail ?? {});
    const onKey = (event) => {
      if (event.key !== "c" || event.ctrlKey || event.metaKey || event.altKey || event.defaultPrevented) return;
      const target = event.target;
      if (target instanceof HTMLElement && (target.isContentEditable || target.closest("input, textarea, select, dialog"))) return;
      event.preventDefault();
      setDefaults(defaultsFromUrl());
    };
    addEventListener(OPEN, onOpen);
    addEventListener("keydown", onKey);
    return () => {
      removeEventListener(OPEN, onOpen);
      removeEventListener("keydown", onKey);
    };
  }, []);
  if (!defaults || !project) return null;
  return html`<${NewItemDialog} project=${project} defaults=${defaults} refresh=${refresh} close=${() => setDefaults(null)} />`;
}

// On the board, a new item starts in the release and epic it's filtered to; on the list, in its release.
function defaultsFromUrl() {
  const query = new URLSearchParams(location.search);
  if (location.pathname === "/list") return { release: query.get("release") ?? undefined };
  if (location.pathname !== "/board") return {};
  const epic = query.get("epic");
  return { release: query.get("release") ?? undefined, parent: epic && epic !== "none" ? epic : undefined };
}

function NewItemDialog({ project, defaults, refresh, close }) {
  const dialog = useRef(null);
  const epics = project.items.filter((item) => item.type === "epic");
  const [form, setForm] = useState({
    type: defaults.type ?? "task",
    title: "",
    parent: defaults.parent ?? "",
    release: defaults.release === "none" ? "" : (defaults.release ?? project.active_release ?? ""),
    priority: "medium",
    owner: "claude",
    labels: "",
    body: "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const update = (key) => (event) => setForm({ ...form, [key]: event.currentTarget.value });
  const isEpic = form.type === "epic";
  const parent = isEpic ? "" : form.parent;

  useEffect(() => {
    dialog.current?.showModal();
  }, []);

  async function submit(event) {
    event.preventDefault();
    if (!form.title.trim() || busy) return;
    const fields = { priority: form.priority, owner: form.owner };
    if (parent) fields.parent = parent;
    else if (form.release) fields.release = form.release;
    const labels = form.labels.split(",").map((label) => label.trim()).filter(Boolean);
    if (labels.length) fields.labels = labels;
    setBusy(true);
    setError("");
    try {
      const answer = await write("/api/items", { type: form.type, title: form.title, fields, body: form.body });
      await refresh();
      close();
      const query = new URLSearchParams(location.search);
      query.set("item", answer.id);
      const base = location.pathname.startsWith("/items/") ? "/board" : location.pathname;
      navigate(`${base}?${query}`);
    } catch (problem) {
      setError(problem.message);
      setBusy(false);
    }
  }

  return html`<dialog class="new-dialog" ref=${dialog} aria-labelledby="new-heading"
    onKeyDown=${(event) => {
      if (event.key === "Escape") {
        // Handled here, so the item panel under the form doesn't close too.
        event.preventDefault();
        close();
      }
    }}
    onCancel=${(event) => {
      event.preventDefault();
      close();
    }}>
    <form onSubmit=${submit}>
      <h2 id="new-heading">New item</h2>
      <div class="form-row">
        <div class="form-field"><label for="new-type">Type</label>
          <select id="new-type" class="select" value=${form.type} onChange=${update("type")}>
            <option value="task">Task</option><option value="bug">Bug</option><option value="epic">Epic</option>
          </select>
        </div>
        <div class="form-field grow"><label for="new-title">Title</label>
          <input id="new-title" class="input" value=${form.title} onInput=${update("title")} required autofocus
            placeholder="What needs doing" />
        </div>
      </div>
      <div class="form-row">
        ${isEpic
          ? null
          : html`<div class="form-field grow"><label for="new-epic">Epic</label>
              <select id="new-epic" class="select" value=${form.parent} onChange=${update("parent")}>
                <option value="">No epic</option>
                ${epics.map((epic) => html`<option value=${epic.id}>${epic.id} ${epic.title}</option>`)}
              </select>
            </div>`}
        ${parent
          ? html`<span class="form-field form-note small muted">Release: from its epic</span>`
          : html`<div class="form-field"><label for="new-release">Release</label>
              <select id="new-release" class="select" value=${form.release} onChange=${update("release")}>
                <option value="">No release</option>
                ${project.releases.map((release) => html`<option value=${release.name}>${release.name}</option>`)}
              </select>
            </div>`}
      </div>
      <div class="form-row">
        <div class="form-field"><label for="new-priority">Priority</label>
          <select id="new-priority" class="select" value=${form.priority} onChange=${update("priority")}>
            <option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
          </select>
        </div>
        <div class="form-field"><label for="new-owner">Owner</label>
          <select id="new-owner" class="select" value=${form.owner} onChange=${update("owner")}>
            <option value="claude">Claude</option><option value="me">You</option>
          </select>
        </div>
        <div class="form-field grow"><label for="new-labels">Labels</label>
          <input id="new-labels" class="input" value=${form.labels} onInput=${update("labels")} placeholder="ui, board" />
        </div>
      </div>
      <div class="form-field"><label for="new-description">Description <span class="muted small">(optional, Markdown; a ## Subtasks checklist works too)</span></label>
        <textarea id="new-description" class="textarea" value=${form.body} onInput=${update("body")} rows="6"></textarea>
      </div>
      ${error ? html`<p class="notice error" role="alert">${error}</p>` : null}
      <div class="dialog-buttons">
        <button class="btn" type="button" onClick=${close}>Cancel</button>
        <button class="btn primary" type="submit" disabled=${busy || !form.title.trim()}>${busy ? "Creating…" : "Create"}</button>
      </div>
    </form>
  </dialog>`;
}
