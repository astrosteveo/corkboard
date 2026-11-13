// The releases view: one release and everything in it, as a tree in the same order as
// `corkboard tree`: epics by number, each one's tasks and bugs by status, then number.
import { write } from "./api.js";
import { html, useState } from "./lib.js";
import { Markdown } from "./markdown.js";
import { Icon, Progress, STATUS_ICON, STATUS_LABEL, pageTitle, panelHref, releaseUrl } from "./ui.js";

const TREE_ORDER = ["done", "in-progress", "waiting", "todo", "backlog", "cancelled"];

export function ReleasesPage({ project, route, refresh }) {
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
  return html`
    <div class="page-title"><h1>Releases</h1></div>
    <${Tabs} project=${project} current=${name} />
    <section class="release" aria-label=${name ?? "No release"}>
      <${ReleaseHead} project=${project} release=${release} loose=${loose} refresh=${refresh} />
      ${epics.map((epic) => html`<${EpicRow} key=${epic.id} project=${project} epic=${epic} />`)}
      ${loose.length
        ? html`<div class="tree-group">
            <div class="tree-epic loose"><span class="loose-name">No epic</span></div>
            <ul class="tree-tasks">${loose.map((item) => html`<${TaskRow} key=${item.id} item=${item} />`)}</ul>
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

function Tabs({ project, current }) {
  const tabs = [...project.releases.map((release) => ({ name: release.name, sub: release.status })), { name: null, sub: "" }];
  return html`<nav class="release-tabs" aria-label="Releases">
    ${tabs.map(
      (tab) => html`<a class="release-tab" href=${releaseUrl(tab.name)} data-release=${tab.name ?? "none"}
        aria-current=${tab.name === current ? "page" : null}>
        <span>${tab.name ?? "No release"}</span>
        ${tab.sub ? html`<span class=${`tab-sub ${tab.sub}`}>${tab.sub}</span>` : null}
      </a>`,
    )}
  </nav>`;
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
    <div class="tree-epic">
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

function TaskRow({ item }) {
  const [open, setOpen] = useState(false);
  const subtasks = item.subtasks;
  const done = subtasks.filter((subtask) => subtask.done).length;
  return html`<li class="tree-task" data-id=${item.id} data-status=${item.status}>
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
