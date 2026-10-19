# Design intent stated by the board owner

Statements here come from the designer and are AUTHORITATIVE. Do not report them
as defects. You may still report *residual* risk that survives the stated intent.

## DI-1: JP1 / JP2 / JP3 are configured by hand before use
The three 3-pole solder jumpers are intended to be solder-blobbed as appropriate
by the user before the board is put into service. They ship open deliberately.

Therefore:
- "The MAX6373 SET0/SET1/SET2 pins float on an as-manufactured board" is NOT a
  design error. Do not raise it as one.
- Still in scope, if and only if it is real and specific:
  - whether the board is DISCOVERABLE enough to be configured correctly: silkscreen,
    labelling, documentation, and whether a user can tell JP1 from JP2 from JP3 and
    which way round to bridge each one;
  - whether a WRONG or PARTIAL blob produces a silent/confusing failure rather than
    an obvious one (e.g. a strapping that makes the board appear dead);
  - whether the assembly/manufacturing data is consistent with this intent;
  - whether the solder-jumper footprint chosen is actually blobbable by hand.

# Review preferences stated by the board owner

## RP-1: non-obvious load-bearing values must be annotated on the schematic
Where a component value is constrained by something not visible on the sheet, the
remedy is a **schematic text note next to the part**, not just a line in a review
report. Raise these as actionable findings with suggested wording.

Known instance: **R18 = 1k**. It looks like a casual pull-up and is not: Q1's 4k7
base path loads ENABLE, so the obvious "tidy-up" to 10k leaves only ~0.2 V margin
to the LT3074's 1.32 V ENABLE threshold. Nothing on the schematic says so, which
makes it a live trap for a future editor (including a future automated tidy-up).

Suggested note wording, to sit beside R18:
    R18 = 1k is load-bearing. Q1 (4k7 base path) loads ENABLE; do not raise this
    value. At 10k the ENABLE high level falls to ~0.2 V above the LT3074 1.32 V
    threshold. Recompute the divider against U1/U2 ENABLE Vih before changing.

Apply the same treatment to any other value Wave 1 found to be constrained by a
non-local interaction: if changing it quietly breaks something, it needs a note.
