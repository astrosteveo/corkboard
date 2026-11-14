// The list: every item in a table, filtered the way `corkboard list` filters, for sorting through
// the backlog. Filters and the sort order live in the URL, so a reload or a live update keeps them.
// Status and priority change in the row, the same as `corkboard move` and `corkboard set`.
import { write } from "./api.js";
import { AskDialog, number } from "./board.js";
import { html, useState } from "./lib.js";
import { openNewItem } from "./newitem.js";
import { navigate } from "./router.js";
import { changedSince, useSeen } from "./seen.js";
import { Icon, STATUS_ICON, STATUS_LABEL, pageTitle, panelHref } from "./ui.js";

const STATUSES = ["backlog", "todo", "in-progress", "waiting", "done", "cancelled"];
const DEFAULT_STATUSES = ["backlog", "todo"];
const TYPES = ["epic", "task", "bug"];
const RANK = { high: 0, medium: 1, low: 2 };

// What each column sorts by. null sorts last either way, such as an item with no epic.
const COLUMNS = [
  { key: "id", label: "ID", value: (item) => number(item) },
  { key: "type", label: "Type", value: (item) => TYPES.indexOf(item.type) },
  { key: "status", label: "Status", value: (item) => STATUSES.indexOf(item.status) },
  { key: "priority", label: "Priority", value: (item) => RANK[item.priority] ?? 1 },
  { key: "title", label: "Title", value: (item) => item.title.toLowerCase() },
  { key: "epic", label: "Epic", value: (item, project) => epicOf(project, item)?.title.toLowerCase() ?? null },
  { key: "labels", label: "Labels", value: (item) => (item.labels.length ? item.labels.join(", ") : null) },
];

export function ListPage({ project, route, refresh }) {
  const seen = useSeen(project);
  const [saving, setSaving] = useState({}); // id → { status or priority }, while a change saves
  const [asking, setAsking] = useState(null); // the item whose status is being set to waiting
  const [error, setError] = useState("");
  const [note, setNote] = useState("");
  pageTitle("List", project);

  const query = route.query;
  const filters = readFilters(query);
  const matches = (item) =>
    (!filters.type || item.type === filters.type) &&
    (!filters.label || item.labels.includes(filters.label)) &&
    (!filters.release || (item.release ?? "none") === filters.release);
  const others = project.items.filter(matches);
  const items = others.filter((item) => filters.statuses.includes(item.status)).sort(sorter(project, filters.sort));

  const set = (changes) => {
    const next = new URLSearchParams(query);
    for (const [key, value] of Object.entries(changes)) {
      if (value === null) next.delete(key);
      else next.set(key, value);
    }
    const search = next.toString();
    navigate(`/list${search ? `?${search}` : ""}`, { replace: true });
  };
  const setStatuses = (statuses) => {
    const chosen = STATUSES.filter((status) => statuses.includes(status));
    set({ status: chosen.join(",") === DEFAULT_STATUSES.join(",") ? null : chosen.join(",") });
  };

  async function change(item, action, data, preview) {
    setError("");
    setNote("");
    setSaving((current) => ({ ...current, [item.id]: preview }));
    try {
      const answer = await write(`/api/items/${encodeURIComponent(item.id)}/${action}`, data);
      await refresh();
      const notes = [...(answer.warnings ?? [])];
      if (preview.status && !filters.statuses.includes(preview.status)) {
        notes.unshift(`${item.id} is ${STATUS_LABEL[preview.status]} now, so the status filter hides it.`);
      }
      setNote(notes.join(" "));
    } catch (problem) {
      setError(`Couldn't change ${item.id}: ${problem.message}`);
    } finally {
      setSaving((current) => {
        const rest = { ...current };
        delete rest[item.id];
        return rest;
      });
    }
  }
  const move = (item, status, message = "") => change(item, "move", { status, message }, { status });

  return html`
    <header class="page-head">
      <div class="board-title">
        <h1>List</h1>
        <span class="muted">${items.length === 1 ? "1 item" : `${items.length} items`}</span>
      </div>
      <button class="btn primary" type="button"
        onClick=${() => openNewItem({ release: filters.release || undefined })}>
        <${Icon} name="plus" size=${16} /> New item
      </button>
    </header>
    <${Filters} project=${project} filters=${filters} others=${others} set=${set} setStatuses=${setStatuses} />
    ${error ? html`<p class="notice error" role="alert">${error}</p>` : null}
    ${note ? html`<p class="notice" role="status">${note}</p>` : null}
    ${items.length
      ? html`<div class="list-wrap">
          <table class="list-table">
            <thead>
              <tr>
                ${COLUMNS.map((column) => html`<${Heading} key=${column.key} column=${column} sort=${filters.sort} set=${set} />`)}
              </tr>
            </thead>
            <tbody>
              ${items.map(
                (item) => html`<${Row} key=${item.id} project=${project} item=${item} seen=${seen}
                  selected=${query.get("item") === item.id} saving=${saving[item.id]}
                  onStatus=${(status) => (status === "waiting" ? setAsking(item) : move(item, status))}
                  onPriority=${(priority) => change(item, "set", { fields: { priority } }, { priority })} />`,
              )}
            </tbody>
          </table>
        </div>`
      : html`<p class="empty">${filters.statuses.length ? "No items match these filters." : "Pick a status to see items."}</p>`}
    ${asking
      ? html`<${AskDialog} item=${asking}
          onCancel=${() => setAsking(null)}
          onSubmit=${(message) => {
            setAsking(null);
            move(asking, "waiting", message);
          }} />`
      : null}
  `;
}

// The filters from the URL. No status= means backlog and todo, the way the backlog starts out.
function readFilters(query) {
  const status = query.get("status");
  return {
    statuses: status === null ? DEFAULT_STATUSES : status.split(",").filter((s) => STATUSES.includes(s)),
    type: TYPES.includes(query.get("type")) ? query.get("type") : "",
    label: query.get("label") ?? "",
    release: query.get("release") ?? "",
    sort: query.get("sort") ?? "id",
  };
}

function Filters({ project, filters, others, set, setStatuses }) {
  const labels = [...new Set(project.items.flatMap((item) => item.labels))].sort();
  return html`<div class="filters" role="group" aria-label="Filters">
    <div class="status-filter" role="group" aria-labelledby="status-filter-name">
      <span class="filter-name" id="status-filter-name">Status</span>
      ${STATUSES.map((status) => {
        const on = filters.statuses.includes(status);
        const count = others.filter((item) => item.status === status).length;
        return html`<button type="button" class="status-toggle" aria-pressed=${on ? "true" : "false"}
          onClick=${() => setStatuses(on ? filters.statuses.filter((s) => s !== status) : [...filters.statuses, status])}>
          ${STATUS_LABEL[status]} <span class="num">${count}</span>
        </button>`;
      })}
    </div>
    <label>Type
      <select class="select" value=${filters.type} onChange=${(event) => set({ type: event.currentTarget.value || null })}>
        <option value="">All types</option>
        <option value="epic">Epic</option>
        <option value="task">Task</option>
        <option value="bug">Bug</option>
      </select>
    </label>
    <label>Label
      <select class="select" value=${filters.label} onChange=${(event) => set({ label: event.currentTarget.value || null })}>
        <option value="">All labels</option>
        ${labels.map((label) => html`<option value=${label}>${label}</option>`)}
      </select>
    </label>
    <label>Release
      <select class="select" value=${filters.release} onChange=${(event) => set({ release: event.currentTarget.value || null })}>
        <option value="">All releases</option>
        ${project.releases.map((release) => html`<option value=${release.name}>${release.name} (${release.status})</option>`)}
        <option value="none">No release</option>
      </select>
    </label>
  </div>`;
}

// A column header that sorts by its column, and the other way round when clicked again.
function Heading({ column, sort, set }) {
  const desc = sort.startsWith("-");
  const current = (desc ? sort.slice(1) : sort) === column.key;
  const next = current && !desc ? `-${column.key}` : column.key;
  return html`<th scope="col" aria-sort=${current ? (desc ? "descending" : "ascending") : null}>
    <button class="sort-btn" type="button" onClick=${() => set({ sort: next === "id" ? null : next })}>
      ${column.label}
      <span class="sort-arrow" aria-hidden="true">${current ? (desc ? "↓" : "↑") : ""}</span>
    </button>
  </th>`;
}

function Row({ project, item, seen, selected, saving, onStatus, onPriority }) {
  const epic = epicOf(project, item);
  const status = saving?.status ?? item.status;
  const priority = saving?.priority ?? item.priority;
  const label = `${item.id} ${item.title}`;
  return html`<tr class=${selected ? "selected" : null} aria-busy=${saving ? "true" : null}
    onClick=${(event) => {
      if (!event.target.closest("a, select, button")) navigate(panelHref(item.id));
    }}>
    <td class="id-cell">
      <span class="id">${item.id}</span>
      ${changedSince(item, seen) ? html`<span class="changed-dot" role="img" aria-label="Changed since you last looked"></span>` : null}
    </td>
    <td>${item.type === "bug" ? html`<span class="chip bug">bug</span>` : html`<span class="muted">${item.type}</span>`}</td>
    <td>
      <select class=${`field-select status-${status}`} value=${status} disabled=${!!saving} aria-label=${`Status of ${label}`}
        onChange=${(event) => {
          const chosen = event.currentTarget.value;
          event.currentTarget.value = item.status;
          onStatus(chosen);
        }}>
        ${STATUSES.map((s) => html`<option value=${s}>${STATUS_ICON[s]} ${STATUS_LABEL[s]}</option>`)}
      </select>
    </td>
    <td>
      <select class=${`field-select priority-${priority}`} value=${priority} disabled=${!!saving} aria-label=${`Priority of ${label}`}
        onChange=${(event) => onPriority(event.currentTarget.value)}>
        <option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
      </select>
    </td>
    <td class="title-cell">
      <a href=${panelHref(item.id)}>${item.title}</a>
      ${item.open_blockers.length && !["done", "cancelled"].includes(item.status)
        ? html` <span class="small blocked-note">blocked</span>`
        : null}
    </td>
    <td class="epic-cell">${epic ? epic.title : html`<span class="muted">—</span>`}</td>
    <td class="labels-cell">${item.labels.map((l) => html`<span class="chip label">${l}</span>`)}</td>
  </tr>`;
}

// Sorts by the column in `sort`, such as "priority" or "-priority" for the other way round, and
// then by number, the way `corkboard list` sorts.
function sorter(project, sort) {
  const desc = sort.startsWith("-");
  const column = COLUMNS.find((c) => c.key === (desc ? sort.slice(1) : sort)) ?? COLUMNS[0];
  return (a, b) => {
    const x = column.value(a, project);
    const y = column.value(b, project);
    if (x === null || y === null) return (x === null) - (y === null) || number(a) - number(b);
    const order = typeof x === "number" ? x - y : x.localeCompare(y);
    return (desc ? -order : order) || number(a) - number(b);
  };
}

function epicOf(project, item) {
  const parent = item.parent ? project.byId.get(item.parent) : null;
  return parent?.type === "epic" ? parent : null;
}
