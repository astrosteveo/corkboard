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
