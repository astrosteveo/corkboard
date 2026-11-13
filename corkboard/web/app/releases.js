// The releases view: one release and everything in it, as a tree in the same order as
// `corkboard tree`: epics by number, each one's tasks and bugs by status, then number.
// Dragging an epic, or a task with no epic, onto another release's tab moves it there, the same
// as `corkboard set <ID> release=…`. Copy release notes copies the release's done work as Markdown.
import { write } from "./api.js";
import { html, useState } from "./lib.js";
import { Markdown } from "./markdown.js";
import {
  DRAG_TYPE,
  Icon,
  Progress,
  STATUS_ICON,
  STATUS_LABEL,
  pageTitle,
  panelHref,
  releaseUrl,
} from "./ui.js";

const TREE_ORDER = ["done", "in-progress", "waiting", "todo", "backlog", "cancelled"];

export function ReleasesPage({ project, route, refresh }) {
  const [notice, setNotice] = useState(null); // { text, error }
  const name = shownRelease(project, route.release);
  const release = name ? project.releaseByName.get(name) : null;
  pageTitle(name ? `Release ${name}` : "No release", project);
  if (name === undefined) {
    return html`<div class="page-title"><h1>Releases</h1>
      <p>There's no release ${route.release}. <a href="/releases">See the releases</a>.</p></div>`;
  }
  const epics = project.items
    .filter((item) => item.type === "epic" && (item.release ?? "") === (name ?? ""))
    .sort(byNumber);
  const loose = project.items
    .filter((item) => item.type !== "epic" && !epicOf(project, item) && (item.release ?? "") === (name ?? ""))
    .sort(byTreeOrder);
  // Move an epic, or a task with no epic, to another release.
  async function moveTo(id, target) {
    const item = project.byId.get(id);
    if (!item || (item.release ?? null) === target) return;
    const epic = epicOf(project, item);
    if (epic) {
      setNotice({ error: true, text: `${id} gets its release from its epic, ${epic.id}. Drag the epic instead.` });
      return;
    }
    try {
      await write(`/api/items/${encodeURIComponent(id)}/set`, { fields: { release: target ?? "" } });
      await refresh();
      setNotice({ text: `Moved ${id} ${item.title} to ${target ?? "no release"}.`, id, target });
    } catch (problem) {
      setNotice({ error: true, text: `Couldn't move ${id}: ${problem.message}` });
    }
  }

  return html`
    <div class="page-head">
      <div class="page-title"><h1>Releases</h1></div>
      <${CopyNotes} project=${project} name=${name} epics=${epics} loose=${loose} />
    </div>
    <${Tabs} project=${project} current=${name} moveTo=${moveTo} />
    ${notice
      ? html`<p class=${notice.error ? "notice error" : "notice"} role=${notice.error ? "alert" : "status"}>
          ${notice.text}
          ${notice.id ? html` <a href=${releaseUrl(notice.target)}>Go to ${notice.target ?? "No release"}</a>` : null}
        </p>`
      : null}
    <section class="release" aria-label=${name ?? "No release"}>
      <${ReleaseHead} project=${project} release=${release} loose=${loose} refresh=${refresh} />
      ${epics.map((epic) => html`<${EpicRow} key=${epic.id} project=${project} epic=${epic} />`)}
      ${loose.length
        ? html`<div class="tree-group">
            <div class="tree-epic loose"><span class="loose-name">No epic</span></div>
            <ul class="tree-tasks">${loose.map((item) => html`<${TaskRow} key=${item.id} item=${item} draggable />`)}</ul>
          </div>`
        : null}
      ${!epics.length && !loose.length ? html`<p class="empty">Nothing here yet.</p>` : null}
    </section>
  `;
}

// The release the URL names: null for /releases/none, the active (or first) one for /releases,
// and undefined when there's no such release.
function shownRelease(project, wanted) {
  if (wanted === "none") return null;
  if (wanted) return project.releaseByName.has(wanted) ? wanted : undefined;
  return project.active_release ?? project.releases[0]?.name ?? null;
}

function Tabs({ project, current, moveTo }) {
  const tabs = [...project.releases.map((release) => ({ name: release.name, sub: release.status })), { name: null, sub: "" }];
  return html`<nav class="release-tabs" aria-label="Releases">
    ${tabs.map((tab) => html`<${Tab} key=${tab.name ?? "none"} tab=${tab} current=${current} moveTo=${moveTo} />`)}
  </nav>`;
}

// A release tab, which is also where you drop an epic to move it to that release.
function Tab({ tab, current, moveTo }) {
  const [over, setOver] = useState(false);
  const accepts = (event) => tab.name !== current && event.dataTransfer?.types.includes(DRAG_TYPE);
  return html`<a class=${over ? "release-tab over" : "release-tab"} href=${releaseUrl(tab.name)}
    data-release=${tab.name ?? "none"} aria-current=${tab.name === current ? "page" : null}
    onDragOver=${(event) => {
      if (!accepts(event)) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      setOver(true);
    }}
    onDragLeave=${() => setOver(false)}
    onDrop=${(event) => {
      if (!accepts(event)) return;
      event.preventDefault();
      setOver(false);
      moveTo(event.dataTransfer.getData(DRAG_TYPE), tab.name);
    }}>
    <span>${tab.name ?? "No release"}</span>
    ${tab.sub ? html`<span class=${`tab-sub ${tab.sub}`}>${tab.sub}</span>` : null}
  </a>`;
}

// Markdown of the release's done tasks and bugs, grouped by epic, without cancelled ones.
export function releaseNotes(project, name, epics, loose) {
  const line = (item) => `- ${item.title} (${item.id}${item.type === "bug" ? ", bug" : ""})`;
  const sections = [];
  for (const epic of epics) {
    const done = [...(project.children.get(epic.id) ?? [])].filter((item) => item.status === "done").sort(byNumber);
    if (done.length) sections.push(`### ${epic.title}\n\n${done.map(line).join("\n")}`);
  }
  const looseDone = loose.filter((item) => item.status === "done").sort(byNumber);
  if (looseDone.length) sections.push(`### ${epics.length ? "Other changes" : "Changes"}\n\n${looseDone.map(line).join("\n")}`);
  const title = `## ${name ?? "No release"}`;
  return sections.length ? `${title}\n\n${sections.join("\n\n")}\n` : `${title}\n\nNothing done yet.\n`;
}

function CopyNotes({ project, name, epics, loose }) {
  const [state, setState] = useState(""); // "", "copied", or the notes when copying failed
  async function copy() {
    const notes = releaseNotes(project, name, epics, loose);
    try {
      await navigator.clipboard.writeText(notes);
      setState("copied");
      setTimeout(() => setState(""), 2000);
    } catch {
      setState(notes);
    }
  }
  return html`<div class="copy-notes">
    <button class="btn" type="button" onClick=${copy}>
      <${Icon} name=${state === "copied" ? "check" : "copy"} size=${15} />
      ${state === "copied" ? "Copied" : "Copy release notes"}
    </button>
    ${state && state !== "copied"
      ? html`<div class="notes-fallback">
          <p class="small muted">The browser didn't allow copying. Select the notes and copy them yourself:</p>
          <textarea class="textarea" readonly value=${state} onFocus=${(event) => event.currentTarget.select()}></textarea>
          <button class="btn small-btn" type="button" onClick=${() => setState("")}>Close</button>
        </div>`
      : null}
  </div>`;
}

function ReleaseHead({ project, release, loose, refresh }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  let done;
  let total;
  if (release) ({ done, total } = release.progress);
  else {
    const counted = project.items.filter((item) => item.type !== "epic" && !item.release && item.status !== "cancelled");
    done = counted.filter((item) => item.status === "done").length;
    total = counted.length;
  }

  async function change(fields) {
    setBusy(true);
    setError("");
    try {
      await write(`/api/releases/${encodeURIComponent(release.name)}`, { fields });
      await refresh();
    } catch (problem) {
      setError(problem.message);
    } finally {
      setBusy(false);
    }
  }

  return html`<div class="card release-head">
    <div class="release-info">
      <div class="release-title">
        <h2>${release ? release.name : "No release"}</h2>
        ${release
          ? html`<label class="visually-hidden" for="release-status">Status</label>
            <select id="release-status" class=${`field-select release-status ${release.status}`} value=${release.status}
              disabled=${busy} onChange=${(event) => change({ status: event.currentTarget.value })}>
              <option value="planned">Planned</option><option value="active">Active</option><option value="released">Released</option>
            </select>
            <label class="release-date small muted">Due
              <input class="input date-input" type="date" value=${release.date ?? ""} disabled=${busy}
                onChange=${(event) => change({ date: event.currentTarget.value })} />
            </label>`
          : null}
      </div>
      ${release?.goal
        ? html`<${Markdown} className="release-goal" text=${release.goal} />`
        : release
          ? html`<p class="muted small">No goal written. It's the text of .project/releases/${release.name}.md.</p>`
          : html`<p class="muted small">Tasks and bugs that aren't in any release${loose.length ? "" : " (there are none)"}.</p>`}
      ${error ? html`<p class="notice error" role="alert">${error}</p>` : null}
    </div>
    <div class="release-progress">
      <${Progress} done=${done} total=${total} />
      <span class="num"><strong>${done}/${total}</strong> done</span>
    </div>
  </div>`;
}

function EpicRow({ project, epic }) {
  const [open, setOpen] = useState(true);
  const children = [...(project.children.get(epic.id) ?? [])].sort(byTreeOrder);
  const { done, total } = epic.progress;
  return html`<div class="tree-group" data-epic=${epic.id}>
    <div class="tree-epic" draggable="true" title="Drag onto another release's tab to move this epic there"
      onDragStart=${(event) => {
        event.dataTransfer.setData(DRAG_TYPE, epic.id);
        event.dataTransfer.effectAllowed = "move";
      }}>
      <button class="icon-btn toggle" type="button" aria-expanded=${open}
        aria-label=${`${open ? "Collapse" : "Expand"} ${epic.id}`} onClick=${() => setOpen(!open)}>
        <span class=${open ? "chevron open" : "chevron"}><${Icon} name="chevron" size=${16} /></span>
      </button>
      <span class="id">${epic.id}</span>
      <a class="tree-title" href=${panelHref(epic.id)}>${epic.title}</a>
      <span class="chip">Epic</span>
      <span class=${`tree-status status-${epic.status}`}>${STATUS_LABEL[epic.status]}</span>
      <${Progress} done=${done} total=${total} small />
      <span class="small muted num">${done}/${total}</span>
    </div>
    ${open
      ? children.length
        ? html`<ul class="tree-tasks">${children.map((item) => html`<${TaskRow} key=${item.id} item=${item} />`)}</ul>`
        : html`<p class="empty tree-empty">No tasks yet.</p>`
      : null}
  </div>`;
}

function TaskRow({ item, draggable = false }) {
  const [open, setOpen] = useState(false);
  const subtasks = item.subtasks;
  const done = subtasks.filter((subtask) => subtask.done).length;
  return html`<li class="tree-task" data-id=${item.id} data-status=${item.status}
    draggable=${draggable ? "true" : null}
    onDragStart=${draggable
      ? (event) => {
          event.dataTransfer.setData(DRAG_TYPE, item.id);
          event.dataTransfer.effectAllowed = "move";
        }
      : null}>
    <div class="tree-row">
      <span class=${`tree-icon status-${item.status}`} aria-hidden="true">${STATUS_ICON[item.status]}</span>
      <span class="id">${item.id}</span>
      <a class=${`tree-title${item.status === "cancelled" ? " cancelled" : ""}`} href=${panelHref(item.id)}>${item.title}</a>
      ${item.type === "bug" ? html`<span class="chip bug">Bug</span>` : null}
      ${item.open_blockers.length && !["done", "cancelled"].includes(item.status)
        ? html`<span class="small blocked-text">blocked</span>`
        : null}
      ${item.owner === "me" ? html`<span class="avatar me">You</span>` : null}
      <span class=${`tree-status status-${item.status}`}>${STATUS_LABEL[item.status]}</span>
      ${subtasks.length
        ? html`<button class="sub-toggle" type="button" aria-expanded=${open}
            aria-label=${`${open ? "Hide" : "Show"} the subtasks of ${item.id}`} onClick=${() => setOpen(!open)}>
            <span class="num">${done}/${subtasks.length}</span>
            <span class=${open ? "chevron open" : "chevron"}><${Icon} name="chevron" size=${14} /></span>
          </button>`
        : html`<span class="sub-toggle placeholder"></span>`}
    </div>
    ${open
      ? html`<ul class="tree-subtasks">
          ${subtasks.map(
            (subtask) => html`<li class=${subtask.done ? "done" : ""}>
              <span aria-hidden="true">${subtask.done ? "☑" : "☐"}</span>
              <span>${subtask.text}</span>
            </li>`,
          )}
        </ul>`
      : null}
  </li>`;
}

function epicOf(project, item) {
  const parent = item.parent ? project.byId.get(item.parent) : null;
  return parent?.type === "epic" ? parent : null;
}

function number(item) {
  return Number(item.id.split("-").pop()) || 0;
}

function byNumber(a, b) {
  return number(a) - number(b);
}

function byTreeOrder(a, b) {
  const rank = (item) => (TREE_ORDER.includes(item.status) ? TREE_ORDER.indexOf(item.status) : TREE_ORDER.length);
  return rank(a) - rank(b) || number(a) - number(b);
}
