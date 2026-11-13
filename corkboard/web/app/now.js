// The Now page: where things stand, what Claude needs from you, and what changed since you looked.
// In progress and Next up match `corkboard now`, using the order of work the server sends.
import { write } from "./api.js";
import { shortDate } from "./item.js";
import { html, useState } from "./lib.js";
import { markSeen, nowStamp, unseenEntries, useSeen } from "./seen.js";
import { Avatar, High, Icon, Progress, itemUrl, pageTitle, releaseUrl, subtaskCount } from "./ui.js";

const NEXT_UP = 3;
const SINCE_LINES = 30;

export function NowPage({ project, refresh }) {
  const waiting = project.items.filter((item) => item.status === "waiting");
  pageTitle(waiting.length ? `(${waiting.length}) Now` : "Now", project);
  return html`
    <header class="page-head">
      <div class="page-title">
        <h1>Now</h1>
        <p>Where things stand, what Claude needs from you, and what changed.</p>
      </div>
      <${ReleaseLine} project=${project} />
    </header>
    ${project.problems.length
      ? html`<p class="notice error">
          ${project.problems.length} ${project.problems.length === 1 ? "file" : "files"} in .project/
          couldn't be read. Run <code>corkboard check</code>.
        </p>`
      : null}
    <${Waiting} project=${project} items=${waiting} refresh=${refresh} />
    <div class="columns">
      <${InProgress} project=${project} />
      <${NextUp} project=${project} />
    </div>
    <${Since} project=${project} />
  `;
}

function ReleaseLine({ project }) {
  const release = project.releaseByName.get(project.active_release);
  if (!release) {
    return html`<a class="release-line" href="/releases"><span class="muted">No active release</span></a>`;
  }
  const { done, total } = release.progress;
  return html`<a class="release-line" href=${releaseUrl(release.name)}>
    <span class="release-name">
      <strong>${release.name} · active</strong>
      ${release.date ? html`<span class="small muted">Due ${shortDate(release.date)}</span>` : null}
    </span>
    <${Progress} done=${done} total=${total} />
    <span class="num"><strong>${done}/${total}</strong> done</span>
  </a>`;
}

function Waiting({ project, items, refresh }) {
  const [notice, setNotice] = useState("");
  return html`<section class="waiting" aria-labelledby="waiting-h">
    <h2 id="waiting-h" class="section-label">Waiting on you · ${items.length}</h2>
    ${notice ? html`<p class="outcome" role="status"><${Icon} name="check" size=${16} stroke=${2.5} /> ${notice}</p>` : null}
    ${items.length
      ? items.map(
          (item) => html`<${WaitingCard} key=${item.id} project=${project} item=${item}
            refresh=${refresh} setNotice=${setNotice} />`,
        )
      : notice
        ? null
        : html`<p class="empty">Nothing is waiting on you. Claude asks here when it needs an answer or a review.</p>`}
  </section>`;
}

function WaitingCard({ item, refresh, setNotice }) {
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const asked = lastWaitingEntry(item);
  const text = reply.trim();

  async function send(status) {
    setBusy(true);
    setError("");
    try {
      await write(`/api/items/${item.id}/move`, { status, message: text });
      setNotice(
        status === "todo"
          ? `Sent. ${item.id} is back in todo with your reply, first in Claude's Next up.`
          : `${item.id} marked done.`,
      );
      await refresh();
    } catch (problem) {
      setError(problem.message);
      setBusy(false);
    }
  }

  const inputId = `reply-${item.id}`;
  return html`<article class="waiting-card">
    <div class="waiting-head">
      <a class="id" href=${itemUrl(item.id)}>${item.id}</a>
      <a class="waiting-title" href=${itemUrl(item.id)}>${item.title}</a>
      ${item.type === "bug" ? html`<span class="chip bug">Bug</span>` : null}
      <${High} item=${item} />
    </div>
    <div class="question">
      <${Avatar} who=${asked?.who === "me" ? "me" : "claude"} />
      <div class="question-text">
        <span class="small muted">
          ${asked?.who === "me" ? "You" : "Claude"} asked${asked ? ` ${whenLabel(asked)}` : ""}
        </span>
        <span>${item.waiting_message || "(no message)"}</span>
      </div>
    </div>
    <form class="reply" onSubmit=${(event) => {
      event.preventDefault();
      if (text && !busy) send("todo");
    }}>
      <label class="visually-hidden" for=${inputId}>Reply to ${item.id}</label>
      <input id=${inputId} class="input tall" type="text" placeholder="Reply to Claude…" value=${reply}
        onInput=${(event) => setReply(event.currentTarget.value)} disabled=${busy} />
      <button class="btn primary tall" type="submit" disabled=${busy || !text}>Send</button>
      <button class="btn tall" type="button" disabled=${busy} onClick=${() => send("done")}
        title=${text ? "Move it to done, with your reply as the message" : "Move it to done"}>Mark done</button>
    </form>
    ${error ? html`<p class="notice error" role="alert">${error}</p>` : null}
  </article>`;
}

function InProgress({ project }) {
  const items = project.items.filter((item) => item.type !== "epic" && item.status === "in-progress");
  return html`<section class="card list-card" aria-labelledby="progress-h">
    <h2 id="progress-h" class="section-label">In progress · ${items.length}</h2>
    ${items.length
      ? items.map(
          (item) => html`<a class="row-link" href=${itemUrl(item.id)}>
            <span class="id">${item.id}</span>
            <span class="title">${item.title}</span>
            <${High} item=${item} />
            ${subtaskCount(item) ? html`<span class="small muted num">${subtaskCount(item)}</span>` : null}
            <${Avatar} who=${item.owner} />
          </a>`,
        )
      : html`<p class="empty">Nothing in progress.</p>`}
  </section>`;
}

function NextUp({ project }) {
  const items = project.next.slice(0, NEXT_UP).map((id) => project.byId.get(id));
  return html`<section class="card list-card" aria-labelledby="next-h">
    <h2 id="next-h" class="section-label">Next up for Claude</h2>
    ${items.length
      ? items.map(
          (item) => html`<a class="row-link" href=${itemUrl(item.id)}>
            <span class="id">${item.id}</span>
            <span class="title">${item.title}</span>
            ${item.answered ? html`<span class="chip warn">Answered by you</span>` : html`<${High} item=${item} />`}
          </a>`,
        )
      : html`<p class="empty">Nothing to do: no unblocked todo items owned by Claude.</p>`}
    ${project.next.length > NEXT_UP
      ? html`<p class="small muted more">…and ${project.next.length - NEXT_UP} more after these.</p>`
      : null}
  </section>`;
}

function Since({ project }) {
  const seen = useSeen(project);
  const entries = unseenEntries(project, seen);
  const shown = entries.slice(-SINCE_LINES);
  const seenDay = seen.slice(0, 10) === today() ? "today" : shortDate(seen.slice(0, 10));
  const label = seen ? `Since ${seenDay} at ${seen.slice(11)}` : "Everything Claude has logged";
  return html`<section class="card since" aria-labelledby="since-h">
    <div class="since-head">
      <div>
        <h2 id="since-h" class="section-label">Since you last looked</h2>
        <span class="small muted">${label}${entries.length ? ` · ${entries.length} ${entries.length === 1 ? "change" : "changes"}` : ""}</span>
      </div>
      ${entries.length
        ? html`<button class="btn" type="button" onClick=${() => markSeen(project, latest(entries))}>Mark seen</button>`
        : null}
    </div>
    ${entries.length
      ? html`<ol class="since-list">
          ${entries.length > shown.length
            ? html`<li class="small muted">…${entries.length - shown.length} earlier changes</li>`
            : null}
          ${shown.map(
            ({ item, entry }) => html`<li>
              <span class="when mono small muted">${whenShort(entry)}</span>
              <${Avatar} who="claude" />
              <a class="id" href=${itemUrl(item.id)}>${item.id}</a>
              <span class="what">${capital(entry.text)} <span class="muted small">· ${item.title}</span></span>
            </li>`,
          )}
        </ol>`
      : html`<p class="empty">You're caught up. New changes from Claude will show up here.</p>`}
  </section>`;
}

function lastWaitingEntry(item) {
  for (let i = item.log.length - 1; i >= 0; i--) {
    if (item.log[i].text.startsWith("moved to waiting")) return item.log[i];
  }
  return null;
}

// The newest stamp among the entries, or now if that's later: Mark seen covers what's listed.
function latest(entries) {
  const newest = entries.reduce((max, { entry }) => {
    const value = `${entry.date} ${entry.time}`;
    return value > max ? value : max;
  }, "");
  const now = nowStamp();
  return now > newest ? now : newest;
}

function today() {
  return nowStamp().slice(0, 10);
}

function whenLabel(entry) {
  if (entry.date === today()) return `at ${entry.time}`;
  return `${shortDate(entry.date)} at ${entry.time}`;
}

function whenShort(entry) {
  return entry.date === today() ? entry.time : `${shortDate(entry.date)} ${entry.time}`;
}

function capital(text) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}
