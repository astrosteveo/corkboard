// The app: loads the project from the server, and shows the sidebar and the screen for the URL.
import { indexProject, loadProject } from "./api.js";
import { BoardPage } from "./board.js";
import { DocsPage } from "./docs.js";
import { ItemPage, ItemPanel } from "./item.js";
import { html, render, useCallback, useEffect, useState } from "./lib.js";
import { NewItem, openNewItem } from "./newitem.js";
import { NowPage } from "./now.js";
import { ReleasesPage } from "./releases.js";
import { useRoute } from "./router.js";
import { Icon } from "./ui.js";

function App() {
  const route = useRoute();
  const [project, setProject] = useState(null);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    try {
      setProject(indexProject(await loadProject()));
      setError(null);
    } catch (problem) {
      setError(problem.message);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Live updates: the server sends "change" when a file in .project/ changes, such as when Claude
  // runs corkboard. Reconnecting loads the project again too, in case a change was missed.
  const [live, setLive] = useState(false);
  useEffect(() => {
    const events = new EventSource("/api/events");
    events.addEventListener("change", refresh);
    events.addEventListener("open", () => {
      setLive(true);
      refresh();
    });
    events.addEventListener("error", () => setLive(false));
    return () => events.close();
  }, [refresh]);

  const pulls = usePulls(project);

  let body;
  if (!project) {
    body = error
      ? html`<p class="notice error">Couldn't load the project. ${error}</p>`
      : html`<p class="muted">Loading…</p>`;
  } else {
    body = html`<${Screen} route=${route} project=${project} refresh=${refresh} pulls=${pulls} />`;
  }

  return html`<div class="shell">
    <${Sidebar} project=${project} route=${route} live=${live} />
    <main class=${route.name === "board" ? "main wide" : "main"} id="main">
      ${error && project ? html`<p class="notice error">Lost touch with the server. ${error}</p>` : null}
      ${body}
    </main>
    ${project && route.name !== "item" && route.query.get("item")
      ? html`<${ItemPanel} project=${project} id=${route.query.get("item").toUpperCase()} refresh=${refresh} />`
      : null}
    <${NewItem} project=${project} refresh=${refresh} />
  </div>`;
}

// Each item's newest own pull request and the items whose one merged while they're open, from
// /api/pulls. The server reads them from GitHub at most once a minute, so this asks again when the
// project changes, and once a minute while the page is open, since a merge changes no file here.
function usePulls(project) {
  const [pulls, setPulls] = useState(null);
  useEffect(() => {
    if (!project) return undefined;
    let current = true;
    const load = () =>
      fetch("/api/pulls", { cache: "no-store" })
        .then((response) => (response.ok ? response.json() : null))
        .then((data) => current && data && setPulls(data))
        .catch(() => {});
    load();
    const timer = setInterval(load, 60_000);
    return () => {
      current = false;
      clearInterval(timer);
    };
  }, [project]);
  return pulls;
}

function Screen({ route, project, refresh, pulls }) {
  const props = { project, refresh, route, pulls };
  switch (route.name) {
    case "now":
      return html`<${NowPage} ...${props} />`;
    case "board":
      return html`<${BoardPage} ...${props} />`;
    case "releases":
      return html`<${ReleasesPage} ...${props} />`;
    case "item":
      return html`<${ItemPage} ...${props} id=${route.id} />`;
    case "docs":
      return html`<${DocsPage} ...${props} />`;
    default:
      document.title = "Not found · Corkboard";
      return html`<div class="page-title"><h1>Not found</h1>
        <p>There's no page at ${route.path}. <a href="/">Go to Now</a>.</p></div>`;
  }
}

const NAV = [
  { name: "now", href: "/", label: "Now", icon: "now" },
  { name: "board", href: "/board", label: "Board", icon: "board" },
  { name: "releases", href: "/releases", label: "Releases", icon: "releases" },
  { name: "docs", href: "/docs", label: "Docs", icon: "docs" },
];

function Sidebar({ project, route, live }) {
  const waiting = project ? project.items.filter((item) => item.status === "waiting").length : 0;
  return html`<nav class="sidebar" aria-label="Main">
    <div class="brand">
      <span class="brand-mark" aria-hidden="true">${project?.prefix?.slice(0, 3) || "CB"}</span>
      <span class="brand-text">
        <span class="brand-name">${project?.name ?? "Corkboard"}</span>
        <span class="brand-host">${location.host}</span>
      </span>
    </div>
    <div class="nav">
      ${NAV.map(
        (entry) => html`<a href=${entry.href} aria-current=${route.name === entry.name ? "page" : null}>
          <${Icon} name=${entry.icon} />
          <span class="label">${entry.label}</span>
          ${entry.name === "now" && waiting
            ? html`<span class="badge" aria-label=${`${waiting} waiting on you`}>${waiting}</span>`
            : null}
        </a>`,
      )}
    </div>
    <button class="new-btn" type="button" onClick=${() => openNewItem()} disabled=${!project}>
      <${Icon} name="plus" size=${16} /> <span class="label">New item</span> <kbd>C</kbd>
    </button>
    <div class="sidebar-foot" role="status">
      ${live
        ? html`<span class="live"><span class="dot" aria-hidden="true"></span>Live</span>
            <span>Watching .project/ for changes</span>`
        : html`<span class="live off"><span class="dot" aria-hidden="true"></span>Reconnecting…</span>
            <span>Changes show up when the server is back</span>`}
    </div>
  </nav>`;
}

render(html`<${App} />`, document.getElementById("app"));
