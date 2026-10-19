# Wave 2 — adversarial verification of the MANUFACTURING DATA claims

Role: REFUTER. Everything below was re-derived from primary files (`.kicad_sch`, `.kicad_pcb`, the two BOM files, the two placement files, the LT3074 datasheet). Nothing is taken from the Wave 1 text.

## Method / scripts

Three-way (really five-way) reconciliation done with `csv` + `openpyxl` set arithmetic over:

| Source | Parts |
|---|---|
| `CLAUDE_REVIEW/raw/components.tsv` (schematic) | 118 designators |
| `MANUFACTURING_DATA/BOM/LDO_MON_PMOD_Board_V1_BOM.csv` (KiCad CSV BOM) | 115 designators / 41 rows |
| `MANUFACTURING_DATA/BOM/LDO_MON_PMOD_Board_V1_BOM_JLC_FORMATTED.xlsx` | 106 designators / 35 rows |
| `MANUFACTURING_DATA/Placement/LDO_MON_PMOD_Board_V1-all-pos.csv` | 107 designators |
| `MANUFACTURING_DATA/Placement/LDO_MON_PMOD_Board_V1_POSITION_JLC_FORMATTED.xlsx` | 107 designators |

xlsx files read with `openpyxl` (available). Board rotations read directly out of `LDO_MON_PMOD_Board_V1.kicad_pcb` footprint `(at x y rot)`.

### Checks performed

| Check | Method | Result | Notes |
|---|---|---|---|
| `SET_RES_NODE` full trace | `nets.tsv` + schematic symbol parse | **R8 is a direct 0 Ω short to GND** | see Claim A |
| R8 schematic attributes | parse `.kicad_sch` symbol at (270.51, 115.57) | `(dnp no) (in_bom yes) (in_pos_files yes)` | verified byte-level |
| "DNF" graphic, and what it is nearest to | nearest-symbol search over all schematic symbol origins | R8 at **3.059 mm**; next nearest real part R36 at 10.85 mm | unambiguous *visually*, invisible to every tool |
| Any DNP attribute anywhere in the design | `grep "(dnp yes)"` | **0 occurrences** (155 × `(dnp no)`) | the DNP mechanism is unused across the whole project |
| Any DNF/no-fit silk on the PCB | `grep -i` over `.kicad_pcb` | **none** | |
| schematic ↔ CSV BOM | set diff | 3 diffs, all correct (JP1/JP2/JP3, `in_bom no`) | |
| CSV BOM ↔ JLC BOM | set diff | **9 diffs**: J1 J2 J3 P1 TP1–TP4 **and R8** | 8 are legitimate; R8 is not |
| schematic ↔ placement CSV | set diff | 11 diffs, all THT/jumper/testpoint | correct |
| placement CSV ↔ placement xlsx | field-by-field, all 107 rows | identical except **3 rotations** | X, Y, Layer identical everywhere |
| placement ↔ JLC BOM | set diff | **`{R8}`** — R8 is the only placed part with no BOM row | |
| value & footprint agreement, schematic vs JLC BOM | string compare over 106 parts | **0 mismatches** | |
| LCSC part number coverage | scan column 4 | 2 of 35 rows empty (U3, U7) | plus 4 connectors with no BOM row at all |
| Board rotation vs both placement files | parse `.kicad_pcb` | CSV matches the board exactly; xlsx deviates on U4/U6/U8 | |
| LT3074 behaviour at R_SETRES = 0 | datasheet pp. 1, 2, 22, 31–32 | 100 µA × 0 Ω = **0 V, not damaging** | see Claim A |

### Checks I could not do
- **LCSC reel orientation drawings.** No network access. The rotation verdict in Claim D rests on the package-level JLCPCB rotation-correction convention as I know it, not on the LCSC product page for each specific part number. I say so explicitly below and have down-rated confidence accordingly.
- **JLCPCB's exact BOM/CPL mismatch handling.** I state what their quoting flow does from knowledge of the service, not from a document in this repo.

---

## CLAIM A — "R8 shorts SETRES to GND, an assembler fits it, the board is dead"

### Verdict: **WEAKENED**
### Corrected severity: **Should-fix** (not Blocker) · Confidence: **High** on the electrical facts, **Medium** on the assembly outcome

**The electrical half of the claim is fully confirmed. The consequence half is overstated in both directions, and the single best excuse is the one Claim B stumbled on.**

#### What I confirmed (primary evidence)

Complete trace of `SET_RES_NODE` (`nets.tsv:61`, 4 nodes, no others):

```
SET_RES_NODE  =  U1.13 (SETRES_13)  ·  U2.13 (SETRES_13)  ·  R8.1  ·  R36.2
GND           ⊃  R8.2 , R9.2 , U7.3 (W_3) , U7.11 (VSS) , U7.4 , U7.6
Net-(U7-A)    =  R36.1  ·  R9.1  ·  U7.2 (A_2)
```

So the full SETRES network is

```
            ┌── R8 (0R) ──────────────────────────── GND
SET_RES_NODE┤
            └── R36 (0R) ── Net-(U7-A) ──┬── R9 (50k) ── GND
                                         └── U7 A..W (AD5272 rheostat, W at GND)
```

R_SETRES = **R8 ∥ [ R36 + (R9 ∥ R_AW) ]**. R8 is **not** in series with anything and does **not** short out a different element: it is a plain 0 Ω link from the shared SETRES node straight to GND, in parallel with the entire programming network. With R8 fitted, R_SETRES = 0 Ω exactly, for **both** U1 and U2, and the AD5272 is completely bypassed. There is no reading of the topology that rescues it. R8's schematic symbol carries `(dnp no) (in_bom yes) (in_pos_files yes)`.

**Is there a "one of a set" pattern among the three 0 Ω parts?** No — I checked, and this is where the claim's framing is actually *supported*, not excused. The other two 0 Ω parts do different jobs and are both genuinely meant to be fitted:
- **R26**: `Net-(U5-ADDRSEL)` → GND. A PAC1944 I²C address strap. Must be fitted.
- **R36**: in **series** inside the digipot path (`SET_RES_NODE` → `Net-(U7-A)`). Must be fitted.
- **R8**: in **parallel**, shorting the node. Must *not* be fitted.

They are not a selectable set; R8 is the only shorting link of the three, and it is the only one marked DNF.

#### What the LT3074 actually does with R_SETRES = 0 (datasheet, re-read)

- p.1 General Description: *"The LT3074 sources a 100 µA precision reference current to the LT3074's SETRES pin. Placing a resistor from this SETRES pin to GND sets the output voltage."*
- p.22 Applications Information: *"The LT3074 incorporates a 100 µA precision current source flowing out of the SETRES pin… Connecting a resistor from the SETRES pin to ground generates a reference voltage for the error amplifier. This reference voltage is the product of the SETRES pin current and the SETRES pin resistance. The unity-gain [operation]…"*
- p.32 Table 8 (1 % resistors for common output voltages): 0.5 V → 4.99 kΩ, 1.0 V → **10.0 kΩ**, 3.3 V → 33.2 kΩ. Confirms exactly 100 µA/V.
- Absolute Maximum Ratings (p.9): *"SETRES, SETCAP Pin Voltage −0.3 V to 6 V."*
- Electrical Characteristics (p.2): every SETRES-related spec is conditioned on **0.5 V ≤ VOUT ≤ 4.2 V**.

So: **V_REF = 100 µA × 0 Ω = 0 V, and V_OUT = 0 V ± V_OS (±2 mV).** Not damaging — 0 V is well inside the −0.3 V to 6 V absolute maximum on SETRES, the 100 µA source dissipates nothing into a short, and the pass device simply sits off. The operating point is *outside* the characterised range (specs start at 0.5 V out), so behaviour is unspecified rather than destructive. **No part is harmed; no board is scrapped.** The digipot cannot override it: U7 is in parallel with a hard short, and nothing in the AD5272 or the LT3074 treats SETRES = 0 as a "default/preset" mode — the LT3074 has no internal default reference, the SETRES resistor *is* the reference.

**Correction to a number in Wave 1's suggested fix (F-PWR-1):** it recommends *"a fixed resistor option that gives a sane default (e.g. 4.99 kΩ → 1.0 V, exactly the Fig. 92 value)"*. Datasheet **Table 8, p.32** gives 4.99 kΩ → **0.5 V**; 1.0 V is **10.0 kΩ**. The remedy as written programs half the intended voltage.

#### Why the claim is WEAKENED — the excuse I was asked to find

The claim's load-bearing step is *"therefore an assembler fits it"*. That step does not survive contact with the released data:

1. **The JLC BOM — the file actually formatted for the assembler — does not contain R8** (verified, see Claim B). The `0R` row reads `R26,R36`.
2. R8 is the **only** designator in the entire placement file with no row in the JLC BOM (`set(placement) − set(jlc_bom) == {'R8'}`). Every other part reconciles.
3. JLCPCB's assembly flow matches BOM designators against CPL designators; a designator present in the CPL but absent from the BOM is reported as unmatched and is **not placed**. It does not cause a wrong part to be fitted, and it does not stop the order.

So the most likely real-world outcome of releasing this data pack as-is is that **R8 is not fitted and the board works** — which is also the intent recorded by the DNF graphic. The claim's conclusion ("the board is dead") is the *less* likely branch.

#### The residual risk, stated precisely

This is still a real finding, because the intent is recorded **only in two places that can both be lost**:
- a **bare graphic text object** `"DNF"` at (267.462, 115.824), 3.059 mm from R8 at (270.51, 115.57) — not a field, not bound to the symbol, invisible to the netlister, the BOM exporter and the CPL exporter. Nearest-symbol search confirms it reads as R8's (next real part, R36, is 10.85 mm away), so a *human* reading the sheet gets it right;
- a **hand-deleted row in the xlsx**, which will be silently reinstated the next time the xlsx is regenerated from KiCad.

And the two released BOMs now **contradict each other on exactly the one part that determines whether the board functions**:
- `..._BOM.csv` line 26: `"R8,R26,R36","3","0R","", …` — DNP column empty, R8 ordered, qty 3;
- `..._BOM_JLC_FORMATTED.xlsx`: `('0R', 'R26,R36', …, 'C60485')` — R8 absent.

If anyone orders from the KiCad CSV (the one that is *automatically* correct for everything else), or regenerates the xlsx, R8 is fitted and both LDOs read 0 V at bring-up with no obvious cause. Recovery is removing one 0402 — annoying, not fatal.

Worth noting for the file: **`(dnp yes)` appears zero times in the whole schematic** (155 × `(dnp no)`), and the CSV BOM's `Exclude from Position Files` column contains the literal unexpanded string `${EXCLUDE_FROM_POS_FILES}` on every row. The DNP machinery is simply not in use in this project, so R8 is the first part that needed it.

**Suggested fix:** set `(dnp yes)` + `in_pos_files no` on R8 in the schematic so the intent propagates to both BOMs and both CPLs automatically; keep the pads; add a `DNF` silk legend next to R8 on the PCB (currently none); and change the CSV BOM's `0R` row the same way so the two BOMs stop disagreeing. If a non-zero default is wanted instead, 10.0 kΩ gives 1.0 V (Table 8, p.32).

---

## CLAIM B — "R8 is missing from the JLC BOM xlsx"

### Verdict: **CONFIRMED**
### Corrected severity: **Should-fix** · Confidence: **High**

Read directly from the xlsx:

```
('0R', 'R26,R36', 'Resistor_SMD:R_0402_1005Metric', 'C60485')
```

versus the CSV BOM line 26 `"R8,R26,R36","3","0R",…` and the placement row `"R8","0R","R_0402_1005Metric",130.200000,-95.800000,0.000000,top`. R8 is in the schematic, in the CSV BOM, in both placement files, and absent from the JLC BOM. Confirmed.

**What JLC would actually do with a BOM missing R8 and a CPL containing R8:** nothing bad. Their BOM/CPL matcher keys on the designator; `R8` appears in the CPL with no BOM counterpart, is reported as unmatched in the parts-review step, and is left unpopulated. The CPL row is inert without a BOM row — it cannot cause a wrong part or a misplacement, only a non-placement. **So the as-released pair produces the intended result**, and this is the reason Claim A is downgraded from Blocker. The defect is that the two BOMs disagree and the correct one is the hand-maintained one, which is backwards: the hand-edited file is the one that will drift.

### Full five-way reconciliation (every disagreement, not just R8)

| Pair | Disagreements | Verdict |
|---|---|---|
| schematic → CSV BOM | `JP1, JP2, JP3` absent from CSV BOM | **Correct.** All three carry `(in_bom no)` — solder jumpers, nothing to buy (DI-1). |
| CSV BOM → schematic | none | Clean |
| CSV BOM → JLC BOM | `J1, J2, J3, P1, TP1, TP2, TP3, TP4` **and `R8`** | 8 correct (THT connectors + test pads are not SMT-assembly line items); **R8 is the one real divergence.** |
| JLC BOM → CSV BOM | none | Clean |
| schematic → placement CSV | `J1, J2, J3, JP1, JP2, JP3, P1, TP1–TP4` | **Correct** — THT/jumpers/pads excluded from pick-and-place. |
| placement CSV → schematic | none | Clean |
| placement CSV ↔ placement xlsx | **identical designator sets**, identical X, Y and Layer on all 107 rows; **rotation differs on U4, U6, U8 only** | see Claim D |
| placement → JLC BOM | **`{R8}`** | the single cross-file orphan |
| value, schematic vs JLC BOM | **0 mismatches** over 106 parts | Clean |
| footprint, schematic vs JLC BOM | **0 mismatches** over 106 parts | Clean |

I re-derived all of this independently and got the same designator sets Wave 1 reports, so its arithmetic is sound. Wave 1's framing ("JLC ships the board with R8 unpopulated… a both-channels-wrong assembly defect") is **backwards**: unpopulated R8 is the *correct* build. That is a right finding reached by inverted reasoning, and it is the second reason Claim A is weakened — Wave 1's own layout report contains the evidence that refutes Wave 1's own power report.

---

## CLAIM C — "U3 (MAX6373) and U7 (AD5272) have no LCSC part number"

### Verdict: **CONFIRMED**, but **incomplete** — the real unsourceable count is 6, not 2
### Corrected severity: **Should-fix** · Confidence: **High**

Exactly two of the 35 JLC BOM rows have an empty `JLCPCB Part #` cell:

```
('MAX6373',   'U3', 'Package_TO_SOT_SMD:SOT-23-8',                                        None)
('AD5272BCP', 'U7', 'Package_CSP:LFCSP-WD-10-1EP_3x3mm_P0.5mm_EP1.64x2.38mm',             None)
```

All 33 others are populated (LT3074 C44238296, PAC1944 C3688047, 74LVC1G175 C128412, 74LVC1G08 C123314, PCA9306 C33196, MMBT3904 C58011, …). Confirmed.

**Checking all parts, not just those two.** `components.tsv` has `Manufacturer`, `MPN` and `LCSC` columns and **all 118 rows are empty in all three** — the schematic carries no part numbers whatsoever, so the JLC xlsx is the only place sourcing data exists in this repo. Of the 118 schematic designators:

- 7 are not purchasable items (JP1–JP3 solder jumpers, TP1–TP4 test pads) → 111 real parts;
- R8 is deliberately not fitted → 110 parts to buy;
- 104 have an LCSC code via the JLC BOM;
- **6 cannot be sourced from the released data as it stands:**

| Ref | Value in the data | Why it can't be ordered |
|---|---|---|
| U3 | `MAX6373` | empty LCSC cell; and `MAX6373` alone is not an orderable MPN (needs the suffix, e.g. `MAX6373KA+T`) |
| U7 | `AD5272BCP` | empty LCSC cell; **and the resistance variant is missing** — AD5272BCPZ ships as -20, -50 and -100 (20 kΩ/50 kΩ/100 kΩ). The SETRES network's behaviour depends entirely on which one is fitted, and nothing in the released data says. This is a sourcing *ambiguity*, worse than a blank cell, because someone can order the wrong one and it will fit and work. |
| J1 | `3-Pin Harwin` | no BOM row in the JLC BOM at all, and no MPN anywhere — "3-Pin Harwin" is not a part number |
| J2 | `2-Pin Harwin` | same |
| J3 | `Conn_01x04` | the footprint says PhoenixContact MC 1,5/4-G-3.5, but no MPN is recorded |
| P1 | `PMOD-Device-x2-Type-Generic-Alt` | no MPN; Wave 1 separately could not tell vertical from right-angle from the board file, so the host mating geometry is undetermined *and* unorderable |

Also worth flagging: U5's BOM comment is the literal placeholder `PAC1944x-x4MX` with the `x` wildcards left in. It happens to be rescued by LCSC C3688047, but as a human-readable MPN it is not a real part number either.

Wave 1's consequence statement for U3/U7 is sound (both are actives, U7 is an LFCSP with a 1.64 × 2.38 mm exposed pad that genuinely cannot be hand-reworked with an iron). It just stopped two parts short: the four THT connectors have *no* sourcing information anywhere in the repo, which is a bigger hole than an empty cell, because an empty cell at least gets flagged by JLC's parts review and a missing connector gets noticed only when the board arrives.

---

## CLAIM D — "U4/U6/U8 carry a hand-edited 180° rotation; the same correction was not applied to U3/U5"

### Verdict: **WEAKENED** — the discrepancy is real and I reproduce it exactly, but the claim's risk assessment is inverted and it names the wrong companion parts
### Corrected severity: **Nice-to-have** (down from Should-fix) · Confidence: **Medium** (the decisive evidence — per-part LCSC reel drawings — is offline)

#### Verified rotations, all ICs and all polarised parts

Read from `.kicad_pcb` footprint `(at …)`, from the CPL CSV, and from the xlsx:

| Ref | Part | Package | Side | `.kicad_pcb` | CPL CSV | **JLC xlsx** | Delta |
|---|---|---|---|---|---|---|---|
| U1 | LT3074AV#PBF | `klib_logic:LT3074AV#PBF` (22-ld LQFN) | top | 90 | 90 | 90 | — |
| U2 | LT3074AV#PBF | same | top | 90 | 90 | 90 | — |
| U3 | MAX6373 | SOT-23-8 | top | 0 | 0 | 0 | — |
| U4 | 74LVC1G175 | SOT-23-6 | top | 0 | 0 | **180** | **+180** |
| U5 | PAC1944 | VQFN-16-1EP 3×3 | top | 0 | 0 | 0 | — |
| U6 | 74LVC1G08 | Texas R-PDSO-N5 (SOT-553) | top | 0 | 0 | **180** | **+180** |
| U7 | AD5272BCP | LFCSP-WD-10-1EP 3×3 | top | 180 | 180 | 180 | — |
| U8 | PCA9306 | VSSOP-8 2.3×2.0 P0.5 | top | 0 | 0 | **180** | **+180** |
| Q1 | MMBT3904 | SOT-23 | **bottom** | 180 | 180 | 180 | — |
| D1 | LED | LED_0402 | top | 0 | 0 | 0 | — |
| D2 | LED | LED_0402 | top | 0 | 0 | 0 | — |
| C6 | 220 µF | CP_Elec_8x10 (alu electrolytic) | top | 90 | 90 | 90 | — |
| C9 | 4u7 | C_0603_1608Metric | bottom | 180 | 180 | 180 | — |
| C13 | 4u7 | C_0603_1608Metric | bottom | 180 | 180 | 180 | — |

Claim D's factual core is exactly right: three parts, +180 each, nothing else differs — X, Y and Layer are byte-identical on all 107 rows. The board file confirms the CSV, so the xlsx was hand-edited after export.

#### Are the three edits correct?

**Almost certainly yes, and the claim's worst case ("U4, U6 and U8 are all assembled backwards") is the unlikely branch.** The three packages corrected are precisely the three that carry a +180 entry in the standard JLCPCB rotation-correction convention — the one baked into the `kicad-jlcpcb-tools` CPL rotation database, where the SOT-23 family, SOT-553, and VSSOP-8 2.3×2.0 P0.5 are all `180`, while QFN/VQFN and LFCSP are `0`. Against that rule:

| Ref | Package | Rule says | xlsx does | |
|---|---|---|---|---|
| U4 | SOT-23-6 | +180 | +180 | ✅ consistent |
| U6 | SOT-553 | +180 | +180 | ✅ consistent |
| U8 | VSSOP-8 2.3×2.0 P0.5 | +180 | +180 | ✅ consistent |
| U5 | VQFN-16 | 0 | 0 | ✅ consistent — **U5 is not a missed correction, it needs none** |
| U7 | LFCSP-10 | 0 | 0 | ✅ consistent |
| **U3** | **SOT-23-8** | **+180** | **0** | ❌ **missed** |
| **Q1** | **SOT-23** | **+180** | **180 (unchanged)** | ❌ **missed** |

So the edits were not ad-hoc guesses — they are the three corrections the convention calls for. **Claim D names the wrong companion parts.** It flags U5 (VQFN-16), which correctly needs no correction, and it misses **Q1 (SOT-23)** entirely, which by the same rule should have been corrected and was not. The rule-consistent reading is: three of five required corrections were applied, U3 and Q1 were missed, U5/U7 are fine.

**Which parts would actually be assembled wrong?**

- **Q1 (MMBT3904, SOT-23, C58011, bottom side, (106.2, −98.6), 180°)** — the one genuinely exposed part. If the SOT-23 +180 convention holds, Q1 goes down rotated 180° from intended, which on a SOT-23 swaps the pin-1/pin-3 ends: base↔emitter. Q1's emitter is on GND (`GND ⊃ Q1.2 (E_2)`), so a flipped Q1 puts the base node on GND and the emitter on the 4k7 base path — the ENABLE pull-down transistor stops working as a switch. Confidence here is lowered by Q1 being a **bottom-side** part: bottom-layer rotation conventions interact with mirroring and the correction may not apply the same way. Flag it for the JLC placement preview; do not rework it on my say-so.
- **U3 (MAX6373, SOT-23-8)** — **moot in practice.** U3 has no LCSC part number (Claim C), so JLC will not place it at all; its CPL rotation is never used. Fix the part number and the rotation becomes live, so fix both together or neither.
- **U4, U6, U8** — on the evidence I have, these are the **correctly** handled ones. Treat the xlsx value as right and the CSV as the one needing a post-processing step.
- **D1/D2 (LED_0402, C74338)** — both at 0° in all three files, no correction attempted. LED reel polarity is the single most common JLC orientation error and KiCad's `LED_SMD:LED_0402_1005Metric` puts the cathode at pin 1. I cannot resolve C74338's reel orientation offline. Combined with Wave 1's F-LAY-7 (the only cathode marking on the board is a 0.1 mm silk dot that is below JLC's 0.15 mm minimum and will probably not print at all), **D1/D2 are a better orientation risk than U4/U6/U8** and nobody has looked at them.
- **C9/C13** — the 180° is the board's own placement, identical in both files, and the real parts are 4.7 µF **ceramic** 0603s (LCSC C1705). The polarised schematic symbol is a symbol-level cosmetic issue only; there is **no manufacturing polarity risk** here. Clean.
- **C6 (220 µF CP_Elec_8x10, C125981)** — the only genuinely polarised capacitor on the board, at 90° with no correction applied, and Claim D does not mention it. Also unverifiable offline; add it to the placement-preview check list.

**Suggested fix (replacing Wave 1's):** stop hand-editing the xlsx. Generate the JLC CPL from the CSV with a scripted per-package rotation table, seeded with the standard JLCPCB correction database, and record the table next to the BOM. Before release, check the JLC placement preview for **Q1, U3, D1, D2 and C6** — not U5, which is already right.

---

## Summary

| Claim | Verdict | Corrected severity | Confidence |
|---|---|---|---|
| A — R8 0 Ω shorts SETRES; assembler fits it; board dead | **WEAKENED** | Should-fix | High (electrical) / Medium (outcome) |
| B — R8 missing from the JLC BOM xlsx | **CONFIRMED** | Should-fix | High |
| C — U3/U7 have no LCSC part number | **CONFIRMED** (incomplete: 6 parts unsourceable, not 2) | Should-fix | High |
| D — U4/U6/U8 hand-rotated 180°, U3/U5 not | **WEAKENED** | Nice-to-have | Medium |

**The one-line version.** The R8 topology is exactly as described and R_SETRES = 0 Ω really does program both LT3074s to 0 V — but it is not destructive (0 V is inside the SETRES absolute maximum), and the BOM that is actually formatted for the assembler already omits R8, so the released data pack most likely builds correctly. What is genuinely wrong is that the two released BOMs contradict each other on the single part that decides whether the board works, and the do-not-fit intent lives only in an unbound graphic and a hand-deleted spreadsheet row — both of which vanish on the next regeneration. The rotation edits are the convention-correct ones; the parts at risk are Q1, D1/D2 and C6, which nobody has checked, not U4/U6/U8, which were handled properly.

### Issues found nearby, not in any claim
1. **AD5272 resistance variant unspecified** (`AD5272BCPZ-20 / -50 / -100`). The whole SETRES programming range depends on it and it is recorded nowhere. Arguably the most consequential sourcing gap in the pack, worse than the two blank LCSC cells because a wrong variant fits and runs.
2. **J1, J2, J3, P1 have no MPN anywhere** in the repo (`3-Pin Harwin`, `Conn_01x04`, `PMOD-Device-x2-Type-Generic-Alt`).
3. **Wave 1 F-PWR-1's suggested fix misquotes Table 8**: 4.99 kΩ gives 0.5 V, not 1.0 V (1.0 V is 10.0 kΩ, datasheet p.32).
4. **The CSV BOM's `Exclude from Position Files` column contains the unexpanded literal `${EXCLUDE_FROM_POS_FILES}`** on all 41 rows — a broken BOM field template. Harmless today, but it means that column conveys nothing, which matters the moment anyone tries to use it to express the R8 intent.
5. **`(dnp yes)` appears zero times in the schematic.** The DNP mechanism is entirely unused, so there is no existing convention for a reviewer or a future editor to notice that R8 is special.
