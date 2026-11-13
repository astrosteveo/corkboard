// One item as a full page at /items/<ID>.
import { html } from "./lib.js";
import { Markdown } from "./markdown.js";
import {
  Avatar,
  High,
  Progress,
  STATUS_ICON,
  STATUS_LABEL,
  itemUrl,
  pageTitle,
  releaseUrl,
  subtaskCount,
} from "./ui.js";

export function ItemPage({ project, id }) {
  const item = project.byId.get(id);
  if (!item) {
    pageTitle(`${id} not found`, project);
    return html`<div class="page-title"><h1>${id}</h1><p>There's no item ${id} in this project.</p></div>`;
  }
  pageTitle(`${item.id} ${item.title}`, project);
  return html`<article class="item-page">
    <${ItemView} project=${project} item=${item} />
  </article>`;
}

export function ItemView({ project, item }) {
  const epic = item.parent ? project.byId.get(item.parent) : null;
  return html`<div class="item">
    <div class="crumbs small muted">
      ${epic ? html`<a href=${itemUrl(epic.id)}>${epic.title}</a><span aria-hidden="true"> › </span>` : null}
      <span class="id">${item.id}</span>
    </div>
    <h1 class="item-title">${item.title}</h1>
    <div class="item-meta">
      <span class=${`chip status-${item.status}`}>${STATUS_ICON[item.status] ?? ""} ${STATUS_LABEL[item.status] ?? item.status}</span>
      ${item.type === "bug" ? html`<span class="chip bug">Bug</span>` : null}
      ${item.type === "epic" ? html`<span class="chip">Epic</span>` : null}
      ${item.priority === "high" ? html`<${High} item=${item} />` : html`<span class="small muted">${capital(item.priority)} priority</span>`}
      <${Avatar} who=${item.owner} />
      ${item.release
        ? html`<a class="small" href=${releaseUrl(item.release)}>Release ${item.release}${item.release_from_epic ? " (from epic)" : ""}</a>`
        : html`<span class="small muted">No release</span>`}
      ${item.labels.map((label) => html`<span class="chip label">${label}</span>`)}
    </div>
    ${item.status === "waiting" && item.waiting_message
      ? html`<p class="notice waiting-note"><strong>Waiting on you:</strong> ${item.waiting_message}</p>`
      : null}
    ${item.open_blockers.length
      ? html`<p class="small muted">Blocked by ${item.open_blockers.map(
          (blocker, index) => html`${index ? ", " : ""}<a href=${itemUrl(blocker)}>${blocker}</a>`,
        )}</p>`
      : null}
    <section class="item-section">
      ${item.description
        ? html`<${Markdown} text=${item.description} />`
        : html`<p class="empty">No description.</p>`}
    </section>
    ${item.type === "epic"
      ? html`<${EpicTasks} project=${project} epic=${item} />`
      : html`<${Subtasks} item=${item} />`}
    <${Activity} item=${item} />
  </div>`;
}

function Subtasks({ item }) {
  if (!item.subtasks.length) return null;
  return html`<section class="item-section">
    <h2 class="section-label">Subtasks ${subtaskCount(item)}</h2>
    <ul class="subtasks">
      ${item.subtasks.map(
        (subtask) => html`<li class=${subtask.done ? "done" : ""}>
          <span class="tick" aria-hidden="true">${subtask.done ? "☑" : "☐"}</span>
          <span>${subtask.text}</span>
          <span class="visually-hidden">${subtask.done ? "(done)" : "(not done)"}</span>
        </li>`,
      )}
    </ul>
  </section>`;
}

function EpicTasks({ project, epic }) {
  const children = project.children.get(epic.id) ?? [];
  if (!children.length) return null;
  return html`<section class="item-section">
    <h2 class="section-label">Tasks ${epic.progress.done}/${epic.progress.total}
      <${Progress} done=${epic.progress.done} total=${epic.progress.total} small />
    </h2>
    <div class="rows">
      ${children.map(
        (child) => html`<a class="row-link" href=${itemUrl(child.id)}>
          <span class="status-icon" aria-hidden="true">${STATUS_ICON[child.status]}</span>
          <span class="id">${child.id}</span>
          <span class="title">${child.title}</span>
          <span class="small muted">${STATUS_LABEL[child.status]}</span>
        </a>`,
      )}
    </div>
  </section>`;
}

function Activity({ item }) {
  if (!item.log.length) return null;
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
  </section>`;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function shortDate(date) {
  const [, month, day] = date.split("-");
  return `${MONTHS[Number(month) - 1] ?? month} ${Number(day)}`;
}

function capital(text) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}
