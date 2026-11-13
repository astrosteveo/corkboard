// The board: tasks and bugs in one release, in columns by status. Filters live in the URL, so a
// reload or a live update keeps them, and a board view can be shared as a link.
import { html } from "./lib.js";
import { navigate } from "./router.js";
import { changedSince, useSeen } from "./seen.js";
import { Avatar, High, STATUS_LABEL, itemUrl, pageTitle, subtaskCount } from "./ui.js";

const SHOWN = ["todo", "in-progress", "waiting", "done"];
const ALL = ["backlog", "todo", "in-progress", "waiting", "done", "cancelled"];
const DONE_LIMIT = 5;
const RANK = { high: 0, medium: 1, low: 2 };

export function BoardPage({ project, route }) {
  const seen = useSeen(project);
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
    .map((status) => [status, visible.filter((item) => item.status === status).length])
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
    </header>
    <${Filters} project=${project} release=${release} inRelease=${inRelease} filters=${filters} set=${set} />
    <div class="board" role="list" aria-label="Columns">
      ${statuses.map(
        (status) => html`<${Column} key=${status} project=${project} status=${status} seen=${seen}
          items=${visible.filter((item) => item.status === status).sort(byOrder)}
          filters=${filters} set=${set} />`,
      )}
    </div>
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

function Column({ project, status, items, seen, filters, set }) {
  const limited = status === "done" && !filters.done && items.length > DONE_LIMIT;
  const shown = limited ? items.slice(0, DONE_LIMIT) : items;
  const groups = filters.group ? groupByEpic(project, shown) : [{ name: null, items: shown }];
  return html`<section class=${`column column-${status}`} role="listitem" aria-labelledby=${`col-${status}`}>
    <h2 class="column-head" id=${`col-${status}`}>
      <span class="column-dot" aria-hidden="true"></span>
      <span>${STATUS_LABEL[status]}</span>
      <span class="muted">${items.length}</span>
    </h2>
    ${groups.map(
      (group) => html`
        ${group.name ? html`<span class="group-name">${group.name}</span>` : null}
        ${group.items.map(
          (item) => html`<${Card} key=${item.id} project=${project} item=${item} seen=${seen} grouped=${filters.group} />`,
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

function Card({ project, item, seen, grouped }) {
  const epic = epicOf(project, item);
  const progress = subtaskCount(item);
  const changed = changedSince(item, seen);
  return html`<a class="card-item" href=${itemUrl(item.id)} data-id=${item.id}>
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
      <span class="spacer"></span>
      ${progress ? html`<span class="small muted num">${progress}</span>` : null}
      <${Avatar} who=${item.owner} />
    </span>
  </a>`;
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
