# game-master

A table for long, narrative-heavy text games with real skill checks, run by
Claude Code. Each game is a folder of plain files, so a chat is disposable:
close it whenever it gets long, open a new one, and the game continues from
disk. Several games can sit side by side for months.

Built for strategy and politics first, with rulesets for fantasy adventure
and life sim, and a blank one for anything else.

## Start playing

Needs Claude Code and Python 3 (no packages to install).

```
cd game-master
claude
```

Accept the trust prompt the first time; the project's settings (dice
permissions, hooks, status line) only apply after that. Then:

| Type | To |
|---|---|
| `/new-game` | Start a game. A short conversation about what you want, then the world is built and the first scene opens. You can add your idea: `/new-game a succession crisis in a river kingdom`. |
| `/play saltmarsh` | Resume a game in a fresh chat. `/play` alone lists your games. |
| `/save` | Checkpoint now. The GM also does this by itself at scene breaks. |
| `/wrap` | End the session: writes the chronicle entry, tidies, saves. Then close the chat. |

During play, just say what your character does. Put anything out of character
in double parentheses: `((can you remind me who Oren is?))`.

To switch games, `/wrap`, then start a new chat and `/play` the other one.

## What keeps it a game

The rules the GM follows are in [`CLAUDE.md`](CLAUDE.md), and they are worth a
read, since you can change any of them. The short version:

- **Dice are rolled by a script, never by the GM or by you.** Every roll is
  appended to the game's `rolls.log` before its result is shown, with the
  difficulty and the stakes written down first. The log is hash-chained, so
  an edited or deleted roll is detected.
- **Stakes before the roll.** You hear the skill, the difficulty, what
  success gets and what failure costs, and may change your approach or back
  out once. After that the result stands and the same approach cannot be
  retried.
- **The world's facts are fixed before you test them.** What each person and
  faction wants, fears and will never accept is written in `secrets/` when
  they are created. An argument works when it hits something written there,
  not because it was argued well.
- **Good ideas change the situation,** by removing the need to roll, lowering
  the difficulty, granting advantage, or improving the stakes. They do not
  change what is true.
- **Failure costs something on the sheet,** and loss up to the limit you set
  in session zero is possible.
- **The world moves without you.** Factions and people advance their own
  plans every turn, rolled for out of your sight, by a subagent that reads
  only the game files and never sees the chat.
- **Fortune points** (2, at most 3) buy a reroll or a flashback to something
  your character plausibly prepared. They come back when things go badly.

Check the dice any time:

```
python3 engine/roll.py saltmarsh log -n 20     # recent rolls (hidden ones masked)
python3 engine/roll.py saltmarsh verify        # has the log been touched?
```

## A game on disk

```
games/saltmarsh/
  game.md           premise, tone, difficulty, house rules
  rules.md          this game's ruleset (a copy you can change)
  state.md          now: scene in progress, character sheet, resources, clocks, open threads
  index.md          one line per person, faction, place, thing
  world/            what your character knows about each of them
  chronicle.md      a summary of every session
  rolls.log         every roll
  secrets/          GM only: the truth, hidden clocks, what is coming
```

Everything outside `secrets/` is yours to read and is spoiler-free: it holds
only what your character knows. Stay out of `secrets/`; nothing stops you
except that it would spoil your own game. Tool calls that touch those files
show up collapsed in the chat, so do not expand them either.

Each save is a git commit of that game's folder, so a damaged file can be
rolled back with ordinary git. That is for repairing state, not for undoing
a bad roll.

## Long games and fresh chats

A game outgrows any single chat, so the chat is never the save file.

- At the start of a session the GM reads five small files (`game.md`,
  `rules.md`, `state.md`, `index.md`, `secrets/fronts.md`) plus the last
  chronicle entry. People and places are read when they come on stage.
- The files are updated as play goes and checkpointed at scene breaks.
- The status line shows the game, the in-game date and how full the chat is.
  When the chat gets long (about 120k tokens or half the window, whichever
  comes first) the GM is told, and will offer to `/wrap` at the next scene
  break. A new chat with `/play` picks up from the files.
- If a chat does get compacted before you wrap, a hook tells the summariser
  what to keep and then points the GM back at the files.

## Settings you may want to change

- **Model.** [`.claude/settings.json`](.claude/settings.json) sets `sonnet`
  for sessions started in this folder; delete that line to use your usual
  default, or switch with `/model`. The two subagents (`world-builder`,
  `world-turn`) run on Sonnet at high effort, set in
  [`.claude/agents/`](.claude/agents).
- **Status line.** The project sets its own, which replaces a personal one
  while you are in this folder. Delete the `statusLine` block to get yours
  back; the long-chat warning then stops working, nothing else does.
- **Thresholds** for the save reminder and the long-chat warning are
  constants at the top of [`engine/game.py`](engine/game.py).
- **Rulesets.** [`templates/genres/`](templates/genres) holds the starting
  ruleset for each genre. Editing one changes future games only; each game
  keeps its own copy in `rules.md`.
- **Table rules.** [`CLAUDE.md`](CLAUDE.md) applies to every game. A rule you
  want for one game only goes under House rules in that game's `game.md`.

On Windows, if `python3` is not a command, change it to `python` in
`.claude/settings.json`.

## Playing from the Claude app (cloud sessions)

It works, with two differences from a laptop:

- A cloud session starts at the repository root, so this folder's
  `.claude/settings.json` (hooks, status line) is not read. Start with
  something like "play saltmarsh in game-master"; the rules and skills load
  when the GM opens the folder. Saving then relies on the GM's habits alone,
  without the reminders.
- Saves are commits, and a cloud session pushes to its own branch. Merge
  that branch into `main` before starting another session, or the new one
  will not see the latest save.

## What this does not do

- It cannot stop you reading `secrets/`.
- It cannot make the GM infallible. The structure removes the easy ways to go
  soft; if a ruling still seems off, question it once, and if a pattern
  shows up, tighten `CLAUDE.md`.
- State is kept in Markdown by the GM, not computed by code. Each save runs
  a consistency check on the folder, which catches missing files and broken
  links, not a mis-added treasury.

## Development

```
python3 engine/test_engine.py
```

runs the tests for the dice, the save commands and the hooks.

```
CLAUDE.md             table rules for the GM, all games
.claude/settings.json permissions, hooks, status line, model
.claude/skills/       /new-game, /play, /save, /wrap
.claude/agents/       world-builder, world-turn
engine/roll.py        dice and the roll log
engine/game.py        new, list, load, check, save; hook and status line handlers
templates/game/       skeleton of a game folder
templates/genres/     politics, fantasy, life-sim, custom
games/                your games
```
