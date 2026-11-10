---
name: save
description: Checkpoint the game in play by bringing its files up to date and snapshotting them. Use at every scene break, before a world turn, before anything risky to the save, whenever a context note says the last checkpoint was a while ago, and when the player asks to save.
argument-hint: "[short note]"
---

# Checkpoint

Note from the player, if any: `$ARGUMENTS`

A save is only as good as the files. The goal is that a different chat,
reading only the files, could continue this scene without the player
noticing the join.

1. **Bring `state.md` up to now:** date and place; "Scene in progress"
   rewritten for this exact moment (who is present, what was just said, what
   the player is deciding); resources, conditions, Fortune; visible clocks;
   open threads added and resolved ones removed.

2. **Write down everything else that changed since the last save:**
   - new people, factions, places, things: a line in `index.md`, a `world/`
     file if they will return, a `secrets/` file if they have an agenda;
   - what the character learned: into the `world/` entry;
   - what changed out of sight: into `secrets/` entries and
     `secrets/fronts.md` (hidden clocks, clues handed out);
   - changed standing with anyone: their `index.md` line.

   Go back over the turns since the last save and look for the easily lost
   things: a name coined in passing, a sum agreed, a promise, a lie and who
   heard it, a deadline.

3. **Snapshot:**

       python3 engine/game.py save <game> -m "<one line: what happened since the last save>"

   Fix anything it reports as an error. For a file over its line budget,
   move detail out to where it belongs and run it again.

4. If this session runs in a cloud container, push, following the session's
   git instructions.

5. Tell the player in one short line that the game is saved, then carry on.
   A save is not a pause in the story.
