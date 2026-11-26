#!/usr/bin/env python3
"""Tests for roll.py and game.py. Run: python3 engine/test_engine.py"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import game  # noqa: E402
import roll  # noqa: E402


def run(module, *argv, stdin: str | None = None) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    patches = [contextlib.redirect_stdout(out), contextlib.redirect_stderr(err)]
    if stdin is not None:
        patches.append(mock.patch.object(sys, "stdin", io.StringIO(stdin)))
    with contextlib.ExitStack() as stack:
        for patch in patches:
            stack.enter_context(patch)
        code = module.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class Sandbox(unittest.TestCase):
    """A temporary game-master folder with its own git repository."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "games").mkdir()
        for module in (roll, game):
            for name, value in (("ROOT", self.root), ("GAMES", self.root / "games")):
                patcher = mock.patch.object(module, name, value)
                patcher.start()
                self.addCleanup(patcher.stop)
        patcher = mock.patch.object(game, "RUNTIME", self.root / ".runtime")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def git_init(self):
        for args in (
            ["init", "-q"],
            ["config", "user.email", "test@example.invalid"],
            ["config", "user.name", "Test"],
            ["config", "commit.gpgsign", "false"],
            ["commit", "-q", "--allow-empty", "-m", "init"],
        ):
            subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def new_game(self, slug="ashfall", genre="politics"):
        code, out, err = run(game, "new", slug, "--genre", genre, "--title", "Ashfall")
        self.assertEqual(code, 0, err)
        return self.root / "games" / slug


class TierTests(unittest.TestCase):
    def test_margins(self):
        cases = {10: "CRITICAL", 9: "SUCCESS", 0: "SUCCESS", -1: "PARTIAL", -4: "PARTIAL",
                 -5: "FAILURE", -9: "FAILURE", -10: "DISASTER"}
        for margin, expected in cases.items():
            self.assertEqual(roll.tier_for(margin, 10), expected, margin)

    def test_naturals_shift_one_tier(self):
        self.assertEqual(roll.tier_for(-2, 20), "SUCCESS")
        self.assertEqual(roll.tier_for(12, 20), "CRITICAL")
        self.assertEqual(roll.tier_for(3, 1), "PARTIAL")
        self.assertEqual(roll.tier_for(-12, 1), "DISASTER")

    def test_advantage_keeps_higher(self):
        with mock.patch.object(roll, "d", side_effect=[4, 17]):
            self.assertEqual(roll.roll_check(2, 15, "adv")["kept"], 17)
        with mock.patch.object(roll, "d", side_effect=[4, 17]):
            result = roll.roll_check(2, 15, "dis")
        self.assertEqual((result["kept"], result["total"], result["outcome"]), (4, 6, "FAILURE"))

    def test_dice_expressions(self):
        for _ in range(200):
            result = roll.roll_expr("2d6+1")
            self.assertTrue(3 <= result["total"] <= 13)
            self.assertTrue(1 <= roll.roll_expr("d20")["total"] <= 20)
        for bad in ("banana", "0d6", "2d1", "99d6", "2d6+"):
            with self.assertRaises(roll.RollError):
                roll.roll_expr(bad)

    def test_d20_is_roughly_uniform(self):
        counts = [0] * 20
        for _ in range(20000):
            counts[roll.d(20) - 1] += 1
        self.assertTrue(all(800 <= c <= 1200 for c in counts), counts)


class RollLogTests(Sandbox):
    def check(self, *extra):
        return run(roll, "ashfall", "check", "--skill", "Rhetoric", "--mod", "3",
                   "--dc", "15", "--stakes", "win: x / lose: y", *extra)

    def test_rolls_are_logged_and_chained(self):
        base = self.new_game()
        for _ in range(3):
            code, out, _ = self.check()
            self.assertEqual(code, 0)
            self.assertIn("stakes: win: x / lose: y", out)
        code, out, _ = run(roll, "ashfall", "dice", "1d20", "--why", "weekly event")
        self.assertEqual(code, 0)
        entries = roll.read_log(base / "rolls.log")
        self.assertEqual([e["n"] for e in entries], [1, 2, 3, 4])
        self.assertEqual(roll.verify_entries(entries), [])
        code, out, _ = run(roll, "ashfall", "verify")
        self.assertEqual((code, "chain intact" in out), (0, True))

    def test_edited_or_deleted_entries_are_detected(self):
        base = self.new_game()
        for _ in range(3):
            self.check()
        log = base / "rolls.log"
        lines = log.read_text().splitlines()

        edited = json.loads(lines[1])
        edited["kept"], edited["outcome"] = 20, "CRITICAL"
        log.write_text("\n".join([lines[0], json.dumps(edited), lines[2]]) + "\n")
        self.assertEqual(run(roll, "ashfall", "verify")[0], 1)
        code, _, err = self.check()
        self.assertEqual(code, 2)
        self.assertIn("does not verify", err)

        log.write_text("\n".join([lines[0], lines[2]]) + "\n")
        self.assertEqual(run(roll, "ashfall", "verify")[0], 1)

        log.write_text("\n".join(lines) + "\n")
        self.assertEqual(run(roll, "ashfall", "verify")[0], 0)

    def test_stakes_are_required(self):
        self.new_game()
        self.assertEqual(self.check("--stakes", "  ")[0], 2)
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            roll.main(["ashfall", "check", "--skill", "X", "--mod", "1", "--dc", "12"])

    def test_one_reroll_per_roll(self):
        self.new_game()
        self.check()
        code, out, _ = self.check("--reroll-of", "1")
        self.assertEqual(code, 0)
        self.assertIn("[reroll of #1]", out)
        code, _, err = self.check("--reroll-of", "1")
        self.assertEqual(code, 2)
        self.assertIn("already been rerolled", err)
        code, _, err = self.check("--reroll-of", "2")
        self.assertEqual(code, 2)
        self.assertIn("itself a reroll", err)

    def test_reroll_cannot_change_the_roll(self):
        self.new_game()
        self.check()
        code, _, err = run(roll, "ashfall", "check", "--skill", "Rhetoric", "--mod", "5",
                           "--dc", "12", "--stakes", "s", "--reroll-of", "1")
        self.assertEqual(code, 2)
        self.assertIn("mod, dc", err)

    def test_hidden_rolls_are_masked_in_the_log_view(self):
        self.new_game()
        self.check("--hidden", "--who", "House Varn")
        _, out, _ = run(roll, "ashfall", "log")
        self.assertIn("hidden roll", out)
        self.assertNotIn("Rhetoric", out)
        _, out, _ = run(roll, "ashfall", "log", "--reveal")
        self.assertIn("House Varn", out)

    def test_unknown_game(self):
        code, _, err = run(roll, "nope", "verify")
        self.assertEqual(code, 2)
        self.assertIn("no game called", err)
        self.assertEqual(run(roll, "../etc", "verify")[0], 2)


class GameTests(Sandbox):
    def test_new_creates_a_complete_folder(self):
        base = self.new_game()
        for name in game.REQUIRED + ["rolls.log"]:
            self.assertTrue((base / name).exists(), name)
        self.assertTrue((base / "world").is_dir())
        self.assertIn("**Title:** Ashfall", (base / "game.md").read_text())
        self.assertIn("strategy and politics", (base / "rules.md").read_text())
        self.assertEqual(run(game, "new", "ashfall", "--genre", "politics")[0], 2)
        self.assertEqual(run(game, "new", "other", "--genre", "western")[0], 2)
        self.assertEqual(run(game, "new", "Bad Name", "--genre", "politics")[0], 2)

    def test_every_genre_template_fits_its_budget(self):
        budget = dict(game.HOT_FILES)["rules.md"]
        for path in (game.TEMPLATES / "genres").glob("*.md"):
            self.assertLessEqual(game.line_count(path), budget, path.name)
            self.assertNotIn("{{", path.read_text(), path.name)

    def test_a_fresh_game_only_warns_about_placeholders(self):
        base = self.new_game()
        errors, warnings = game.check_game("ashfall")
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 2, warnings)
        self.assertTrue(all("placeholders" in w for w in warnings))
        # Examples inside the templates' comments are not real entries.
        self.assertEqual(game.chronicle_tail(base / "chronicle.md"), (0, ""))
        self.assertIn("chronicle.md has no entries yet", run(game, "load", "ashfall")[1])

    def test_check_reports_problems(self):
        base = self.new_game()

        (base / "world" / "varn.md").write_text("# House Varn\n")
        (base / "index.md").write_text("- [Ghost](world/ghost.md): missing\n")
        (base / "state.md").write_text("line\n" * 200)
        (base / "secrets" / "fronts.md").unlink()
        errors, warnings = game.check_game("ashfall")
        text = "\n".join(warnings)
        self.assertIn("secrets/fronts.md is missing", errors)
        self.assertIn("world/ghost.md, which does not exist", text)
        self.assertIn("world/varn.md is not listed", text)
        self.assertIn("state.md is 200 lines", text)
        self.assertEqual(run(game, "check", "ashfall")[0], 1)

    def test_save_commits_only_the_game(self):
        self.git_init()
        base = self.new_game()
        (self.root / "unrelated.txt").write_text("not part of the save\n")
        code, out, _ = run(game, "save", "ashfall", "-m", "session zero")
        self.assertEqual(code, 0, out)
        self.assertIn("Saved: save(ashfall): session zero", out)
        files = subprocess.run(
            ["git", "-C", str(self.root), "show", "--name-only", "--format=", "HEAD"],
            capture_output=True, text=True, check=True).stdout.split()
        self.assertTrue(files and all(f.startswith("games/ashfall/") for f in files), files)
        self.assertIn("Nothing changed", run(game, "save", "ashfall")[1])

        (base / "state.md").write_text("- **When:** Day 2\n")
        (base / "world" / "new.md").write_text("# New\n")
        code, out, _ = run(game, "save", "ashfall")
        self.assertIn("save(ashfall): checkpoint", out)
        self.assertEqual(game.unsaved("ashfall"), [])

    def test_save_without_git(self):
        self.new_game()
        with mock.patch.object(game, "in_git", return_value=False):
            code, out, _ = run(game, "save", "ashfall")
        self.assertEqual(code, 0)
        self.assertIn("not in a git repository", out)

    def test_load_lists_hot_files_and_records_the_session(self):
        base = self.new_game()
        (base / "chronicle.md").write_text("# C\n\n## Session 1: Arrival\n\ntext\n\n## Session 2: The Vote\n")
        (base / "state.md").write_text("# State\n\n- **When:** Day 14, evening\n")
        code, out, _ = run(game, "load", "ashfall", "--session", "abc-123")
        self.assertEqual(code, 0)
        for name in ("game.md", "rules.md", "state.md", "index.md", "fronts.md"):
            self.assertIn(name, out)
        self.assertIn("from line 7 (last entry: Session 2: The Vote)", out)
        self.assertIn("In-game: Day 14, evening", out)
        self.assertEqual(game.read_json(game.session_path("abc-123"))["game"], "ashfall")
        # An unsubstituted placeholder is not a session id.
        self.assertEqual(run(game, "load", "ashfall", "--session", "${CLAUDE_SESSION_ID}")[0], 0)
        self.assertEqual(len(list((self.root / ".runtime").glob("*.json"))), 1)

    def test_list(self):
        self.assertIn("No games yet", run(game, "list")[1])
        self.new_game()
        self.assertIn("ashfall: Ashfall (politics)", run(game, "list")[1])


class HookTests(Sandbox):
    SID = "sess-1"

    def hook(self, event, **data):
        data.setdefault("session_id", self.SID)
        code, out, _ = run(game, "hook", event, stdin=json.dumps(data))
        self.assertEqual(code, 0)
        return out

    def test_session_start_lists_games(self):
        self.assertIn("No saved games", self.hook("session-start", source="startup"))
        self.new_game()
        self.assertIn("ashfall: Ashfall", self.hook("session-start", source="startup"))

    def test_session_start_after_compaction_points_at_files(self):
        self.new_game()
        run(game, "load", "ashfall", "--session", self.SID)
        out = self.hook("session-start", source="compact")
        self.assertIn("just compacted", out)
        self.assertIn("state.md", out)
        self.assertIn("was playing 'ashfall'", self.hook("session-start", source="resume"))
        # A different chat has no game loaded.
        self.assertNotIn("compacted", self.hook("session-start", source="compact", session_id="other"))

    def test_prompt_hook_is_silent_without_a_game(self):
        self.new_game()
        self.assertEqual(self.hook("prompt"), "")

    def test_prompt_hook_anchor_and_save_nudge(self):
        self.new_game()
        run(game, "load", "ashfall", "--session", self.SID)
        outputs = [self.hook("prompt") for _ in range(16)]
        anchored = [i + 1 for i, o in enumerate(outputs) if "Table rules in force" in o]
        nudged = [i + 1 for i, o in enumerate(outputs) if "last checkpoint" in o]
        self.assertEqual(anchored, [6, 12])
        self.assertEqual(nudged, [12, 16])
        run(game, "save", "ashfall")
        self.assertEqual(game.read_json(game.session_path(self.SID))["since_save"], 0)

    def test_context_notes_fire_once_per_level(self):
        self.new_game()
        run(game, "load", "ashfall", "--session", self.SID)

        def status(pct, tokens):
            payload = {"session_id": self.SID,
                       "context_window": {"used_percentage": pct, "total_input_tokens": tokens}}
            return run(game, "statusline", stdin=json.dumps(payload))[1]

        self.assertIn("chat 10% full", status(10, 20_000))
        self.assertNotIn("getting long", self.hook("prompt"))
        status(13, 130_000)  # a 1M window: few percent, many tokens
        self.assertIn("getting long", self.hook("prompt"))
        self.assertNotIn("getting long", self.hook("prompt"))
        status(80, 160_000)
        self.assertIn("very long", self.hook("prompt"))
        self.assertNotIn("very long", self.hook("prompt"))

    def test_statusline_shows_game_and_date(self):
        base = self.new_game()
        (base / "state.md").write_text("- **When:** Day 14, evening\n")
        payload = json.dumps({"session_id": self.SID, "context_window": {"used_percentage": 42.4}})
        self.assertIn("no game loaded", run(game, "statusline", stdin=payload)[1])
        run(game, "load", "ashfall", "--session", self.SID)
        self.assertEqual(run(game, "statusline", stdin=payload)[1].strip(),
                         "Ashfall | Day 14, evening | chat 42% full")

    def test_pre_compact_gives_summary_instructions(self):
        self.new_game()
        self.assertEqual(self.hook("pre-compact", trigger="auto"), "")
        run(game, "load", "ashfall", "--session", self.SID)
        self.assertIn("Not yet saved to files", self.hook("pre-compact", trigger="auto"))

    def test_hooks_survive_bad_input(self):
        for stdin in ("", "not json", "[1,2]", '{"session_id": "../../x"}'):
            for event in ("session-start", "prompt", "pre-compact"):
                self.assertEqual(run(game, "hook", event, stdin=stdin)[0], 0)
            self.assertEqual(run(game, "statusline", stdin=stdin)[0], 0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
