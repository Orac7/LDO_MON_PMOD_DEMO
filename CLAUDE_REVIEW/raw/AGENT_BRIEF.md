# Shared brief for Wave 1 reviewers

Repo root: /Users/sam.hutchings/Workspace/github.com/Orac7/LDO_MON_PMOD_DEMO
Design:    LDO_MON_PMOD_Board_V1/LDO_MON_PMOD_Board_V1.kicad_sch  (and .kicad_pcb)

The board is a PMOD-form-factor LDO monitor/demo: two LT3074 LDOs (U1,U2) whose
outputs are measured by a PAC1944 4-channel power monitor (U5), with a MAX6373
watchdog (U3), a 74LVC1G175 D flip-flop (U4), a 74LVC1G08 AND gate (U6), an
AD5272 digital potentiometer (U7), a PCA9306 I2C level translator (U8) and an
MMBT3904 (Q1). Host interface is the PMOD connector P1.

## Pre-computed ground truth (READ THESE FIRST, do not re-derive)
CLAUDE_REVIEW/raw/components.tsv   118 components: ref, value, footprint, lib, desc
CLAUDE_REVIEW/raw/nets.tsv         65 nets: every net with its full node list, pin function and pin type
CLAUDE_REVIEW/raw/net_summary.md   floating nets, multi-driver nets, pin-type census
CLAUDE_REVIEW/raw/erc_strict.rpt   ERC with ALL rules enabled
CLAUDE_REVIEW/raw/drc_strict.rpt   DRC with all rules enabled and exclusions cleared
CLAUDE_REVIEW/raw/netlist.net      full KiCad s-expr netlist

## Datasheets (CLAUDE_REVIEW/datasheets/, read with the Read tool, `pages` param)
LT3074_LDO.pdf  MAX6373_watchdog.pdf  PAC1944_power_monitor.pdf  AD5272_digipot.pdf
PCA9306_lvl_translator.pdf  74LVC1G175_dff.pdf  74LVC1G08_and.pdf

## Rules
- READ ONLY. Never modify anything in LDO_MON_PMOD_Board_V1/.
- Ground every claim in a specific net name, refdes+pin, or datasheet page. No generic advice.
- Already known, do NOT re-report: 0 unconnected pads; 0 netlist parity issues; 6 ERC
  rules set to `ignore`; 9 DRC exclusions; C9/C13 polarised symbol on non-polarised
  footprint; `GPIO` global label appears once; U1.6/U2.6 PG unconnected.
  You MAY add new analysis of those items, but don't just restate them.
- Distinguish what you VERIFIED against a datasheet from what you INFER. Say which.
- A clean result is a valuable result. Report "checked X, correct" explicitly.

## Output format
Write your report to the file named in your individual brief, as markdown:

### Checks performed
A table: | Check | Method (tool/parse/judgement) | Result | Notes |
Include checks that came back clean, and checks you could NOT do, with the reason.

### Findings
For each, a block:
    #### F-<AREA>-<n>: <one line title>
    - Severity: Blocker | Should-fix | Nice-to-have
    - Confidence: High | Medium | Low
    - Where: <refdes / net / file:line>
    - Evidence: <datasheet page, net node list, or report line that proves it>
    - Why it matters: <concrete failure mode, not a generality>
    - Suggested fix: <specific>
Order findings most severe first. If you find nothing, say so plainly.
