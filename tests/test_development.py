import os
import subprocess
import unittest
from unittest import mock

from helpers import LOG, Fixture

from corkboard import development


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

    def test_git_missing_or_too_slow_gives_nothing(self):
        fixture = GitFixture(self)
        fixture.commit("feat: thing (EX-1)")
        for error in (FileNotFoundError("git"), subprocess.TimeoutExpired("git", 3)):
            with self.subTest(error=error):
                with mock.patch("corkboard.development.subprocess.run", side_effect=error):
                    self.assertEqual(development.commits(fixture.root, "EX-1"), [])
                    self.assertEqual(development.branches(fixture.root, "EX-1"), [])


if __name__ == "__main__":
    unittest.main()
