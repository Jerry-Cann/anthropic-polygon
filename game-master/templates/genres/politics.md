# Rules: strategy and politics

The ruleset for this game. It builds on the table rules in the project's
`CLAUDE.md` (checks, difficulty ladder, outcome tiers, Fortune, clocks,
conditions) and adds what a game about power needs. Rename skills, resources
and offices to fit the setting during session zero; record later changes under
House rules in `game.md`.

The challenge in this genre comes from scarcity and opposition, not from high
difficulty numbers: there is never enough time, money or goodwill for
everything, and every other player at the table of power is also making moves.

## Skills

Rated 0 to 5. A new character assigns 4, 3, 2, 2, 1, 1, 0, 0.

| Skill | Covers |
|---|---|
| Rhetoric | Speeches, public argument, moving a room or a crowd |
| Negotiation | Private deals, bargaining, finding the price |
| Intrigue | Secrets, spies, deception, noticing a plot |
| Insight | Reading a person: what they want, whether they are lying |
| Command | Leading soldiers or staff, crisis decisions, being obeyed |
| Stewardship | Money, logistics, administration, making things run |
| Law and Lore | Procedure, precedent, history, what is permitted and by whom |
| Presence | Composure, intimidation, charm, holding the centre of attention |

Opposition is usually a person or a bloc: difficulty is 10 plus their relevant
rating, shifted by who holds the advantage in the situation.

## Resources

Small numbers on purpose, so that each point is a decision.

- **Treasury** (0 to 10): liquid wealth in abstract units. One unit is a
  meaningful sum: a bribe that turns a mid-ranking official, a month of a
  mercenary company, a public festival. At 0 nothing that costs money can be
  attempted and upkeep starts failing.
- **Influence** (0 to 10): political capital, the willingness of people to do
  things because the character asks. Spent to call a vote, force an
  appointment, bury a report, get a meeting that would otherwise be refused.
  Regained by delivering for others and by visible wins.
- **Standing** (0 to 10): how secure the character's position is. It is not
  spent; it moves with events. At 3 or below rivals move openly. At 0 the
  position is lost (see Losing).
- **Favours**: specific and named, not a number. "Magistrate Oren owes one
  large favour for the buried inquiry." Calling one in gets the thing without
  a roll if it is within that person's power and proportionate; then it is gone.
- **Debts**: the same, in the other direction. People collect at bad moments.

## Assets

Offices, holdings, agents and allies are written as capabilities, one line
each, not as bonuses to stack. "Spymaster Ilse: runs one operation a week in
the capital without using an action; her reports are reliable about the court
and guesswork about the provinces." An asset can be lost, turned, or tied up.

Delegating to an agent means the agent rolls with their own rating, the
character is not there to adjust, and the agent's interests colour the result.

## Time: the week

The strategic turn is one week (change the unit to fit the setting: a day
during a crisis, a month in a slow dynasty game).

Each week the character has **three actions**. An action is anything that
takes real time and attention: a negotiation, an investigation, a journey, a
public appearance, preparing a vote, running an operation personally. Short
conversations with people already at hand do not cost an action; they cannot
by themselves achieve what an action achieves.

1. **Brief.** The GM says what the character knows this morning: reports,
   rumours with their source, demands from others, what is due this week.
2. **Actions.** Played as scenes when the outcome is uncertain and
   interesting, as a few lines when it is not. The character may hold an
   action in reserve to react during the world turn.
3. **World turn.** Everyone else moves (below).
4. **Accounts.** Upkeep is paid, clocks and resources are updated, state is
   saved.

Zoom in freely: a single dinner can take a whole session if that is where the
game is. The three-action limit is what makes it a choice.

## The world turn

Run after the character's actions each week, by the `world-turn` subagent or
by the GM following the same steps. It works from the files, so `state.md`
must be current first.

1. **Factions act.** Every faction with a live agenda takes one action toward
   it, chosen from its own goals and what it knows, not from what would make a
   good scene for the character. Roll its rating against the opposition
   (hidden roll, `--who` the faction). SUCCESS ticks its clock once, CRITICAL
   twice, PARTIAL once with exposure (someone could notice), FAILURE nothing,
   DISASTER a setback that costs it something. Factions act against each
   other, not only against the character.
2. **People act.** Named individuals with their own agendas do the same when
   they have a reason to: a rival courts the character's ally, a creditor
   loses patience, a friend gets into trouble.
3. **Event.** Roll 1d20 for the realm. 1 to 3: a crisis nobody planned (bad
   harvest, riot, death, scandal). 4 to 8: a complication for whoever is
   currently strongest. 9 to 16: nothing beyond what the factions did. 17 to
   19: an opening (a vacancy, a quarrel among rivals, a windfall) that goes to
   whoever moves first. 20: something that changes the map.
4. **Reactions to the character.** Whatever the character did in public this
   week has been noticed. Those it threatens respond in proportion.
5. **What reaches the character.** Decide what they learn and through whom.
   Good sources report accurately and late; rumour is early and wrong in one
   detail. A character with no eyes somewhere learns nothing from there until
   it becomes public.

## Factions

Each faction has an entry in `world/` (what is publicly known) and one in
`secrets/` (the truth). The secret entry carries:

- **Ratings** 0 to 5 in Force, Wealth, Sway and Secrets.
- **Agenda:** what it is trying to do now, as a clock.
- **Wants / fears / will never accept.**
- **Fault line:** the internal split that could be widened.
- **Disposition** toward the character, from -3 to +3, with the reason.
- **Knows:** what it knows about the character and their plans.

## Votes, councils and counts

When a decision is made by a body, list its blocs with the number of voices
each and their lean: for, against, or open with what would move them. The
character's actions before the vote change leans one bloc at a time. On the
day, committed blocs vote their lean; each open bloc rolls its own check on
the strength of what it was last offered or threatened with. A whip count is
an Intrigue or Insight check and can be wrong.

## Mass conflict

Battles, riots and sieges are resolved as a clock per side (first to fill
wins), each round one Command check for the character's side with the stakes
stated: what this push gains and what it risks. Numbers, ground, supply and
surprise set the difficulty and who has advantage. Named people in the fight
are at risk on FAILURE or worse.

## Losing

Standing at 0, or a decisive defeat, removes the character from their
position: deposed, arrested, exiled, discredited. What that means for the
game is set under Dials in `game.md`; by default play continues from the new
circumstances, with what the character still has.

Short of that, the usual costs of failure here are: a point of Standing or
Influence, a favour burned, an ally cooled, a rival's clock ticking, a secret
exposed, an action wasted, a door closed for good.

## Advancement

At the end of a chapter (a crisis resolved one way or the other) raise one
skill by 1, to a maximum of 5, and restore Fortune to 2 if it is lower. Most
growth in this genre is not on the sheet: it is offices held, people owed and
enemies made.
