"""The work behind an item: its branch, its pull requests and the commits that mention its ID.

Nothing here is stored in item files; it's read each time. Branches and commits come from git, so
they work offline. Commits come from HEAD and the local branches. Remote branches are left out,
since squash-merged pull requests leave their branches on the remote and those commits would
show up a second time. Pull requests come from GitHub through `gh`, and are simply missing when
`gh`, a GitHub remote or a connection is.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .project import mention_pattern

COMMITS = 5
TIMEOUT = 3  # seconds; a git or gh call that takes longer is skipped, not waited on

# The newest pull requests, with only the overall state of the last commit's checks: asking for
# every check run as well takes gh several seconds on a repo with many pull requests.
PULL_REQUESTS = """
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    pullRequests(first: 100, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        number title body headRefName state isDraft
        commits(last: 1) { nodes { commit { statusCheckRollup { state } } } }
      }
    }
  }
}
"""

CHECKS = {
    "SUCCESS": "passing",
    "FAILURE": "failing",
    "ERROR": "failing",
    "PENDING": "pending",
    "EXPECTED": "pending",
}


@dataclass(frozen=True)
class Commit:
    hash: str
    subject: str


@dataclass(frozen=True)
class PullRequest:
    number: int
    title: str
    body: str
    branch: str
    state: str  # open, draft, merged or closed
    checks: str  # passing, failing, pending, or "" when it has none

    def mentions(self, item_id: str) -> bool:
        """Whether the exact ID is in the title or body, or the ID in any case in the branch."""
        return bool(
            mention_pattern(item_id).search(f"{self.title}\n{self.body}")
            or mention_pattern(item_id, ignore_case=True).search(self.branch)
        )


def branches(root: Path, item_id: str) -> list[str]:
    """Local branches whose names have the ID, in any case, such as ex-12-drag-cards."""
    pattern = mention_pattern(item_id, ignore_case=True)
    names = _run(root, "git", "branch", "--format=%(refname:short)").splitlines()
    return [name for name in names if pattern.search(name)]


def commits(root: Path, item_id: str, limit: int = COMMITS) -> list[Commit]:
    """The newest commits whose message has the exact ID, so EX-12 doesn't match EX-120."""
    pattern = mention_pattern(item_id)
    out = _run(
        root,
        "git",
        "log",
        "HEAD",
        "--branches",
        "--no-show-signature",
        "--fixed-strings",
        f"--grep={item_id}",
        "--format=%h%x1f%s%x1f%B%x1e",
    )
    found = []
    for record in out.split("\x1e"):
        parts = record.strip().split("\x1f")
        if len(parts) == 3 and pattern.search(parts[2]):
            found.append(Commit(parts[0], parts[1]))
            if len(found) == limit:
                break
    return found


def pull_requests(root: Path) -> list[PullRequest]:
    """The repo's 100 newest pull requests on GitHub, newest first, read with one `gh` call.

    Empty when gh is missing, fails or is too slow, or when the repo has no GitHub remote.
    """
    out = _run(
        root,
        "gh",
        "api",
        "graphql",
        "-f",
        f"query={PULL_REQUESTS}",
        "-F",
        "owner={owner}",
        "-F",
        "repo={repo}",
    )
    try:
        nodes = json.loads(out)["data"]["repository"]["pullRequests"]["nodes"]
        return [_pull_request(node) for node in nodes]
    except (ValueError, LookupError, TypeError, AttributeError):
        return []


def _pull_request(node: dict) -> PullRequest:
    state = node["state"].lower()
    if state == "open" and node["isDraft"]:
        state = "draft"
    last = node["commits"]["nodes"]
    rollup = last[0]["commit"]["statusCheckRollup"] if last else None
    checks = CHECKS.get(rollup["state"], "") if rollup else ""
    return PullRequest(
        int(node["number"]), node["title"], node["body"] or "", node["headRefName"], state, checks
    )


def _run(root: Path, *command: str) -> str:
    """What a command prints, run from `root`, or "" when it's missing, fails or is too slow."""
    try:
        result = subprocess.run(
            list(command),
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout if result.returncode == 0 else ""
