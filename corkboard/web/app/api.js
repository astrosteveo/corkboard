// Talking to corkboard's local server.
import { useEffect, useState } from "./lib.js";

// GET a JSON path, and again whenever `project` changes, which it does when a file in .project/
// changes. Returns { data, error }. The last answer stays while the next one loads, so the screen
// doesn't flash, and a lost connection keeps it too; main.js already says the server is gone.
export function useJson(path, project) {
  const [state, setState] = useState({ path: null, data: null, error: null });
  useEffect(() => {
    if (!path) return undefined;
    let current = true;
    fetch(path, { cache: "no-store" })
      .then(async (response) => {
        const data = await response.json().catch(() => null);
        if (!current) return;
        if (response.ok) setState({ path, data, error: null });
        else setState({ path, data: null, error: data?.error ?? `The server answered ${response.status}.` });
      })
      .catch((problem) => {
        if (current) setState((old) => (old.path === path && old.data ? old : { path, data: null, error: problem.message }));
      });
    return () => {
      current = false;
    };
  }, [path, project]);
  return state.path === path ? state : { data: null, error: null };
}

export async function loadProject() {
  const response = await fetch("/api/project", { cache: "no-store" });
  if (!response.ok) throw new Error(`The server answered ${response.status} for /api/project.`);
  return response.json();
}

// Lookups the screens share, built once per load of the project.
export function indexProject(project) {
  const items = new Map(project.items.map((item) => [item.id, item]));
  const children = new Map();
  for (const item of project.items) {
    if (item.parent && items.get(item.parent)?.type === "epic") {
      if (!children.has(item.parent)) children.set(item.parent, []);
      children.get(item.parent).push(item);
    }
  }
  const releases = new Map(project.releases.map((release) => [release.name, release]));
  return { ...project, byId: items, children, releaseByName: releases };
}

// One change through the write API, such as write(`/api/items/EX-12/move`, { status: "done" }).
// Resolves to the server's answer, { line, warnings }, or throws an Error with its message.
export async function write(path, data) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  let answer = null;
  try {
    answer = await response.json();
  } catch {
    answer = null;
  }
  if (!response.ok) {
    const error = new Error(answer?.error ?? `The server answered ${response.status}.`);
    error.status = response.status;
    error.answer = answer;
    throw error;
  }
  return answer;
}
