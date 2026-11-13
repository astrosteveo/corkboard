// "Since you last looked": the time of your last Mark seen, kept in this browser per repo.
// Log lines Claude wrote after it count as unseen, on the Now page and as dots on the board.
import { useEffect, useState } from "./lib.js";

const CHANGE = "corkboard:seen";

function key(project) {
  return `corkboard.seen:${project.root}`;
}

// The last Mark seen as "YYYY-MM-DD HH:MM", the same form as log lines, or "" if never.
export function getSeen(project) {
  try {
    return localStorage.getItem(key(project)) ?? "";
  } catch {
    return "";
  }
}

export function markSeen(project, when = nowStamp()) {
  try {
    localStorage.setItem(key(project), when);
  } catch {
    // Private windows can refuse storage; the list then stays until the page reloads.
  }
  dispatchEvent(new Event(CHANGE));
}

export function useSeen(project) {
  const [seen, setSeen] = useState(() => getSeen(project));
  useEffect(() => {
    const update = () => setSeen(getSeen(project));
    update();
    addEventListener(CHANGE, update);
    addEventListener("storage", update); // Mark seen in another tab
    return () => {
      removeEventListener(CHANGE, update);
      removeEventListener("storage", update);
    };
  }, [project.root]);
  return seen;
}

export function stamp(entry) {
  return `${entry.date} ${entry.time}`;
}

export function nowStamp() {
  const now = new Date();
  const two = (n) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${two(now.getMonth() + 1)}-${two(now.getDate())} ${two(now.getHours())}:${two(now.getMinutes())}`;
}

// Log lines Claude wrote after `seen`, oldest first, each with its item.
export function unseenEntries(project, seen) {
  const entries = [];
  for (const item of project.items) {
    for (const entry of item.log) {
      if (entry.who === "claude" && stamp(entry) > seen) entries.push({ item, entry });
    }
  }
  return entries.sort((a, b) => stamp(a.entry).localeCompare(stamp(b.entry)));
}

// Whether Claude changed the item since `seen`: the dot (●) on board cards.
export function changedSince(item, seen) {
  return item.log.some((entry) => entry.who === "claude" && stamp(entry) > seen);
}
