// Talking to corkboard's local server.

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
