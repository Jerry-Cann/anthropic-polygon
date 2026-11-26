# Rules: fantasy adventure

The ruleset for this game. It builds on the table rules in the project's
`CLAUDE.md` (checks, difficulty ladder, outcome tiers, Fortune, clocks,
conditions) and adds what a game of travel, danger and discovery needs.
Rename and reshape during session zero to fit the setting; record later
changes under House rules in `game.md`.

The challenge here comes from attrition and commitment: wounds, supplies and
daylight run down, and going deeper is a choice made without knowing
everything that is ahead.

## Skills

Rated 0 to 5. A new character assigns 4, 3, 2, 2, 1, 1, 0, 0.

| Skill | Covers |
|---|---|
| Might | Force, endurance, heavy weapons, breaking and carrying |
| Finesse | Speed, balance, light weapons, locks, sleight of hand |
| Stealth | Going unseen and unheard, ambush, tailing |
| Wits | Noticing, searching, working out what happened here |
| Lore | History, creatures, languages, how magic is supposed to work |
| Survival | Travel, weather, tracking, foraging, treating wounds |
| Presence | Persuading, deceiving, intimidating, reading people |
| Craft | The character's art: spellcasting, alchemy, artifice, prayer. Rename it. |

If the setting has no magic for the character, replace Craft with a trade or
split Presence in two.

## Harm

No hit points. Harm is a track of three wounds plus conditions.

- **Wounds** (0 to 3). One wound: hurt, no penalty. Two: disadvantage on
  physical checks. Three: down, and out of the fight; without help the
  character is dying. A fourth wound kills, if `game.md` allows death.
- Wounds heal one per week of rest, or one per day under real care. Not
  overnight.
- **Conditions** (table rules) cover everything else: Exhausted, Poisoned,
  Frightened, Cursed, Hunted. Each names what it hinders and what clears it.

## Supplies and gear

- **Supplies** (0 to 6): food, water, light, rope, bandages, as one number.
  Tick one per day of travel or delve, and one when a PARTIAL or FAILURE is
  paid for in kit. At 0: Exhausted, then wounds.
- **Coin** (0 to 10): abstract. One unit buys a good horse or a week of
  comfortable living for a party.
- **Gear:** up to six significant items, each one line saying what it allows.
  A sword does not add a number; having one is why fighting an armed man is a
  check at all and not a foregone conclusion.

## Magic

Define during session zero what magic can and cannot do in this world, and
write it here. The default: a working is a Craft check; difficulty by how far
it bends the world (a light 8, a locked door 12, a man's mind 18); the cost
lands on PARTIAL or worse and is one of strain (a condition), attention
(something notices), or price (a clock ticks). Magic does not skip a problem
for free: it trades one risk for another.

## Time and travel

The day has four watches: morning, afternoon, evening, night. A watch is
enough for one significant thing: a leg of travel, a search, a negotiation, a
rest. Travelling or working through the night costs Exhausted.

Each leg of a journey through dangerous country, roll 1d20: 1 to 4 a hazard
or hostile meeting, 5 to 8 a sign of something (tracks, smoke, a body), 9 to
17 nothing, 18 to 20 a find or a friendly meeting. What exactly is rolled or
chosen from the region's entry in `secrets/`.

## Fights

A fight is not blow by blow. Each exchange, the player says what the
character is trying to achieve and how; the GM states difficulty and stakes;
one check resolves the exchange.

- Opponents have **Threat** (the difficulty to act against them directly: 10
  for a guard, 13 for a veteran, 16 for a knight or a troll, 20 for something
  that should not be fought head-on) and **Resolve** (how many successful
  exchanges until they are beaten, flee or yield: 1 for most, 2 to 3 for a
  serious foe, a clock for a monster).
- SUCCESS takes one Resolve or achieves the stated aim. CRITICAL does both or
  ends it. PARTIAL does it and the character pays: a wound, a lost position, a
  broken item. FAILURE: the opponent gets what they were trying for, usually a
  wound. DISASTER: that and something worse.
- Being outnumbered is disadvantage, or simply raises the stakes. Ground,
  surprise and preparation shift difficulty a step. Most opponents want
  something other than a fight to the death; they run, bargain and surrender.
- Avoiding, escaping or ending a fight by other means is always on the table
  and often the smart play.

## The world turn

Run at each rest, each day of downtime and each time the character leaves a
place for more than a day; by the `world-turn` subagent or by the GM
following the same steps.

1. **Fronts advance.** Each hidden clock in `secrets/fronts.md` whose driver
   was not hindered ticks, or rolls to tick if opposed.
2. **Places change.** Anywhere the character disturbed reacts: guards
   doubled, a lair abandoned, a village emptied, a rival party moving in.
3. **People act.** Named people pursue their own aims: the patron grows
   impatient, the rival reaches the next site first, the rescued man talks.
4. **Signs.** Decide what trace of all this the character could notice, and
   where.

## Losing

Set under Dials in `game.md`. By default the character can die, and can also
lose in other ways: captured, cursed, too late. Failure on the road usually
costs wounds, supplies, time (a front ticks), position, or something carried.

## Advancement

At the end of a chapter (a site resolved, a journey completed, a foe dealt
with) raise one skill by 1, to a maximum of 5, and restore Fortune to 2 if it
is lower. Gear, allies and knowledge of the world are the faster road to
power.
