#!/usr/bin/env python3
"""Save-file housekeeping for the game table.

    python3 engine/game.py list
    python3 engine/game.py new <game> --genre politics --title "Ashfall"
    python3 engine/game.py load <game> [--session ID]
    python3 engine/game.py check <game>
    python3 engine/game.py save <game> -m "what happened"

`hook` and `statusline` are called by Claude Code itself (see
.claude/settings.json), not by hand.

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import roll  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GAMES = ROOT / "games"
TEMPLATES = ROOT / "templates"
RUNTIME = ROOT / ".runtime"

# Files read at the start of every session, with a soft line budget each.
# Budgets keep the always-loaded part of a long game small; detail belongs
# in world/, secrets/ and chronicle.md, which are read only when needed.
HOT_FILES = [
    ("game.md", 120),
    ("rules.md", 220),
    ("state.md", 150),
    ("index.md", 400),
    ("secrets/fronts.md", 150),
]
REQUIRED = [name for name, _ in HOT_FILES] + ["chronicle.md"]

# Nudges added to the GM's context by the prompt hook.
ANCHOR_EVERY = 6  # player turns between reminders of the table rules
SAVE_NUDGE_AT = 12  # player turns without a checkpoint before saying so
SAVE_NUDGE_REPEAT = 4
# (level, percent of window, tokens): whichever is reached first.
CONTEXT_LEVELS = [(1, 50, 120_000), (2, 75, 180_000)]

ANCHOR = (
    "Table rules in force for this game: stakes and difficulty are stated before any roll; "
    "dice come only from engine/roll.py and the result stands; world facts come from the "
    "game files, not from what would be convenient; a failed roll costs something on the sheet."
)


class GameError(Exception):
    pass


# ------------------------------------------------------------------ helpers


def game_dir(slug: str) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        raise GameError(f"'{slug}' is not a game name (lowercase letters, digits, hyphens)")
    path = GAMES / slug
    if not path.is_dir():
        raise GameError(f"no game called '{slug}'. Existing games: {', '.join(slugs()) or 'none'}")
    return path


def slugs() -> list[str]:
    if not GAMES.is_dir():
        return []
    return sorted(p.name for p in GAMES.iterdir() if p.is_dir() and (p / "game.md").exists())


def shown(path: Path) -> str:
    """Path as the GM should type it from the current directory."""
    try:
        return os.path.relpath(path, Path.cwd())
    except ValueError:
        return str(path)


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def field(path: Path, name: str) -> str:
    """Value of a '- **Name:** value' line near the top of a file."""
    if not path.exists():
        return ""
    pattern = re.compile(rf"^\s*[-*]?\s*\*\*{re.escape(name)}:?\*\*:?\s*(.+?)\s*$", re.IGNORECASE)
    for line in path.read_text(encoding="utf-8").splitlines()[:40]:
        match = pattern.match(line)
        if match and "{{" not in match.group(1):
            return match.group(1)
    return ""


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=False
    )


def in_git() -> bool:
    try:
        return git("rev-parse", "--is-inside-work-tree").stdout.strip() == "true"
    except FileNotFoundError:
        return False


def last_save(slug: str) -> str:
    if not in_git():
        return ""
    out = git("log", "-1", "--format=%cd  %s", "--date=format:%Y-%m-%d %H:%M", "--", f"games/{slug}")
    return out.stdout.strip()


def unsaved(slug: str) -> list[str]:
    if not in_git():
        return []
    out = git("status", "--porcelain", "--", f"games/{slug}")
    return [line for line in out.stdout.splitlines() if line.strip()]


# ------------------------------------------------- per-session runtime state


def valid_session(session: str | None) -> str | None:
    if session and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session):
        return session
    return None


def session_path(session: str) -> Path:
    return RUNTIME / f"{session}.json"


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    os.replace(tmp, path)


def prune_runtime(max_age_days: int = 30) -> None:
    if not RUNTIME.is_dir():
        return
    cutoff = time.time() - max_age_days * 86400
    for path in RUNTIME.iterdir():
        try:
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            pass


# ------------------------------------------------------------------- checks


def without_comments(text: str) -> str:
    """Blank out HTML comments, keeping line numbers. Templates use them for examples."""
    return re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.DOTALL)


def chronicle_tail(path: Path) -> tuple[int, str]:
    """Line number and title of the last '## ' entry in the chronicle."""
    start, title = 0, ""
    if path.exists():
        text = without_comments(path.read_text(encoding="utf-8"))
        for lineno, line in enumerate(text.splitlines(), 1):
            if line.startswith("## "):
                start, title = lineno, line[3:].strip()
    return start, title


def check_game(slug: str) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for a game folder."""
    base = game_dir(slug)
    errors, warnings = [], []

    for name in REQUIRED:
        if not (base / name).exists():
            errors.append(f"{name} is missing")

    for name, budget in HOT_FILES:
        path = base / name
        if path.exists():
            lines = line_count(path)
            if lines > budget:
                warnings.append(
                    f"{name} is {lines} lines (budget {budget}): move detail into world/, "
                    "secrets/ or chronicle.md"
                )

    for name in ("game.md", "state.md", "rules.md"):
        path = base / name
        if path.exists() and "{{" in path.read_text(encoding="utf-8"):
            warnings.append(f"{name} still has unfilled {{{{placeholders}}}}")

    index = base / "index.md"
    if index.exists():
        text = without_comments(index.read_text(encoding="utf-8"))
        linked = set(re.findall(r"\]\((world/[^)#\s]+\.md)\)", text))
        for target in sorted(linked):
            if not (base / target).exists():
                warnings.append(f"index.md links to {target}, which does not exist")
        world = base / "world"
        if world.is_dir():
            for path in sorted(world.rglob("*.md")):
                rel = path.relative_to(base).as_posix()
                if rel not in linked:
                    warnings.append(f"{rel} is not listed in index.md")

    try:
        problems = roll.verify_entries(roll.read_log(base / roll.LOG_NAME))
    except roll.RollError as exc:
        problems = [str(exc)]
    if problems:
        errors.append("rolls.log does not verify: " + "; ".join(problems[:3]))

    return errors, warnings


# ----------------------------------------------------------------- commands


def cmd_list(args) -> int:
    names = slugs()
    if not names:
        print("No games yet. /new-game starts one.")
        return 0
    for slug in names:
        base = GAMES / slug
        title = field(base / "game.md", "Title") or slug
        genre = field(base / "game.md", "Genre") or "?"
        when = field(base / "state.md", "When") or "not started"
        saved = last_save(slug).split("  ")[0] or "never saved"
        print(f"{slug}: {title} ({genre}). In-game: {when}. Last save: {saved}.")
    return 0


def cmd_new(args) -> int:
    slug = args.game
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,40}", slug):
        raise GameError("game names are short kebab-case, e.g. 'ashfall' or 'two-crowns'")
    target = GAMES / slug
    if target.exists():
        raise GameError(f"games/{slug} already exists")
    genres = sorted(p.stem for p in (TEMPLATES / "genres").glob("*.md"))
    if args.genre not in genres:
        raise GameError(f"unknown genre '{args.genre}'. Available: {', '.join(genres)}")

    shutil.copytree(TEMPLATES / "game", target)
    shutil.copyfile(TEMPLATES / "genres" / f"{args.genre}.md", target / "rules.md")
    (target / "world").mkdir(exist_ok=True)
    for keep in target.rglob(".gitkeep"):
        keep.unlink()
    values = {
        "{{TITLE}}": args.title or slug,
        "{{SLUG}}": slug,
        "{{GENRE}}": args.genre,
        "{{CREATED}}": date.today().isoformat(),
    }
    for path in target.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for key, value in values.items():
            text = text.replace(key, value)
        path.write_text(text, encoding="utf-8")
    (target / roll.LOG_NAME).touch()

    print(f"Created {shown(target)} from the '{args.genre}' ruleset:")
    for path in sorted(target.rglob("*")):
        if path.is_file():
            print("  " + shown(path))
    print("Fill the {{placeholders}} in game.md and state.md during session zero.")
    return 0


def cmd_load(args) -> int:
    slug = args.game
    base = game_dir(slug)
    prune_runtime()
    session = valid_session(args.session)
    if session:
        record = read_json(session_path(session))
        record.update({"game": slug, "prompts": 0, "since_save": 0})
        write_json(session_path(session), record)

    title = field(base / "game.md", "Title") or slug
    genre = field(base / "game.md", "Genre") or "?"
    print(f"Loaded {slug}: {title} ({genre})")
    when = field(base / "state.md", "When")
    if when:
        print(f"In-game: {when}")

    entries = roll.read_log(base / roll.LOG_NAME)
    problems = roll.verify_entries(entries)
    print(f"Rolls: {len(entries)} logged, " + ("chain intact" if not problems else "CHAIN BROKEN"))
    print(f"Last save: {last_save(slug) or 'none yet'}")
    dirty = unsaved(slug)
    if dirty:
        print(f"Unsaved changes on disk: {len(dirty)} file(s) differ from the last save")

    print("\nRead these now, in full:")
    for name, _ in HOT_FILES:
        path = base / name
        if path.exists():
            print(f"  {shown(path)} ({line_count(path)} lines)")
    start, entry = chronicle_tail(base / "chronicle.md")
    if start:
        print(f"  {shown(base / 'chronicle.md')} from line {start} (last entry: {entry})")
    else:
        print("  (chronicle.md has no entries yet)")

    errors, warnings = check_game(slug)
    if errors or warnings:
        print("\nNeeds attention:")
        for msg in errors:
            print("  ERROR " + msg)
        for msg in warnings:
            print("  " + msg)
    return 0


def cmd_check(args) -> int:
    errors, warnings = check_game(args.game)
    for msg in errors:
        print("ERROR " + msg)
    for msg in warnings:
        print("warning: " + msg)
    if not errors and not warnings:
        print(f"{args.game}: files in order")
    return 1 if errors else 0


def cmd_save(args) -> int:
    slug = args.game
    game_dir(slug)
    errors, warnings = check_game(slug)
    for msg in errors:
        print("ERROR " + msg)
    for msg in warnings:
        print("warning: " + msg)

    if RUNTIME.is_dir():
        for path in RUNTIME.glob("*.json"):
            record = read_json(path)
            if record.get("game") == slug and record.get("since_save"):
                record["since_save"] = 0
                write_json(path, record)

    if not in_git():
        print("Saved on disk. This folder is not in a git repository, so no snapshot was taken.")
        return 0
    spec = f"games/{slug}"
    if not unsaved(slug):
        print("Nothing changed since the last save.")
        return 0
    added = git("add", "--", spec)
    if added.returncode != 0:
        print("git add failed:\n" + added.stderr.strip())
        return 1
    message = f"save({slug}): {args.message.strip() or 'checkpoint'}"
    done = git("commit", "-m", message, "--", spec)
    if done.returncode != 0:
        print("git commit failed, the files are on disk but not snapshotted:")
        print((done.stderr or done.stdout).strip())
        return 1
    head = git("rev-parse", "--short", "HEAD").stdout.strip()
    print(f"Saved: {message} [{head}]")
    return 0


# -------------------------------------------------- Claude Code integration


def read_stdin_json() -> dict:
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return {}
        data = json.loads(sys.stdin.read() or "{}")
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def active_game(session: str | None) -> tuple[str | None, dict]:
    session = valid_session(session)
    if not session:
        return None, {}
    record = read_json(session_path(session))
    slug = record.get("game")
    if slug and (GAMES / slug / "game.md").exists():
        return slug, record
    return None, record


def hook_session_start(data: dict) -> None:
    source = data.get("source", "startup")
    slug, _ = active_game(data.get("session_id"))
    if slug and source in ("compact", "resume", "fork"):
        base = GAMES / slug
        hot = ", ".join(shown(base / name) for name, _ in HOT_FILES if (base / name).exists())
        if source == "compact":
            print(
                f"Game table: the game in play is '{slug}'. The conversation was just compacted, "
                "so everything before this point is now a lossy summary. The game files are the "
                "record of truth and may be behind by whatever happened since the last save."
            )
            print(
                "Any fact in the summary that is missing from the files (names, promises, "
                "numbers, a roll in progress) is at risk until it is written down."
            )
        else:
            print(
                f"Game table: this session was playing '{slug}'. The files may have moved on "
                "since this conversation last ran, for example if the game was played in "
                "another chat; where they disagree with the conversation, the files win."
            )
        print(f"Hot files, to re-read before narrating: {hot}")
        return
    names = slugs()
    if names:
        print("Game table. Saved games (start one with /play <name>, or /new-game):")
        for name in names:
            base = GAMES / name
            title = field(base / "game.md", "Title") or name
            when = field(base / "state.md", "When") or "not started"
            print(f"  {name}: {title}. In-game: {when}.")
    else:
        print("Game table. No saved games yet; /new-game starts one.")


def hook_prompt(data: dict) -> None:
    session = valid_session(data.get("session_id"))
    slug, record = active_game(session)
    if not slug:
        return
    record["prompts"] = int(record.get("prompts", 0)) + 1
    record["since_save"] = int(record.get("since_save", 0)) + 1
    notes = []

    if record["prompts"] % ANCHOR_EVERY == 0:
        notes.append(ANCHOR)

    since = record["since_save"]
    if since >= SAVE_NUDGE_AT and (since - SAVE_NUDGE_AT) % SAVE_NUDGE_REPEAT == 0:
        notes.append(
            f"The last checkpoint of '{slug}' was {since} player turns ago. Anything that "
            "happened since exists only in this conversation until the files are updated "
            f"and `python3 engine/game.py save {slug}` runs."
        )

    ctx = read_json(RUNTIME / f"{session}.ctx")
    pct = ctx.get("pct") or 0
    tokens = ctx.get("tokens") or 0
    noted = int(record.get("ctx_level", 0))
    level = 0
    for lvl, lvl_pct, lvl_tokens in CONTEXT_LEVELS:
        if pct >= lvl_pct or tokens >= lvl_tokens:
            level = lvl
    if level > noted:
        size = f"about {round(tokens / 1000)}k tokens, {round(pct)}% of the window"
        if level == 1:
            notes.append(
                f"This conversation is getting long ({size}). The player prefers ending a chat "
                "at a scene break with /wrap and continuing in a fresh one, rather than letting "
                "it be compacted. The next natural break is a good moment to offer that."
            )
        else:
            notes.append(
                f"This conversation is now very long ({size}) and compaction is close. "
                "Wrapping up at the first reasonable stopping point, with /wrap, keeps the "
                "game's memory intact."
            )
        record["ctx_level"] = level
    elif level < noted:
        record["ctx_level"] = level  # the window shrank, e.g. after compaction

    write_json(session_path(session), record)
    if notes:
        print("\n".join(notes))


def hook_pre_compact(data: dict) -> None:
    slug, _ = active_game(data.get("session_id"))
    if not slug:
        return
    # Claude Code uses a PreCompact hook's stdout as instructions for the summary.
    print(
        f"This conversation is a tabletop game session; the game in play is '{slug}' "
        f"(files under games/{slug}). In the summary, keep exactly: the current scene (where, "
        "when in game time, who is present, what just happened); the player's last stated "
        "intent; any roll that was announced but not yet resolved, with its skill, difficulty "
        "and stakes; and a list titled 'Not yet saved to files' of every name, number, promise, "
        "lie, debt or changed relationship established since the last save. Keep the player's "
        "out-of-character preferences and any house rules agreed in this chat. Prose style and "
        "earlier scenes can be dropped: the chronicle on disk covers them."
    )


def cmd_hook(args) -> int:
    # A hook must never break the session it runs in.
    try:
        data = read_stdin_json()
        {
            "session-start": hook_session_start,
            "prompt": hook_prompt,
            "pre-compact": hook_pre_compact,
        }[args.event](data)
    except Exception as exc:  # noqa: BLE001
        print(f"game.py hook {args.event}: {exc}", file=sys.stderr)
    return 0


def cmd_statusline(args) -> int:
    try:
        data = read_stdin_json()
        session = valid_session(data.get("session_id"))
        window = data.get("context_window") or {}
        pct = window.get("used_percentage")
        tokens = window.get("total_input_tokens")
        if session and (pct is not None or tokens is not None):
            write_json(RUNTIME / f"{session}.ctx", {"pct": pct or 0, "tokens": tokens or 0})
        slug, _ = active_game(session)
        parts = []
        if slug:
            base = GAMES / slug
            parts.append(field(base / "game.md", "Title") or slug)
            when = field(base / "state.md", "When")
            if when:
                parts.append(when)
        else:
            parts.append("game table: no game loaded (/play)")
        if pct is not None:
            parts.append(f"chat {round(pct)}% full")
        print(" | ".join(parts))
    except Exception:  # noqa: BLE001
        print("game table")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Save-file housekeeping for the game table.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list saved games").set_defaults(func=cmd_list)

    new = sub.add_parser("new", help="create a game folder from a genre ruleset")
    new.add_argument("game")
    new.add_argument("--genre", required=True)
    new.add_argument("--title", default="")
    new.set_defaults(func=cmd_new)

    load = sub.add_parser("load", help="mark a game as in play and list what to read")
    load.add_argument("game")
    load.add_argument("--session", default=None, help="Claude Code session id")
    load.set_defaults(func=cmd_load)

    check = sub.add_parser("check", help="lint a game folder")
    check.add_argument("game")
    check.set_defaults(func=cmd_check)

    save = sub.add_parser("save", help="lint, then snapshot the game folder with git")
    save.add_argument("game")
    save.add_argument("-m", "--message", default="")
    save.set_defaults(func=cmd_save)

    hook = sub.add_parser("hook", help="(called by Claude Code)")
    hook.add_argument("event", choices=["session-start", "prompt", "pre-compact"])
    hook.set_defaults(func=cmd_hook)

    sub.add_parser("statusline", help="(called by Claude Code)").set_defaults(func=cmd_statusline)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (GameError, roll.RollError) as exc:
        print(f"game.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
