# Wave 2 — adversarial verification of `wave1_layout.md`

All geometry below was re-derived from `LDO_MON_PMOD_Board_V1/LDO_MON_PMOD_Board_V1.kicad_pcb` with my own shapely scripts, written without reusing Wave 1's `05_plane_return_path.py` / `06_pcb_geometry.py` logic. Datasheet text was re-extracted with `pdftotext`, not read off a rendered page image. Scratch scripts: `/private/tmp/claude-502/.../scratchpad/w2.py … wB.py`.

## 0. Two preliminaries that the brief asked about, settled first

**0a. Are the zone fills present and current?** Yes, in both senses, so zone-based conclusions are reliable in *both* directions.
- The file contains 20 `zone` blocks and 22 `filled_polygon` blocks. The In1/In4 GND zone is a single zone spanning two layers (`(layers "In1.Cu" "In4.Cu")`) and emits three fills: `In1.Cu` 1314.40 mm², `In4.Cu` 1264.66 mm², `In4.Cu` 5.08 mm².
- I re-plotted with `kicad-cli pcb export gerbers --check-zones` (which refills before plotting) and compared against the released Gerbers: `In4_Cu` 5380 vs 5380 non-comment lines, `B_Cu` 1649 vs 1649, `F_Cu` 2694 vs 2697 (the 3-line delta is the aperture/block-ordering artefact Wave 1 already documented). **The stored fills are not stale.**

**0b. Did Wave 1's scripts ignore `filled_polygon`?** No — the brief's hypothesis is wrong. Both `05` and `06` parse `filled_polygon` and build shapely polygons from them (`05` lines 33–47, `06` lines 39–47), and `06`'s via-landing test checks zone intersection, track endpoints *and* pads. The alleged false-negative mechanism is not what produced CLAIM A. The scripts do have other defects, listed under CLAIM B.

---

## CLAIM A — OUT e-pad vias land copper on one layer only

**Verdict: CONFIRMED** (core geometry), with two factual corrections and a severity note.
**Corrected severity: Should-fix. Confidence: High on geometry, Medium on the thermal consequence.**

### What I reproduced independently
My own landing test — a via lands on layer *L* if its pad disc (r = size/2) has >1e-6 mm² of intersection with the union of (zone fills ∪ buffered tracks ∪ pad outlines) of the same net on *L*:

```
full 174-via census, layers-landed histogram: {1: 4, 2: 91, 3: 69, 4: 10}
  (129.4,98.9)  OUT_1  lands=['F.Cu']
  (129.4,98.1)  OUT_1  lands=['F.Cu']
  (129.4,107.1) OUT_2  lands=['F.Cu']
  (129.4,107.9) OUT_2  lands=['F.Cu']
```
Those four, and only those four, land on one layer. The IN e-pad contrast is also confirmed: all eight `SENSE_4_N` vias at (127.6/128.3, 98.1/98.9/107.1/107.9) land `['F.Cu','In3.Cu']`, and the In3 `SENSE_4_N` fill is 1287.58 mm². Wave 1's numbers match mine to the digit.

Detail Wave 1 missed that makes the picture slightly worse: the vias do not even touch the F.Cu OUT pour. The `OUT_2` F.Cu fill starts at x = 129.700; the via disc at x = 129.4 r = 0.3 reaches x = 129.700 exactly — tangent, zero area. The vias land on **pad U1.24/U2.24 only**, and the pad is what bridges to the pour (pad spans x 128.92–129.85, overlapping the fill by 0.15 mm).

### Correction 1 — the "no OUT copper anywhere but F.Cu" statement is false
Wave 1: *"There is no `OUT_1`/`OUT_2` copper on In1, In2, In3, In4 or B.Cu anywhere on the board."* Measured per-layer conductor area (zones + tracks + pads):

| net | F.Cu | B.Cu | In1–In4 |
|---|---|---|---|
| OUT_1 | 28.45 mm² | **0.43 mm²** | 0 |
| OUT_2 | 19.66 mm² | **1.17 mm²** | 0 |

Both OUT nets already have B.Cu copper and an existing F↔B transition: `OUT_1` via at (138.0, 104.85) feeding B.Cu track to R28.2; `OUT_2` via at (135.15, 109.01) feeding B.Cu track to R29.2 and C15.1. Wave 1 measured *zone* copper and reported it as *all* copper. The conclusion is unaffected (that copper is 7–9 mm east of the e-pad) but the statement as written is wrong, and it matters for the fix: a B.Cu OUT pour is not a new concept on this board, it is an extension of routing that already exists.

### Correction 2 — the datasheet quote is accurate; the severity framing is not
I re-extracted p.41 (`pdftotext -f 41 -l 41`). The text is verbatim what Wave 1 quoted:

> "The IN and OUT pins at the bottom of the package should be soldered to IN and OUT planes accordingly. In addition, the IN and OUT must be connected to large copper layers below with thermal vias; these layers spread heat dissipated by the LT3074."

So this is **requirement language ("must")**, but it sits inside an Applications-Information paragraph opening *"For higher ambient temperatures, care should be taken…"*. It is a layout recommendation for high-ambient operation, not a functional or absolute-maximum requirement. θJCBOT = 3.5 °C/W and θJCTOP = 47 °C/W are confirmed from Table 3 (document p.10). The worked example on p.42 is 3 A at 300 mV dropout → PDISS = 0.925 W, θJA 33 °C/W, ΔTJ = 30.5 °C — on ADI's own demo board.

**The Wave 2 brief calls this an "alleged Blocker". Wave 1 did not rate it a Blocker — F-LAY-1 is `Severity: Should-fix`, and in fact no finding in `wave1_layout.md` is rated Blocker.** I agree with Should-fix, not Blocker, for one additional reason Wave 1 did not account for: the OUT e-pad's 28.45 mm² / 19.66 mm² of F.Cu sits over 0.100 mm of prepreg above the full In1 GND plane, giving a spreading path of roughly `t/(k·A)` = 1e-4/(0.3 × 28e-6) ≈ 12 °C/W into In1 even with no vias at all. The OUT half of the heat path is degraded, not absent.

### Residual real issue hiding nearby
The four dead vias punch 0.25 mm barrels with anti-pads through In1 (GND), In2 (3V3), In3 (VIN) and In4 (GND) directly beside the hottest part, for zero benefit, and they are unplugged inside a solder-paste aperture (Wave 1's F-LAY-9). If the owner does not want to add a B.Cu OUT pour, **deleting the four vias is strictly better than leaving them**, and Wave 1 ranked that option second. I would rank it first-equal.

---

## CLAIM B — I²C on In4 splits the GND plane, 18 B.Cu segments cross the slots, ALERT_N ×7 including 3.10 mm at U2

**Verdict: WEAKENED — right facts, wrong mechanism, wrong headline number, and the "clean F.Cu contrast" that gives it its force is demonstrably false.**
**Corrected severity: Nice-to-have. Confidence: High.**

### What survives
- **In4 is a GND plane and is B.Cu's reference.** Confirmed from the stackup: `B.Cu ← dielectric 5 (prepreg, 0.100 mm) ← In4.Cu`, and the In4 zone net is `GND`. Not in dispute.
- **The I²C bus really is routed on In4.** 43 segments, nets `SCL`, `SDA`, `SCL_HV`, `SDA_HV`, all 0.100 mm wide. Confirmed.
- **In4 really does fill as two islands** — 1264.66 mm² and 5.08 mm² at (109.00, 92.99)–(111.76, 99.25). KiCad itself emitted them as two separate `filled_polygon` blocks, so this is not an artefact of Wave 1's `unary_union`. The pocket is bounded by the `SCL` run (111.85,98.95)→(110.4,97.5)→(110.4,92.9) and the `SDA` run (111.55,99.45)→(108.8,96.7)→(108.8,93.5). Confirmed.

### What does not survive

**(i) The pocket is not a severed reference — it is stitched.** It contains two GND vias, (109.900, 96.900) and (109.6525, 94.950), both F.Cu–B.Cu through vias. The 5.08 mm² island is therefore bonded to the F.Cu GND pour, In1 and the B.Cu GND pour; it is a 0.4 %-of-plane pocket tied into the same ground system, not an orphan. Wave 1 noted the two vias in passing and then still called it "a severed piece of reference plane".

**(ii) The headline 3.10 mm "crossing" is not a crossing.** The segment is `B.Cu ALERT_N (130.20, 108.20) → (130.20, 105.10)` — a straight vertical run at constant x = 130.20. The In4 GND fill edge there is at x ≈ 130.30, and `SDA_HV` runs on In4 at x = 130.00 from y = 104.70 to y = 109.05. I sampled the In4 occupancy on a 0.1 mm grid over x 129.3–131.3, y 105.5–108.0: copper begins at x = 130.30 for every row. **The trace runs parallel to, and 0.1 mm outside, the slot edge for its whole 3.10 mm.** A 0.1 mm trace cannot "cross" a 0.3 mm slot for 3.10 mm — the number is geometrically impossible as a crossing, which should have been the tell. Wave 1's metric is `LineString.difference(GND_fill).length`, which measures *centreline not over copper* and cannot distinguish a crossing from a parallel run; the prose then narrated every such stretch as a crossing.

**(iii) The count of 18 is not reproducible, and is not what the data says.** The saved `05_plane_return_path.py` prints only per-net totals — the "nearest cause" attribution table in the report is not in the script, so the 18 cannot be regenerated. My recount of every B.Cu non-GND segment against the In4 GND fill:

| | stretches ≥0.3 mm |
|---|---|
| total | **84** |
| via anti-pad | 46 |
| THT anti-pad | 6 |
| plane edge / other | 9 |
| **attributable to an In4 I²C track** | **23** |
| …of which genuine slot crossings (both segment ends over plane, unbacked run ≤0.8 mm) | **6** |
| …long-unbacked (ends over plane, >0.8 mm) | 3 |
| …running off/alongside the plane edge | 14 |

So the I²C-attributable population is 23, not 18, but only **6** are the thing the finding describes.

**(iv) The "F.Cu/In1 came back essentially perfect" contrast is false, and it is what makes the finding sound structural.** Wave 1: *"**every** F.Cu 'unbacked' stretch the test found is a ≤0.45 mm via anti-pad."* Running the identical test on F.Cu vs In1:

```
F.Cu vs In1.Cu: 91 stretches >=0.3mm, total 42.5mm, 10 of them >=0.8mm
   1.95mm EXT_VBIAS (156.09,105.19)   1.36mm ENABLE (115.70,108.68)
   1.00mm Net-(J2-Pin_2)              1.00mm EXT_VBIAS   1.00mm BIAS
   0.91mm SDA  0.91mm SCL  0.91mm DP_RST_N  0.91mm CNTRL  0.82mm 3V3_PMOD
B.Cu vs In4.Cu: 84 stretches >=0.3mm, total 52.4mm, 22 of them >=0.8mm
```
A 1.95 mm stretch cannot be a 0.45 mm anti-pad. F.Cu has *more* unbacked stretches than B.Cu (91 vs 84) and only ~20 % less total unbacked length. The two routing layers are in comparable shape; In4's I²C roughly doubles the count of long (≥0.8 mm) stretches, from a baseline that was never clean.

**(v) Slot width versus dielectric height.** Measured transverse cuts: an isolated In4 I²C track leaves a slot of **0.30–0.40 mm** (0.1 track + 2 × 0.1 netclass clearance). The one genuinely wide slot is at x 126.00–127.50 beside `SCL_HV`, **1.50 mm** wide, where the zone's 0.1 mm `min_thickness` deleted the surviving fingers and merged several clearances. Against a 0.100 mm dielectric, a 0.3 mm slot is a ~3×h perturbation that the fringing return field bridges with negligible loop-area penalty; the 1.5 mm slot is a real discontinuity but still modest, and every victim on the list is a DC bias/configuration node (`VIOC`, `CLKDIS`, `ASEL`, `BIASAF`, `SET_CAP_NODE`, `EN`) or a slow open-drain interrupt (`ALERT_N`). The fastest thing on the board is 400 kHz–1 MHz I²C. Wave 1's own stackup section says this, then the finding reasons as if these were fast edges.

### The different real problem hiding underneath
The mechanism that actually applies here is **crosstalk, not return-path discontinuity**, because In4 traces sit 0.100 mm below B.Cu traces with no shield between them. Measuring B.Cu-trace length within 0.3 mm lateral of an In4 I²C trace:

```
SDA_HV <-> ALERT_N          5.36 mm        SCL_HV <-> ALERT_N        2.67 mm
SDA_HV <-> Net-(U1-VIOC)    1.79 mm        SCL_HV <-> Net-(U2-EN)    1.73 mm
SDA    <-> ENABLE           1.69 mm        SCL    <-> ALERT_N        1.69 mm
   ... TOTAL 27.80 mm over 21 net pairs
```
Even this is benign on the numbers: ~0.15–0.2 pF of mutual capacitance on the worst pair (SDA_HV/ALERT_N) against a 10–20 pF open-drain node gives a coupled step of a few tens of mV from a 3.3 V I²C edge. And the LT3074's one capacitance-sensitive pin, VIOC (datasheet p.41: *"the total capacitance on the VIOC pin must be below 20pF"*), picks up well under 1 pF from this. I could not find a mechanism here that produces a functional failure.

**Net assessment:** burying a bus in a reference plane is still poor practice and worth cleaning up on the next spin, and the 1.50 mm slot at x 126–127.5 is the one spot worth a stitching via or a reroute. But it is a tidiness item on this board, not "the one genuinely structural layout problem".

---

## CLAIM C — 0.9 mm neck on both OUT pours carrying the full 3 A

**Verdict: WEAKENED — the 3 A is right, the arithmetic is right for the width used, but the width is wrong by ~30 % and the method over-reads it.**
**Corrected severity: Nice-to-have. Confidence: High on geometry, Medium on thermal.**

**The 3 A figure is sound.** `R15` (2 mΩ) and `R16` (2 mΩ) take `OUT_1` and `OUT_2` into the common `SENSE_1_N` node, i.e. the two LT3074s are paralleled, so each neck is an independent per-channel path and 3 A is both the part's rating and the datasheet's worked-example current (p.42). Not a sibling-part number, not a figure from a different configuration. Load current is set externally at J3, so worst case is the right case.

**The 0.9 mm is a measurement artefact of the method.** I reproduce Wave 1's erosion result exactly — negative-buffer split at r = 0.425 (Wave 1's 0.05 mm step rounded it to 0.45 → "0.9 mm"), the small piece bounded by (130.12, 98.33)–(131.18, 98.78) for OUT_1 and (130.12, 107.33)–(131.47, 107.97) for OUT_2. But erosion-to-split measures the largest inscribed disc at the pinch, which under-reads a constriction whose boundary cuts diagonally — exactly the `(130.9, 97.9) → (132.0, 99.0)` diagonal Wave 1 itself quoted. The conducting cross-section *transverse to the current direction* is what matters. Scanning vertical cuts through the full F.Cu conductor (pour + pads):

```
OUT_1: narrowest vertical cut 1.20 mm at x=129.87, 1.20-1.25 mm over x 129.87-131.07, then opens out
OUT_2: narrowest vertical cut 1.20 mm at x=129.87, same profile
```
**The real neck is 1.20 mm wide and about 1.25 mm long**, not 0.9 mm.

**IPC-2221 arithmetic** (external layer, k = 0.048, 35 µm, I = k·ΔT^0.44·A^0.725):

| width | 1 A | 2 A | 3 A |
|---|---|---|---|
| 0.90 mm (Wave 1's figure) | 1.6 °C | 7.9 °C | **19.9 °C** |
| 1.20 mm (measured) | 1.0 °C | 4.9 °C | **12.4 °C** |

So Wave 1's "about a 20 °C rise" is correct arithmetic applied to a width that is 30 % too small. And both numbers are the steady-state rise of a **long uniform trace**; this constriction is 1.25 mm long between pours several millimetres wide, so lateral spreading dominates and the actual rise is single-digit °C. DC resistance of the neck is **0.51 mΩ → 1.54 mV and 4.6 mW at 3 A**, against the ~0.9 W the LDO itself dissipates 1 mm away. The neck is not the thermal story at this location; the die is.

**The different real problem next door.** `OUT_1` includes `U1.8`, `U1.9`, `U1.10 (SENSE_10)` and `U1.24` on the same net (`nets.tsv` line 41; same for `OUT_2`). The LT3074's SENSE pin is tied to OUT *at the package*, so remote sensing is not used and the 0.51 mΩ neck plus the 2 mΩ shunt plus the pour run to J3 are all **outside** the regulation loop. At 3 A that is ≥7.5 mV of uncompensated load-regulation error at the terminal block, which is a larger and more relevant number for a measurement demo board than the neck's self-heating. That belongs to the schematic reviewer, but it is the thing worth acting on here.

---

## CLAIM D — no mounting holes on a 70 mm board cantilevered off a 12-pin header

**Verdict: facts CONFIRMED, framing WEAKENED — the absence of mounting holes is not a Pmod defect, but the board fails the Pmod spec's actual mechanical requirement, which Wave 1 did not check.**
**Corrected severity: Nice-to-have (same as Wave 1), but re-pointed. Confidence: High.**

**Facts verified:**
- Edge.Cuts is a single `gr_rect` 94.92,89.00 → 165.00,111.00 = **70.08 × 22.00 mm = 2.7591″ × 0.8661″**. Confirmed.
- `LDO_MON_PMOD_Board_V1-NPTH.drl` contains only `M48 / header / FMAT,2 / METRIC / % / G90 / G05 / M30` — zero holes. Zero `np_thru_hole` pads anywhere in the `.kicad_pcb`. Zero `MountingHole*` footprints. Confirmed: there are genuinely no mounting holes.

**But "no mounting holes" is not a spec violation.** I grepped the whole of `pmod-interface-specification-1_2_0.pdf`: the words *mounting hole*, *hole*, and any mechanical fastening requirement **do not appear anywhere in the document**. The spec defines no mounting holes for peripheral modules. Boards much longer than this one ship as Pmods. Wave 1 is reporting a design choice, not a departure from the standard.

**What the spec does say, §4 "Physical Connection Standard" (p.3), is where this board actually fails:**

> "Peripheral modules with a single connector that are intended for direct connection to a host, or that are intended to fit into the Pmod mounting clip, should be 0.8″ wide. There should also be >25 mil of clearance from the board edge to any components to allow clearance for the Pmod clip to latch the board edge. The connector should be centered along the 0.8″ side of the module."

The Pmod clip is the **only** mechanical retention the standard defines — i.e. it is the standard's own answer to exactly the cantilever risk Wave 1 raised — and this board disqualifies itself from it twice over:

1. **Width.** 22.00 mm = 0.8661″, **1.68 mm over the 0.8″ (20.32 mm)** the clip requires.
2. **Edge keepout.** Three parts sit inside the 25 mil (0.635 mm) band the clip needs to latch, measured from courtyard+pad extents to the two long edges: **C6 (the 220 µF 8×10 can) at 0.450 mm**, C49 at 0.480 mm, C27 at 0.540 mm.

Two related spec points, both of which the board passes or nearly passes: *"modules more than 0.8″ wide can be directly connected to a host in most cases but may interfere with adjacent host ports"* — at 22.00 mm against the 0.9″ (22.86 mm) side-by-side port pitch there is 0.43 mm per side, so it fits but blocks nothing only just. And the connector **is** correctly centred: P1's pads span y 93.65–106.35, centre y = 100.00 = the board's own centre line.

**Assessment.** The cantilever concern is real but modest — ~12 g of board and parts, static moment at P1 of order 4 mN·m; the dominant load is a user's hand force on J3 at a 56 mm lever. Wave 1's severity (Nice-to-have) is right. The *fix* should change: adding ad-hoc M2.5 holes solves a problem the standard already has an answer to. Either bring the board to 0.800″ with ≥0.635 mm edge keepout so the standard Pmod clip can be used (which means moving C6, C49, C27 inboard and losing 1.68 mm of width), or accept that this is a cabled/bench module rather than a clip-mounted Pmod and add the holes — but record the choice, because "22.00 mm" is 1.68 mm from being compliant and looks like it was never checked rather than deliberately rejected.

---

## Defects in the Wave 1 scripts (these are what produced the errors above)

`05_plane_return_path.py`
- The crossing metric is `LineString(a,b).difference(ref_fill).length` on the **centreline only**. It cannot distinguish a trace crossing a slot from a trace running *parallel to* a slot, which is what generated the impossible "3.10 mm crossing". Trace width is ignored entirely.
- It performs **no cause attribution** — via anti-pad, THT anti-pad, plane edge and In4-track are all pooled. The "18 crossings attributable to an In4 track" table in the report cannot be regenerated from the saved script.
- It never computes the *width* of the gap being crossed, which is the quantity that decides whether a plane slot matters at all relative to the 0.100 mm dielectric.
- It reports only the four worst examples per net (`[:4]`), so the F.Cu/In1 result was read as clean when the full list has 10 stretches ≥0.8 mm.

`06_pcb_geometry.py`
- Correct on the point the brief suspected: it does read `filled_polygon` and does test zone intersection as well as tracks and pads. Its via-landing output is reproducible and I agree with it.
- Minor: every non-circular pad is modelled as a plain rectangle (roundrect corner radii ignored), slightly over-stating pad area; the oval-drill branch takes `dr[2]` (the Y dimension) as "the" drill; and there is a dead loop (`for g in [c for c in f if False]`) in the silk section.

## One cross-check for another finding, outside my four claims

**F-LAY-3 (R8 missing from the JLC BOM) is very likely backwards and should be re-examined before anyone edits that spreadsheet.** `SET_RES_NODE` reaches GND two ways: `R36` (0 Ω) → `Net-(U7-A)` → the AD5272 digipot (U7.3 wiper is on GND), and `R8` (0 Ω) → GND directly. The LT3074 datasheet is explicit that *"Placing a resistor from this SETRES pin to GND sets the output voltage"* and that VSETRES = VOUT. Fitting **both** R8 and R36 shorts SETRES to GND and forces VOUT ≈ 0 V on **both** regulators — i.e. R8 and R36 read as mutually exclusive option links (fixed-minimum vs digipot-programmed), and the JLC BOM that omits R8 may well be the correct one. Wave 1 rated the omission Should-fix/High on the opposite assumption. This needs the owner's intent before action.

---

## Summary of verdicts

| Claim | Wave 1 severity | Verdict | Corrected severity | My confidence |
|---|---|---|---|---|
| A — OUT e-pad vias land on one layer | Should-fix (the Wave 2 brief's "Blocker" is not Wave 1's rating) | **CONFIRMED** with two factual corrections | Should-fix | High |
| B — I²C on In4, plane split, 18 crossings | Should-fix | **WEAKENED** — facts true, mechanism and headline number wrong, the "clean F.Cu" contrast is false | Nice-to-have | High |
| C — 0.9 mm neck at 3 A | Should-fix | **WEAKENED** — real neck is 1.20 mm, rise is single-digit °C, 0.5 mΩ / 4.6 mW | Nice-to-have | High |
| D — no mounting holes | Nice-to-have | **CONFIRMED on fact, WEAKENED on framing** — spec defines no holes; board instead fails the 0.8″ / 25 mil clip requirement | Nice-to-have, re-pointed | High |
