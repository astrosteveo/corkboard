import json
import os
import subprocess
import time
import unittest
from unittest import mock

from helpers import LOG, Fixture

from corkboard import api, development


class GitFixture(Fixture):
    """A temporary repo with a .project/ folder that is also a git repo.

    Git's global and system config are switched off for the whole test, for both these helpers
    and the git that corkboard runs, so the user's settings can't change the output.
    """

    def __init__(self, test: unittest.TestCase) -> None:
        super().__init__(test)
        test.enterContext(
            mock.patch.dict(
                os.environ, {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
            )
        )
        self.commits = 0
        self.git("init", "-q", "-b", "main")

    def git(self, *args: str) -> str:
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.com",
        }
        result = subprocess.run(
            ["git", *args], cwd=self.repo, env=env, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()

    def commit(self, message: str) -> str:
        """Makes an empty commit a minute after the last one, and returns its short hash."""
        self.commits += 1
        date = f"2026-11-12T10:{self.commits:02d}:00"
        with mock.patch.dict(os.environ, {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}):
            self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("log", "-1", "--format=%h")


def pr(number, title, state="MERGED", body="", branch="other", draft=False, checks=None):
    """One pull request the way GitHub's API returns it."""
    rollup = {"state": checks} if checks else None
    return {
        "number": number,
        "title": title,
        "body": body,
        "headRefName": branch,
        "state": state,
        "isDraft": draft,
        "url": f"https://github.com/example/repo/pull/{number}",
        "commits": {"nodes": [{"commit": {"statusCheckRollup": rollup}}]},
    }


def answer(fixture: Fixture, *prs: dict) -> None:
    """Makes the fake gh print these pull requests, as `gh api graphql` would."""
    reply = {"data": {"repository": {"pullRequests": {"nodes": list(prs)}}}}
    path = fixture.tools / "reply.json"
    path.write_text(json.dumps(reply), encoding="utf-8")
    fixture.gh(f"exec cat '{path}'")


class ShowDevelopmentTest(unittest.TestCase):
    def test_lists_the_branch_and_the_last_five_commits(self):
        fixture = GitFixture(self)
        fixture.item(
            "EX-12",
            "What and why.\n\n## Subtasks\n- [x] Detect the drop column\n" + LOG,
            title="Drag cards between columns",
            status="in-progress",
        )
        fixture.commit("feat(board): first try (EX-12)")
        fixture.commit("chore: something else")
        fixture.commit("fix: only EX-120")
        fixture.commit("docs: lowercase ex-12 isn't the ID")
        body = fixture.commit("refactor(board): tidy the card\n\nPart of EX-12.")
        order = fixture.commit("fix(board): keep card order on drop (EX-12)")
        tests = fixture.commit("test(board): drop tests (EX-12)")
        final = fixture.commit("feat(board): detect drop column (EX-12)")
        fixture.git("switch", "-q", "-c", "ex-12-drag-cards")
        branch = fixture.commit("wip: only on the branch (EX-12)")
        fixture.git("switch", "-q", "main")
        fixture.git("branch", "ex-120-other")

        code, out, err = fixture.run("show", "EX-12")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(
            out,
            "EX-12 task · in-progress · medium · claude\n"
            "Drag cards between columns\n"
            "path: .project/items/EX-12-drag-cards-between-columns.md\n"
            "\n"
            "What and why.\n"
            "\n"
            "Subtasks 1/1\n"
            "  1 [x] Detect the drop column\n"
            "\n"
            "Development\n"
            "  branch: ex-12-drag-cards\n"
            f"  {branch} wip: only on the branch (EX-12)\n"
            f"  {final} feat(board): detect drop column (EX-12)\n"
            f"  {tests} test(board): drop tests (EX-12)\n"
            f"  {order} fix(board): keep card order on drop (EX-12)\n"
            f"  {body} refactor(board): tidy the card\n"
            "\n"
            "Log\n"
            "  2026-11-12 10:00 me: created\n",
        )

    def test_lists_pull_requests_between_the_branch_and_the_commits(self):
        fixture = GitFixture(self)
        fixture.item("EX-12", title="Drag cards between columns")
        commit = fixture.commit("feat(board): detect drop column (EX-12)")
        fixture.git("branch", "ex-12-drag-cards")
        answer(
            fixture,
            pr(17, "Drag cards, part two", "OPEN", body="Follows EX-12.", checks="PENDING"),
            pr(
                16, "fix: card order", "OPEN", branch="EX-12-card-order", draft=True, checks="ERROR"
            ),
            pr(15, "Only EX-120", "OPEN"),
            pr(14, "Drag cards between columns (EX-12)", checks="SUCCESS"),
            pr(13, "Lowercase ex-12 in a title isn't the ID"),
            pr(12, "Dropped idea (EX-12)", "CLOSED", checks="FAILURE"),
            pr(11, "No checks yet (EX-12)", "OPEN"),
        )

        code, out, err = fixture.run("show", "EX-12")
        self.assertEqual((code, err), (0, ""))
        self.assertIn(
            "Development\n"
            "  branch: ex-12-drag-cards\n"
            "  PR #17 Drag cards, part two · open · checks pending\n"
            "  PR #16 fix: card order · draft · checks failing\n"
            "  PR #14 Drag cards between columns (EX-12) · merged\n"
            "  PR #12 Dropped idea (EX-12) · closed\n"
            "  PR #11 No checks yet (EX-12) · open\n"
            f"  {commit} feat(board): detect drop column (EX-12)\n"
            "\n",
            out,
        )

    def test_without_pull_requests_nothing_else_changes(self):
        fixture = GitFixture(self)
        fixture.item("EX-12")
        fixture.commit("feat(board): detect drop column (EX-12)")
        fixture.git("branch", "ex-12-drag-cards")
        answer(fixture)
        _, expected, _ = fixture.run("show", "EX-12")
        self.assertIn("Development\n  branch: ex-12-drag-cards\n", expected)

        cases = {
            "fails": "echo 'no git remotes found' >&2; exit 1",
            "prints something else": "echo 'not json'",
            "hangs": "exec sleep 30",
        }
        for name, script in cases.items():
            with self.subTest(gh=name):
                fixture.gh(script)
                started = time.monotonic()
                with mock.patch("corkboard.development.TIMEOUT", 0.5):
                    code, out, err = fixture.run("show", "EX-12")
                self.assertLess(time.monotonic() - started, 5)
                self.assertEqual((code, out, err), (0, expected, ""))

    def test_left_out_when_nothing_mentions_the_item(self):
        fixture = GitFixture(self)
        fixture.item("EX-1")
        fixture.commit("chore: nothing about EX-10")
        _, out, _ = fixture.run("show", "EX-1")
        self.assertNotIn("Development", out)

    def test_left_out_outside_a_git_repo(self):
        fixture = Fixture(self)
        fixture.item("EX-1")
        code, out, err = fixture.run("show", "EX-1")
        self.assertEqual((code, err), (0, ""))
        self.assertNotIn("Development", out)


class ApiDevelopmentTest(unittest.TestCase):
    def test_the_item_panel_gets_what_show_lists(self):
        fixture = GitFixture(self)
        fixture.item("EX-12", title="Drag cards between columns")
        first = fixture.commit("feat(board): detect drop column (EX-12)")
        fixture.commit("chore: something else")
        second = fixture.commit("fix(board): keep card order on drop (EX-12)")
        fixture.git("branch", "ex-12-drag-cards")
        answer(
            fixture,
            pr(14, "Drag cards between columns (EX-12)", "OPEN", checks="SUCCESS"),
            pr(13, "Only EX-120"),
        )

        _, out, _ = fixture.run("show", "EX-12")
        self.assertIn(
            "Development\n"
            "  branch: ex-12-drag-cards\n"
            "  PR #14 Drag cards between columns (EX-12) · open · checks passing\n"
            f"  {second} fix(board): keep card order on drop (EX-12)\n"
            f"  {first} feat(board): detect drop column (EX-12)\n",
            out,
        )
        self.assertEqual(
            api.item_extras(fixture.load(), "ex-12")["development"],
            {
                "branches": ["ex-12-drag-cards"],
                "pull_requests": [
                    {
                        "number": 14,
                        "title": "Drag cards between columns (EX-12)",
                        "state": "open",
                        "checks": "passing",
                        "url": "https://github.com/example/repo/pull/14",
                    }
                ],
                "commits": [
                    {
                        "hash": second,
                        "subject": "fix(board): keep card order on drop (EX-12)",
                        "date": "2026-11-12",
                    },
                    {
                        "hash": first,
                        "subject": "feat(board): detect drop column (EX-12)",
                        "date": "2026-11-12",
                    },
                ],
            },
        )

    def test_nothing_when_nothing_mentions_the_item(self):
        fixture = GitFixture(self)
        fixture.item("EX-1")
        fixture.commit("chore: nothing about EX-10")
        self.assertEqual(
            api.item_extras(fixture.load(), "EX-1")["development"],
            {"branches": [], "pull_requests": [], "commits": []},
        )


class DevelopmentTest(unittest.TestCase):
    def test_branches_match_in_any_case_but_not_a_longer_id(self):
        fixture = GitFixture(self)
        fixture.commit("chore: start")
        for name in ("ex-12-drag-cards", "feature/EX-12", "ex-120-other", "xex-12", "ex-1"):
            fixture.git("branch", name)
        self.assertEqual(
            development.branches(fixture.root, "EX-12"), ["ex-12-drag-cards", "feature/EX-12"]
        )

    def test_a_repo_with_no_commits_has_nothing(self):
        fixture = GitFixture(self)
        self.assertEqual(development.branches(fixture.root, "EX-1"), [])
        self.assertEqual(development.commits(fixture.root, "EX-1"), [])

    def test_git_or_gh_missing_or_too_slow_gives_nothing(self):
        fixture = GitFixture(self)
        fixture.commit("feat: thing (EX-1)")
        answer(fixture, pr(1, "Thing (EX-1)"))
        self.assertEqual(len(development.pull_requests(fixture.root)), 1)
        for error in (FileNotFoundError("git"), subprocess.TimeoutExpired("git", 3)):
            with self.subTest(error=error):
                with mock.patch("corkboard.development.subprocess.run", side_effect=error):
                    self.assertEqual(development.commits(fixture.root, "EX-1"), [])
                    self.assertEqual(development.branches(fixture.root, "EX-1"), [])
                    self.assertEqual(development.pull_requests(fixture.root), [])

    def test_pull_request_states_and_checks(self):
        fixture = Fixture(self)
        no_commits = pr(5, "Five", "OPEN")
        no_commits["commits"]["nodes"] = []
        answer(
            fixture,
            pr(7, "Seven", "OPEN", body=None, checks="EXPECTED"),
            pr(6, "Six", "OPEN", draft=True, checks="SUCCESS"),
            no_commits,
            pr(4, "Four", "MERGED", draft=True, checks="ERROR"),
            pr(3, "Three", "CLOSED", checks="SOMETHING_NEW"),
        )
        self.assertEqual(
            [
                (p.number, p.body, p.state, p.checks)
                for p in development.pull_requests(fixture.root)
            ],
            [
                (7, "", "open", "pending"),
                (6, "", "draft", "passing"),
                (5, "", "open", ""),
                (4, "", "merged", "failing"),
                (3, "", "closed", ""),
            ],
        )

    def test_unexpected_gh_output_gives_nothing(self):
        fixture = Fixture(self)
        replies = [
            "",
            "not json",
            "[]",
            '{"data": null}',
            '{"errors": [{"message": "Could not resolve to a Repository"}]}',
            '{"data": {"repository": {"pullRequests": {"nodes": [{"number": 1}]}}}}',
        ]
        for reply in replies:
            with self.subTest(reply=reply):
                path = fixture.tools / "reply.txt"
                path.write_text(reply, encoding="utf-8")
                fixture.gh(f"exec cat '{path}'")
                self.assertEqual(development.pull_requests(fixture.root), [])

    def test_a_pull_request_mentions_the_exact_id_or_the_branch_in_any_case(self):
        def mentions(title="", body="", branch=""):
            return development.PullRequest(1, title, body, branch, "open", "").mentions("EX-12")

        self.assertTrue(mentions(title="Drag cards (EX-12)"))
        self.assertTrue(mentions(body="Part of EX-12."))
        self.assertTrue(mentions(branch="ex-12-drag-cards"))
        self.assertTrue(mentions(branch="feature/EX-12"))
        self.assertFalse(mentions(title="Only EX-120", body="XEX-12", branch="ex-120-other"))
        self.assertFalse(mentions(title="lowercase ex-12", body="ex-12"))


if __name__ == "__main__":
    unittest.main()
