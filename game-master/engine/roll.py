#!/usr/bin/env python3
"""Dice for the game table.

Every roll goes through this script and is appended to the game's rolls.log
before the result is printed, so no number in the story is invented and no
roll can be quietly retried.

    python3 engine/roll.py <game> check --skill Rhetoric --mod 3 --dc 15 \
        --stakes "win: the guild backs the levy / lose: they warn the chancellor"
    python3 engine/roll.py <game> dice 2d6+1 --why "weekly event"
    python3 engine/roll.py <game> log -n 10
    python3 engine/roll.py <game> verify

Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMES = ROOT / "games"
LOG_NAME = "rolls.log"
GENESIS = "0" * 16

# Outcome tiers, worst to best. A natural 20 moves the result up one tier,
# a natural 1 moves it down one.
TIERS = ["DISASTER", "FAILURE", "PARTIAL", "SUCCESS", "CRITICAL"]

TIER_MEANING = {
    "CRITICAL": "succeeds, plus an extra benefit",
    "SUCCESS": "gets what the stakes promised",
    "PARTIAL": "succeeds at a cost, or gets a lesser version",
    "FAILURE": "does not get it, and the stated cost lands",
    "DISASTER": "the stated cost lands and something else breaks too",
}


class RollError(Exception):
    pass


# ---------------------------------------------------------------- log file


def game_dir(slug: str) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        raise RollError(f"'{slug}' is not a game name (lowercase letters, digits, hyphens)")
    path = GAMES / slug
    if not path.is_dir():
        raise RollError(f"no game called '{slug}' in {GAMES}")
    return path


def entry_hash(prev: str, entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "hash"}
    payload = prev + json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def read_log(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise RollError(f"{path.name} line {lineno} is not valid JSON: {exc}") from exc
    return entries


def verify_entries(entries: list[dict]) -> list[str]:
    """Return a list of problems; empty means the chain is intact."""
    problems = []
    prev = GENESIS
    for i, entry in enumerate(entries, 1):
        if entry.get("n") != i:
            problems.append(f"entry {i}: numbered {entry.get('n')}, expected {i}")
        if entry.get("prev") != prev:
            problems.append(f"entry {i}: does not follow the entry before it")
        if entry.get("hash") != entry_hash(entry.get("prev", ""), entry):
            problems.append(f"entry {i}: contents were changed after it was written")
        prev = entry.get("hash", "")
    return problems


def append_entry(path: Path, entries: list[dict], entry: dict) -> dict:
    problems = verify_entries(entries)
    if problems:
        raise RollError(
            "rolls.log does not verify, so no new roll was made:\n  " + "\n  ".join(problems)
        )
    entry["n"] = len(entries) + 1
    entry["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry["prev"] = entries[-1]["hash"] if entries else GENESIS
    entry["hash"] = entry_hash(entry["prev"], entry)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


# -------------------------------------------------------------------- dice


def d(sides: int) -> int:
    return secrets.randbelow(sides) + 1


def tier_for(margin: int, natural: int) -> str:
    if margin >= 10:
        idx = 4
    elif margin >= 0:
        idx = 3
    elif margin >= -4:
        idx = 2
    elif margin >= -9:
        idx = 1
    else:
        idx = 0
    if natural == 20:
        idx = min(idx + 1, 4)
    elif natural == 1:
        idx = max(idx - 1, 0)
    return TIERS[idx]


def roll_check(mod: int, dc: int, mode: str) -> dict:
    dice = [d(20), d(20)] if mode in ("adv", "dis") else [d(20)]
    kept = max(dice) if mode == "adv" else min(dice)
    total = kept + mod
    margin = total - dc
    return {
        "dice": dice,
        "kept": kept,
        "total": total,
        "margin": margin,
        "outcome": tier_for(margin, kept),
    }


DICE_RE = re.compile(r"(\d*)d(\d+)([+-]\d+)?", re.IGNORECASE)


def roll_expr(expr: str) -> dict:
    match = DICE_RE.fullmatch(expr.replace(" ", ""))
    if not match:
        raise RollError(f"'{expr}' is not a dice expression (try 1d6, 2d6+1, d100)")
    count = int(match.group(1) or 1)
    sides = int(match.group(2))
    bonus = int(match.group(3) or 0)
    if not 1 <= count <= 50 or not 2 <= sides <= 1000:
        raise RollError("dice expression out of range (1-50 dice, 2-1000 sides)")
    dice = [d(sides) for _ in range(count)]
    return {"dice": dice, "bonus": bonus, "total": sum(dice) + bonus}


# ----------------------------------------------------------------- display


def signed(n: int) -> str:
    return f"+{n}" if n >= 0 else str(n)


def describe(entry: dict, reveal: bool = True) -> str:
    n = entry["n"]
    tags = ""
    if entry.get("hidden"):
        if not reveal:
            return f"#{n}  hidden roll ({entry['ts']})"
        tags += " [hidden]"
    if entry.get("reroll_of"):
        tags += f" [reroll of #{entry['reroll_of']}]"
    who = f" ({entry['who']})" if entry.get("who") else ""
    if entry["kind"] == "check":
        mode = {"adv": " adv", "dis": " dis"}.get(entry["mode"], "")
        dice = "/".join(str(x) for x in entry["dice"])
        kept = f" keep {entry['kept']}" if len(entry["dice"]) > 1 else ""
        line = (
            f"#{n}  CHECK {entry['skill']}{who}{tags}  d20{mode}={dice}{kept} "
            f"{signed(entry['mod'])} = {entry['total']} vs DC {entry['dc']}  "
            f"-> {entry['outcome']} (margin {signed(entry['margin'])})"
        )
        return line + f"\n     stakes: {entry['stakes']}"
    dice = "+".join(str(x) for x in entry["dice"])
    bonus = f" {signed(entry['bonus'])}" if entry.get("bonus") else ""
    return (
        f"#{n}  DICE {entry['expr']}{who}{tags}  [{dice}]{bonus} = {entry['total']}"
        f"\n     why: {entry['why']}"
    )


# ---------------------------------------------------------------- commands


def cmd_check(args) -> int:
    path = game_dir(args.game) / LOG_NAME
    entries = read_log(path)
    mode = "adv" if args.adv else "dis" if args.dis else "normal"
    entry = {
        "kind": "check",
        "who": args.who,
        "skill": args.skill,
        "mod": args.mod,
        "dc": args.dc,
        "mode": mode,
        "stakes": args.stakes.strip(),
        "hidden": bool(args.hidden),
    }
    if not entry["stakes"]:
        raise RollError("--stakes cannot be empty: say what success wins and what failure costs")
    if args.reroll_of is not None:
        original = next((e for e in entries if e["n"] == args.reroll_of), None)
        if original is None or original["kind"] != "check":
            raise RollError(f"#{args.reroll_of} is not a check in this game's log")
        if original.get("reroll_of"):
            raise RollError(f"#{args.reroll_of} is itself a reroll; a roll can be rerolled once")
        if any(e.get("reroll_of") == args.reroll_of for e in entries):
            raise RollError(f"#{args.reroll_of} has already been rerolled once")
        changed = [
            k for k in ("who", "skill", "mod", "dc", "mode") if entry[k] != original[k]
        ]
        if changed:
            raise RollError(
                "a reroll repeats the original roll exactly; these differ: " + ", ".join(changed)
            )
        entry["reroll_of"] = args.reroll_of
    entry.update(roll_check(args.mod, args.dc, mode))
    entry = append_entry(path, entries, entry)
    print(describe(entry))
    print(f"     {entry['outcome']}: {TIER_MEANING[entry['outcome']]}")
    return 0


def cmd_dice(args) -> int:
    path = game_dir(args.game) / LOG_NAME
    entries = read_log(path)
    why = args.why.strip()
    if not why:
        raise RollError("--why cannot be empty: say what this roll decides")
    entry = {
        "kind": "dice",
        "who": args.who,
        "expr": args.expr.replace(" ", "").lower(),
        "why": why,
        "hidden": bool(args.hidden),
    }
    entry.update(roll_expr(args.expr))
    entry = append_entry(path, entries, entry)
    print(describe(entry))
    return 0


def cmd_log(args) -> int:
    entries = read_log(game_dir(args.game) / LOG_NAME)
    if not entries:
        print("no rolls yet")
        return 0
    for entry in entries[-args.n :]:
        print(describe(entry, reveal=args.reveal))
    return 0


def cmd_verify(args) -> int:
    entries = read_log(game_dir(args.game) / LOG_NAME)
    problems = verify_entries(entries)
    if problems:
        print(f"rolls.log FAILED verification ({len(entries)} entries):")
        for problem in problems:
            print("  " + problem)
        return 1
    print(f"rolls.log ok: {len(entries)} rolls, chain intact")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Logged dice for the game table.")
    parser.add_argument("game", help="game folder name under games/")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="d20 + modifier against a difficulty")
    check.add_argument("--skill", required=True, help="skill or rating being tested")
    check.add_argument("--mod", required=True, type=int, help="total modifier, e.g. 3 or -1")
    check.add_argument("--dc", required=True, type=int, help="difficulty")
    check.add_argument("--stakes", required=True, help="what success wins and failure costs")
    check.add_argument("--who", default="PC", help="who is rolling (default: PC)")
    mode = check.add_mutually_exclusive_group()
    mode.add_argument("--adv", action="store_true", help="roll two d20, keep the higher")
    mode.add_argument("--dis", action="store_true", help="roll two d20, keep the lower")
    check.add_argument("--hidden", action="store_true", help="the player does not see the result")
    check.add_argument("--reroll-of", type=int, metavar="N", help="reroll of log entry N")
    check.set_defaults(func=cmd_check)

    dice = sub.add_parser("dice", help="plain dice, e.g. 2d6+1")
    dice.add_argument("expr", help="dice expression")
    dice.add_argument("--why", required=True, help="what this roll decides")
    dice.add_argument("--who", default="GM", help="who is rolling (default: GM)")
    dice.add_argument("--hidden", action="store_true", help="the player does not see the result")
    dice.set_defaults(func=cmd_dice)

    log = sub.add_parser("log", help="show recent rolls")
    log.add_argument("-n", type=int, default=10, help="how many (default 10)")
    log.add_argument("--reveal", action="store_true", help="show hidden rolls in full")
    log.set_defaults(func=cmd_log)

    verify = sub.add_parser("verify", help="check the log has not been edited")
    verify.set_defaults(func=cmd_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except RollError as exc:
        print(f"roll.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
