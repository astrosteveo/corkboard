// Every screen has its own URL: /, /board, /releases/<name>, /items/<ID>, /docs/<name>.
// Links inside the app change the URL with the History API instead of loading a new page.
import { useEffect, useState } from "./lib.js";

const CHANGE = "corkboard:navigate";

export function navigate(url, { replace = false } = {}) {
  if (replace) history.replaceState(null, "", url);
  else history.pushState(null, "", url);
  dispatchEvent(new Event(CHANGE));
}

export function parseRoute(pathname, search) {
  const query = new URLSearchParams(search);
  const parts = pathname.split("/").filter(Boolean).map(decodeURIComponent);
  let route;
  if (parts.length === 0) route = { name: "now" };
  else if (parts[0] === "board" && parts.length === 1) route = { name: "board" };
  else if (parts[0] === "releases" && parts.length <= 2) route = { name: "releases", release: parts[1] ?? null };
  else if (parts[0] === "items" && parts.length === 2) route = { name: "item", id: parts[1].toUpperCase() };
  // A doc's name is its path under docs/, and a link to ui.md from another page works too.
  else if (parts[0] === "docs") route = { name: "docs", doc: parts.slice(1).join("/").replace(/\.md$/, "") || null };
  else route = { name: "notfound" };
  return { ...route, path: pathname, query };
}

export function useRoute() {
  const [where, setWhere] = useState(location.pathname + location.search);
  useEffect(() => {
    const update = () => setWhere(location.pathname + location.search);
    addEventListener("popstate", update);
    addEventListener(CHANGE, update);
    return () => {
      removeEventListener("popstate", update);
      removeEventListener(CHANGE, update);
    };
  }, []);
  const url = new URL(where, location.origin);
  return parseRoute(url.pathname, url.search);
}

// A plain left click on a link to another page of the app stays in the app.
document.addEventListener("click", (event) => {
  if (event.defaultPrevented || event.button !== 0) return;
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  const link = event.target.closest("a[href]");
  if (!link || link.target || link.hasAttribute("download")) return;
  const url = new URL(link.href, location.href);
  if (url.origin !== location.origin || url.pathname.startsWith("/api/")) return;
  event.preventDefault();
  if (url.pathname + url.search !== location.pathname + location.search) {
    navigate(url.pathname + url.search + url.hash);
    scrollTo(0, 0);
  }
});
