---
name: new-game
description: Start a new game with a session zero. Interviews the player, creates the game folder, builds the world and its secrets, makes the character, and opens the first scene. Use when the player wants to start, create or spin up a new game or campaign.
argument-hint: "[idea]"
---

# Session zero

The player's idea, if they gave one: `$ARGUMENTS`

The aim is a world with enough already decided that the player's later
cleverness has something real to push against. Paths are relative to the
game-master folder.

## 1. Talk it through

Find out, in conversation and without a long questionnaire (two rounds of
questions at most; if the player says "surprise me" about something, decide
it yourself):

- **Genre and premise.** Rulesets exist for `politics`, `fantasy` and
  `life-sim` (see `templates/genres/`); `custom` is a blank one for anything
  else. Offer two or three concrete pitches if they have no premise yet.
- **Who they play.** A position with something to lose and people who want
  things from them. Not the most powerful person in the setting.
- **Tone**, and anything to keep off-screen or out entirely.
- **Difficulty**, in concrete terms:
  - *Forgiving:* rivals make mistakes, resources are adequate, losses are
    recoverable.
  - *Standard:* rivals are competent, resources are tight, failure costs.
  - *Hard:* rivals are good and proactive, there is never enough of
    anything, lasting losses are common.
  - *Brutal:* all of that, and the position starts out bad.
- **What can be lost for good,** and what happens to the game if it is.
- **Pacing:** mostly scenes, mostly strategic turns, or mixed.
- **What kind of trouble they enjoy:** betrayal, impossible trade-offs,
  mysteries, slow-burn rivalries, logistics, moral weight.

## 2. Create the game

Pick a short kebab-case name with the player, then:

    python3 engine/game.py new <game> --genre <genre> --title "<Title>"

Fill in `games/<game>/game.md` from the conversation. Adapt
`games/<game>/rules.md` to the setting: rename skills, resources and offices
so they belong to this world, change the time unit if needed, and write out
the magic or technology limits if the genre has them. For `custom`, write
each section.

## 3. Build the world

Hand this to the `world-builder` subagent, so that the secrets are written
without passing through this chat. Give it the game's folder path and a
brief: everything agreed in step 1, the character concept so far, and any
names or facts already mentioned. If that subagent is not available in this
session, start a general-purpose subagent and tell it to follow
`.claude/agents/world-builder.md`.

It returns only what the character would know. Share that with the player as
the lay of the land. Then read `index.md` and `secrets/fronts.md` yourself.

## 4. Make the character

With the player:

- name, role, a line of description;
- skills, using the array in `rules.md`;
- starting resources and assets. At Standard difficulty, resource tracks
  start around the middle of their range, one step lower per difficulty level
  above that and one higher for Forgiving. Two or three assets;
- two ties to people in the index: one they can rely on, one that is
  complicated;
- a **trouble**: a flaw, debt, secret or entanglement that can be used
  against the character. This is where hard bargains come from;
- Fortune 2.

Write all of it to `state.md`, and add what the world knows about the
character to the relevant `secrets/` entries.

## 5. Open

Write the opening situation into "Scene in progress": a moment with a
decision in it and a clock already running, not a tour. Set session to 1. Run
`python3 engine/game.py load <game> --session ${CLAUDE_SESSION_ID}` (leave
`--session` off if that id was not filled in), then `/save` with the note
"session zero".

Then start: set the scene and stop at the first decision.
