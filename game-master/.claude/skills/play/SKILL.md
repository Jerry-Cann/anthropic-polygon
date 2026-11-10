---
name: play
description: Load a saved game from games/ and resume it where it stopped. Use when the player wants to play, continue or pick up a game ("/play ashfall", "let's continue the politics game"), and at the start of any chat before narrating anything.
argument-hint: "[game]"
---

# Resume a game

Game requested: `$ARGUMENTS`

A new chat knows nothing about the game except what is on disk. This loads
it. Paths are relative to the game-master folder.

1. **Pick the game.** If none was named, or the name does not match a
   folder, run `python3 engine/game.py list`, show the list, and ask which.

2. **Load it:**

       python3 engine/game.py load <game> --session ${CLAUDE_SESSION_ID}

   This marks the game as in play for this chat and prints the files to
   read, with anything that needs attention. If the session id above was not
   filled in (it still reads as a placeholder), leave `--session` off.

3. **Read everything it lists, in full, in one batch:** `game.md`,
   `rules.md`, `state.md`, `index.md`, `secrets/fronts.md`, and the last
   chronicle entry from the line number given.

4. **Read who is on stage.** For each person, faction and place named in
   the "Scene in progress" section of `state.md`, read its `world/` entry and
   its `secrets/` entry if it has one.

5. **Deal with warnings.** If the load reported unsaved changes, the last
   chat ended without a save: the files are still the truth, so carry on and
   save at the first scene break. If it reported that `rolls.log` does not
   verify, tell the player before anything else; do not roll until they have
   decided what to do about it. Fix other warnings quietly at the next save.

6. **Open the session** for the player, briefly:
   - a recap of a few sentences: where things stand and what was at stake
     when play stopped, from the chronicle entry and `state.md`. Only what the
     character knows.
   - the sheet at a glance: date, resources, conditions, Fortune, the open
     threads that are pressing.
   - then resume the scene exactly where "Scene in progress" left it, and
     stop at the character's decision.

   If `state.md` shows session 0 with no scene yet, the game was created but
   never started: finish session zero with `/new-game` instead.

From here the table rules in `CLAUDE.md` and the game's `rules.md` apply.
