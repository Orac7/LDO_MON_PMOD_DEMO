# Wave 2 — adversarial verification

Your job is to REFUTE, not to confirm. Each claim below was produced by a Wave 1
reviewer. Assume it is wrong until the primary evidence forces you to accept it.
A refuted claim is a SUCCESS, not a failure — a false positive in a hardware
review costs the owner a redesign cycle.

Repo: /Users/sam.hutchings/Workspace/github.com/Orac7/LDO_MON_PMOD_DEMO
Read CLAUDE_REVIEW/raw/AGENT_BRIEF.md for the artefact and datasheet inventory.
Read CLAUDE_REVIEW/raw/DESIGN_INTENT.md — owner-stated intent is authoritative.

## Method
- Go back to PRIMARY evidence every time: the datasheet page, the .kicad_pcb
  geometry, the actual file bytes. Do NOT trust the Wave 1 report's own quotations
  or page numbers — re-read the cited page and check it says what is claimed.
- Re-derive every number independently. If you get a different answer, say so.
- Check the claim's *reasoning*, not just its conclusion. A right answer reached
  by wrong reasoning is unreliable and must be downgraded.
- Watch specifically for: numbers quoted from a SIBLING part in a family datasheet;
  terminology from the wrong protocol/standard; values read off a figure that
  shows a different configuration; "requirement" language applied to what is
  actually a recommendation, or vice versa.

## Verdict for each claim (use these words exactly)
- CONFIRMED  — primary evidence proves it; cite page/line/coordinate
- PLAUSIBLE  — likely true, but the decisive evidence is not available
- WEAKENED   — real but less severe, or correct for the wrong reason; explain
- REFUTED    — demonstrably false; show why, and say what misled the reviewer

Also give: corrected severity (Blocker/Should-fix/Nice-to-have) and your own
confidence. If you refute a claim, check whether a DIFFERENT real issue is hiding
nearby — reviewers often misdescribe something that is genuinely wrong.
