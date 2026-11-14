// The board: tasks and bugs in one release, in columns by status. Filters live in the URL, so a
// reload or a live update keeps them, and a board view can be shared as a link.
// Dragging a card to another column moves the item, the same as `corkboard move`. The card moves
// at once and goes back if the save fails. Dropping on Waiting asks for the message first.
import { write } from "./api.js";
import { html, useEffect, useRef, useState } from "./lib.js";
import { openNewItem } from "./newitem.js";
import { navigate } from "./router.js";
import { changedSince, useSeen } from "./seen.js";
import { Avatar, DRAG_TYPE, High, Icon, PrBadge, STATUS_LABEL, pageTitle, panelHref, subtaskCount } from "./ui.js";

const SHOWN = ["todo", "in-progress", "waiting", "done"];
const ALL = ["backlog", "todo", "in-progress", "waiting", "done", "cancelled"];
const DONE_LIMIT = 5;
const RANK = { high: 0, medium: 1, low: 2 };

export function BoardPage({ project, route, refresh, pulls }) {
  const seen = useSeen(project);
  const [moved, setMoved] = useState({}); // id → status, while a drop is saving
  const [asking, setAsking] = useState(null); // { id, status } for a drop on Waiting
  const [error, setError] = useState("");
  const statusOf = (item) => moved[item.id] ?? item.status;

  async function moveCard(id, status, message = "") {
    const item = project.byId.get(id);
    if (!item || statusOf(item) === status) return;
    if (status === "waiting" && !message) {
      setAsking({ id, status });
      return;
    }
    setError("");
    setMoved((current) => ({ ...current, [id]: status }));
    try {
      await write(`/api/items/${encodeURIComponent(id)}/move`, { status, message });
      await refresh();
    } catch (problem) {
      setError(`Couldn't move ${id}: ${problem.message} It's back in ${STATUS_LABEL[item.status]}.`);
    } finally {
      setMoved((current) => {
        const rest = { ...current };
        delete rest[id];
        return rest;
      });
    }
  }

  const query = route.query;
  const release = boardRelease(project, query.get("release"));
  const filters = {
    epic: query.get("epic") ?? "",
    label: query.get("label") ?? "",
    owner: query.get("owner") ?? "",
    group: query.get("group") === "1",
    hidden: query.get("hidden") === "1",
    done: query.get("done") === "all",
  };
  pageTitle("Board", project);

  const inRelease = project.items.filter((item) => item.type !== "epic" && (item.release ?? "") === release);
  const visible = inRelease.filter(
    (item) =>
      (!filters.epic || (filters.epic === "none" ? !epicOf(project, item) : item.parent === filters.epic)) &&
      (!filters.label || item.labels.includes(filters.label)) &&
      (!filters.owner || item.owner === filters.owner),
  );
  const statuses = filters.hidden ? ALL : SHOWN;
  const hiddenCounts = ["backlog", "cancelled"]
    .map((status) => [status, visible.filter((item) => statusOf(item) === status).length])
    .filter(([, count]) => count);

  const set = (changes) => {
    const next = new URLSearchParams(query);
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    const search = next.toString();
    navigate(`/board${search ? `?${search}` : ""}`, { replace: true });
  };

  return html`
    <header class="page-head board-head">
      <div class="board-title">
        <h1>Board</h1>
        <span class="muted">${releaseSummary(project, release, inRelease)}</span>
      </div>
      <button class="btn primary" type="button"
        onClick=${() => openNewItem({ release: release || "none", parent: filters.epic !== "none" ? filters.epic : undefined })}>
        <${Icon} name="plus" size=${16} /> New item
      </button>
    </header>
    <${Filters} project=${project} release=${release} inRelease=${inRelease} filters=${filters} set=${set} />
    ${error ? html`<p class="notice error" role="alert">${error}</p>` : null}
    <div class="board" role="list" aria-label="Columns">
      ${statuses.map(
        (status) => html`<${Column} key=${status} project=${project} status=${status} seen=${seen}
          items=${visible.filter((item) => statusOf(item) === status).sort(byOrder)}
          filters=${filters} set=${set} moveCard=${moveCard} saving=${moved} pulls=${pulls} />`,
      )}
    </div>
    ${asking
      ? html`<${AskDialog} item=${project.byId.get(asking.id)}
          onCancel=${() => setAsking(null)}
          onSubmit=${(message) => {
            setAsking(null);
            moveCard(asking.id, asking.status, message);
          }} />`
      : null}
    <p class="board-foot small muted">
      ${hiddenCounts.length && !filters.hidden
        ? html`<span>${hiddenCounts.map(([status, count]) => `${STATUS_LABEL[status]} (${count})`).join(" and ")} hidden</span>
            <button class="btn small-btn" type="button" onClick=${() => set({ hidden: "1" })}>Show</button>`
        : filters.hidden
          ? html`<button class="btn small-btn" type="button" onClick=${() => set({ hidden: "" })}>Hide backlog and cancelled</button>`
          : null}
      <span class="spacer"></span>
      <span class="legend"><span class="changed-dot" aria-hidden="true"></span>Changed since you last looked</span>
    </p>
  `;
}

function Filters({ project, release, inRelease, filters, set }) {
  const epics = project.items.filter((item) => item.type === "epic" && (item.release ?? "") === release);
  const labels = [...new Set(inRelease.flatMap((item) => item.labels))].sort();
  const releaseValue = release || "none";
  return html`<div class="filters" role="group" aria-label="Filters">
    <label>Release
      <select class="select" value=${releaseValue}
        onChange=${(event) => set({ release: event.currentTarget.value, epic: "", label: "" })}>
        ${project.releases.map(
          (r) => html`<option value=${r.name}>${r.name}${r.status === "active" ? " (active)" : ` (${r.status})`}</option>`,
        )}
        <option value="none">No release</option>
      </select>
    </label>
    <label>Epic
      <select class="select" value=${filters.epic} onChange=${(event) => set({ epic: event.currentTarget.value })}>
        <option value="">All epics</option>
        ${epics.map((epic) => html`<option value=${epic.id}>${epic.title}</option>`)}
        <option value="none">No epic</option>
      </select>
    </label>
    <label>Label
      <select class="select" value=${filters.label} onChange=${(event) => set({ label: event.currentTarget.value })}>
        <option value="">All labels</option>
        ${labels.map((label) => html`<option value=${label}>${label}</option>`)}
      </select>
    </label>
    <label>Owner
      <select class="select" value=${filters.owner} onChange=${(event) => set({ owner: event.currentTarget.value })}>
        <option value="">Anyone</option>
        <option value="claude">Claude</option>
        <option value="me">You</option>
      </select>
    </label>
    <label class="check">
      <input type="checkbox" checked=${filters.group} onChange=${(event) => set({ group: event.currentTarget.checked ? "1" : "" })} />
      Group by epic
    </label>
  </div>`;
}

function Column({ project, status, items, seen, filters, set, moveCard, saving, pulls }) {
  const [over, setOver] = useState(false);
  const limited = status === "done" && !filters.done && items.length > DONE_LIMIT;
  const shown = limited ? items.slice(0, DONE_LIMIT) : items;
  const groups = filters.group ? groupByEpic(project, shown) : [{ name: null, items: shown }];
  const accepts = (event) => event.dataTransfer?.types.includes(DRAG_TYPE);
  return html`<section class=${`column column-${status}${over ? " over" : ""}`} role="listitem"
    aria-labelledby=${`col-${status}`} data-status=${status}
    onDragOver=${(event) => {
      if (!accepts(event)) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      setOver(true);
    }}
    onDragLeave=${(event) => {
      if (!event.currentTarget.contains(event.relatedTarget)) setOver(false);
    }}
    onDrop=${(event) => {
      if (!accepts(event)) return;
      event.preventDefault();
      setOver(false);
      moveCard(event.dataTransfer.getData(DRAG_TYPE), status);
    }}>
    <h2 class="column-head" id=${`col-${status}`}>
      <span class="column-dot" aria-hidden="true"></span>
      <span>${STATUS_LABEL[status]}</span>
      <span class="muted">${items.length}</span>
    </h2>
    ${groups.map(
      (group) => html`
        ${group.name ? html`<span class="group-name">${group.name}</span>` : null}
        ${group.items.map(
          (item) => html`<${Card} key=${item.id} project=${project} item=${item} seen=${seen}
            grouped=${filters.group} saving=${item.id in saving} pull=${pulls?.latest[item.id]} />`,
        )}
      `,
    )}
    ${items.length === 0 ? html`<span class="column-empty">Nothing here</span>` : null}
    ${limited
      ? html`<button class="link-btn" type="button" onClick=${() => set({ done: "all" })}>Show ${items.length - DONE_LIMIT} more</button>`
      : status === "done" && filters.done && items.length > DONE_LIMIT
        ? html`<button class="link-btn" type="button" onClick=${() => set({ done: "" })}>Show fewer</button>`
        : null}
  </section>`;
}

function Card({ project, item, seen, grouped, saving, pull }) {
  const [dragging, setDragging] = useState(false);
  const epic = epicOf(project, item);
  const progress = subtaskCount(item);
  const changed = changedSince(item, seen);
  const selected = new URLSearchParams(location.search).get("item") === item.id;
  const classes = ["card-item", selected && "selected", dragging && "dragging", saving && "saving"];
  return html`<a class=${classes.filter(Boolean).join(" ")} href=${panelHref(item.id)} data-id=${item.id}
    draggable="true" aria-busy=${saving ? "true" : null}
    onDragStart=${(event) => {
      event.dataTransfer.setData(DRAG_TYPE, item.id);
      event.dataTransfer.effectAllowed = "move";
      setDragging(true);
    }}
    onDragEnd=${() => setDragging(false)}>
    <span class="card-top">
      <span class="id">${item.id}</span>
      ${item.type === "bug" ? html`<span class="chip bug">Bug</span>` : null}
      <span class="spacer"></span>
      ${changed ? html`<span class="changed-dot" role="img" aria-label="Changed since you last looked"></span>` : null}
    </span>
    <span class="card-title">${item.title}</span>
    ${epic && !grouped ? html`<span class="card-epic small muted">${epic.title}</span>` : null}
    ${item.status === "waiting" && item.waiting_message ? html`<span class="card-question">“${item.waiting_message}”</span>` : null}
    ${item.answered ? html`<span class="chip warn card-chip">Answered by you</span>` : null}
    ${item.open_blockers.length && !["done", "cancelled"].includes(item.status)
      ? html`<span class="card-blocked">Blocked by ${item.open_blockers.join(", ")}</span>`
      : null}
    <span class="card-bottom">
      <${High} item=${item} />
      ${item.labels.map((label) => html`<span class="chip label">${label}</span>`)}
      ${pull ? html`<${PrBadge} pr=${pull} />` : null}
      <span class="card-meta">
        ${progress ? html`<span class="small muted num">${progress}</span>` : null}
        <${Avatar} who=${item.owner} />
      </span>
    </span>
  </a>`;
}

// Asks what an item dropped on Waiting is waiting for, since moving to waiting needs a message.
export function AskDialog({ item, onSubmit, onCancel }) {
  const dialog = useRef(null);
  const [message, setMessage] = useState("");
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  return html`<dialog class="ask-dialog" ref=${dialog} aria-labelledby="ask-title"
    onCancel=${(event) => {
      event.preventDefault();
      onCancel();
    }}>
    <form onSubmit=${(event) => {
      event.preventDefault();
      if (message.trim()) onSubmit(message.trim());
    }}>
      <h2 id="ask-title">Move ${item.id} to Waiting</h2>
      <label for="ask-message">What is it waiting for? The question, or what to review.</label>
      <input id="ask-message" class="input tall" value=${message} autofocus
        onInput=${(event) => setMessage(event.currentTarget.value)} />
      <div class="dialog-buttons">
        <button class="btn" type="button" onClick=${onCancel}>Cancel</button>
        <button class="btn primary" type="submit" disabled=${!message.trim()}>Move to waiting</button>
      </div>
    </form>
  </dialog>`;
}

// The release the board shows: the one in the URL, else the active one, else the first.
function boardRelease(project, wanted) {
  if (wanted === "none") return "";
  if (wanted && project.releaseByName.has(wanted)) return wanted;
  return project.active_release ?? project.releases[0]?.name ?? "";
}

function releaseSummary(project, name, items) {
  const counted = items.filter((item) => item.status !== "cancelled");
  const done = counted.filter((item) => item.status === "done").length;
  if (!name) return `No release · ${done}/${counted.length} done`;
  const release = project.releaseByName.get(name);
  return `${name} · ${release.status} · ${done}/${counted.length} done`;
}

function epicOf(project, item) {
  const parent = item.parent ? project.byId.get(item.parent) : null;
  return parent?.type === "epic" ? parent : null;
}

function groupByEpic(project, items) {
  const groups = new Map();
  for (const item of items) {
    const epic = epicOf(project, item);
    const key = epic ? epic.id : "";
    if (!groups.has(key)) groups.set(key, { name: epic ? epic.title : "No epic", number: epic ? number(epic) : Infinity, items: [] });
    groups.get(key).items.push(item);
  }
  return [...groups.values()].sort((a, b) => a.number - b.number);
}

export function number(item) {
  return Number(item.id.split("-").pop()) || 0;
}

export function byOrder(a, b) {
  return (RANK[a.priority] ?? 1) - (RANK[b.priority] ?? 1) || number(a) - number(b);
}
