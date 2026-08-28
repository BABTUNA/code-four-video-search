# Loom script (~4 min)

Prep: run both queries once beforehand so models are warm (the first run pays
~20s of loading). Have the terminal and README section 6 ready.

## 0:00 - The idea (30s)

"Searching hours of bodycam video fails at *finding* moments, not recognizing
them. So this system has cheap local indexes propose candidates, and a
vision-language model inspects only the finalists - where it's allowed to say
no. Timestamps always come from the system's own bookkeeping, never from a
model's memory."

## 0:30 - Two live queries (90s)

```
uv run c4 search "officer orders the driver to step out of the vehicle"
```
Point at: the CONFIRMED tier, transcript quotes with speaker roles, the
wall-clock label read off the burned-in overlay.

```
uv run c4 search "a gunshot is fired"
```
Point at: no confident match, plus the closest rejected candidate and the
verifier's stated reason. Line: "in evidence review, a confident empty answer
beats a confident wrong one."

## 2:00 - The numbers (90s)

README section 6 table on screen:
- "Each row is one config file - that's the hotswappability story."
- "Captions were the biggest single win, for ninety cents across the corpus."
- "Verification refuses all six trap queries that every unverified config
  answered with confident nonsense."
- "The eval caught my own labels being wrong twice - an unlabeled second
  vehicle fire the system outranked, and two labels that flipped when the
  corpus doubled. That's how I know the harness is real."

## 3:30 - Limits (30s)

"Honest limits: the label method is biased toward text-answerable queries,
one false abstain remains, and prosody queries are unlabeled on purpose -
auditing them requires listening. The README has the full architecture,
research grounding, failure taxonomy, and every rejected label."
