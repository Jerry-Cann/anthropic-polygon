---
name: wrap
description: End a play session cleanly so the game can continue in a fresh chat. Writes the chronicle entry, tidies the state and saves. Use when the player is done for now, wants to switch games, or when the chat has grown long and a scene has just ended.
---

# End the session

The next session will start cold, from the files alone. This leaves them in
the best state for that. Ending at a scene break is better than mid-scene; if
the player wants to stop mid-scene, that works too, and "Scene in progress"
carries it.

1. **Do everything in `/save` steps 1 and 2** so the files match the present.

2. **Add a chronicle entry** at the end of `chronicle.md`, following the
   format in the comment at the top of that file. Raise the session number in
   `state.md` to match. Write it for a reader who was not here: events in
   order, the decisions the player made and what they cost or won, how
   relationships moved, the rolls that turned things (by log number), and what
   was left hanging. Only what the character knows; things that happened out
   of sight go in `secrets/`.

3. **Tidy the hot files.**
   - `state.md`: resolved threads out, stale detail out, under its budget.
   - `secrets/fronts.md`: clocks current, finished fronts retired, and
     "Coming up" stocked with what is already decided for the next stretch of
     game time, so the next session's events are fixed before the player acts
     on them.
   - `index.md`: every line still true.

4. **Snapshot** with `python3 engine/game.py save <game> -m "session N: <title>"`,
   and push if this session runs in a cloud container.

5. **Sign off** to the player:
   - two or three lines on where things stand, in the story's voice;
   - that the game is saved and this chat can be closed;
   - that `/play <game>` in a new chat picks it up.

Do not continue the story after wrapping unless the player asks to. If they
do, that is their call: carry on as normal and save again at the next break.
