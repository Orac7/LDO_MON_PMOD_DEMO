# Findings — LDO_MON_PMOD_Board_V1

Design reviewed at commit `ec3514f`. Six reviewers across two waves; every finding below survived an adversarial pass whose explicit goal was to refute it. Items that did not survive are listed at the end with the reason, so you can see what was considered and rejected.

**No blockers.** The design is electrically sound and the released manufacturing data is current. Nothing here says "do not build". The highest-severity items are integrity problems in the build data and one incomplete thermal path.

## Summary

| ID | Severity | Finding | Confidence |
|---|---|---|---|
| F-01 | Should-fix | Build-critical data lives in unbound schematic text, not component fields | High |
| F-02 | Should-fix | J1 strapping `BIAS = 3V3_PMOD` breaks three things at once | High |
| F-03 | Should-fix | Default digipot setting programs 3.33 V, outside the legal V_OUT window | High |
| F-04 | Should-fix | LT3074 OUT exposed-pad vias reach no copper plane | High |
| F-05 | Should-fix | `ALERT_N` can present up to 5.5 V on a 3.3 V host pin | High |
| F-06 | Should-fix | The board carries no silkscreen legends at all | High |
| F-07 | Should-fix | Board is oversize for the Pmod clip, with parts inside the edge keepout | High |
| F-08 | Should-fix | `R27`–`R34` are 5× the PAC1944's allowed series sense resistance | High |
| F-09 | Should-fix | No minimum preload; a paralleled pair needs >200 mA to avoid an ALERT | Medium |
| F-10 | Should-fix | `C28`/`R17` violate the 74LVC1G175 input slew limit by ~5×10⁴ | Medium |
| F-11 | Should-fix | ERC rules disabled and DRC violations excluded in the project file | High |
| F-12 | Nice-to-have | Channel 3 Kelvin tap misses `R16`'s pad by 0.64 mm | Medium |
| F-13 | Nice-to-have | Silk strokes below fab minimum; D1/D2 cathode dot will not print | High |
| F-14 | Nice-to-have | `R18 = 1k` is load-bearing and undocumented | High |
| F-15 | Nice-to-have | Assorted schematic hygiene | High |

---

## F-01 — Build-critical data lives in unbound schematic text
**Should-fix · High confidence · Root cause behind four other findings**

The schematic has **no `MPN`, `LCSC`, `Manufacturer`, `Voltage`, `Tolerance` or `Dielectric` property on any of the 118 components.** The complete property-key set is `Component Class, Datasheet, Description, Footprint, Intersheetrefs, Netclass, Reference, Value` plus KiCad internals. Everything needed to actually buy the parts instead lives in free-floating graphic text objects, which propagate to nothing:

| Floating text | What it means | What it should be |
|---|---|---|
| `"DNF"` (3.05 mm from R8) | R8 is do-not-fit | `(dnp yes)` on R8 |
| `"NOTE: AD5272 VERSION - 50K NOMINAL RESISTANCE"` | U7 is the 50 kΩ variant | U7 `Value`/`MPN` |
| `"WSL2512R0150FEA"`, `"WSL25122L000FED"` | The **shunt** MPNs | R15/R16/R35/R39 `MPN` |

Consequences, each independently verified:

- **R8 contradiction.** `R8` is `(dnp no) (in_bom yes) (in_pos_files yes)`. It appears in the CSV BOM (`"R8,R26,R36"`) and in the placement file at line 82 as `top`. It has been **hand-deleted from the JLC BOM xlsx** (`['0R', 'R26,R36', …, 'C60485']`). Since a CPL designator with no BOM row is not placed, the board most likely builds correctly today — but the two released BOMs disagree about the one part that decides whether it works, and the next regeneration silently reinstates R8. If fitted, R8 shorts `SET_RES_NODE` to ground and programs **both** LDOs to 0 V. Not damaging — 0 V is well inside the SETRES abs-max — but the board appears dead.
- **U7 variant unspecified.** `AD5272BCP` with no `-20`/`-50`/`-100` suffix anywhere in buildable data. The wrong variant fits the footprint, runs, and silently changes the entire output-programming range: default V_OUT becomes 1.67 V, 3.33 V or 5.00 V.
- **Six parts cannot be sourced** from the released BOM: `U3` and `U7` have empty JLCPCB part numbers; `J1`, `J2`, `J3`, `P1` have no BOM row and no MPN anywhere.
- **No voltage ratings.** `C2`/`C16` (2u2 0603 on BIASAF) and `C1`/`C14` (470n 0402 on BIASDF) sit on the datasheet's own characterisation values, so a 6.3 V X5R part could fall below spec after DC-bias derating. `C49` has an explicit ≥7 V requirement in the AD5272 datasheet and is a 1 µF 0402, commonly stocked at 6.3 V.
- All 41 CSV BOM lines carry an **unexpanded `${EXCLUDE_FROM_POS_FILES}`** literal — the text variable never resolved.

**Fix:** add `MPN`, `LCSC`, `Voltage` and `Dielectric` fields to the components; set `(dnp yes)` on R8; promote the three floating notes into the fields they describe. The BOM then carries this automatically and the contradiction cannot recur.

## F-02 — J1 strapping `BIAS = 3V3_PMOD` breaks three things at once
**Should-fix · High confidence · Highest-leverage single item after F-01**

Flagged independently by three reviewers via three different datasheets:

1. **Caps the output at 2.1 V.** LT3074 p.14, verbatim: `V_BIAS ≥ 1.2 + V_OUT`, restated p.37 and encoded in the EC table as the gating condition `Max[2.375, V_OUT+1.2] ≤ V_BIAS ≤ 5.5`. A hard requirement over full temperature. With BIAS at 3.3 V, V_OUT is capped at 2.1 V — and ~1.94 V at the low end of an unregulated host 3V3.
2. **Breaks I²C level translation.** With BIAS = 3V3_PMOD, VREF1 = VREF2. The PCA9306 requires VREF2 ≥ VREF1 + 0.6 V to translate; at equality it is in pass-through "switch mode", not translation.
3. **Interacts with F-03** — 2.1 V is below the 3.33 V the digipot defaults to.

**Fix:** document J1's two states and their consequences on the schematic, and make the legal operating envelope explicit. If 3V3 bias is intended to be usable, the digipot default must be constrained to suit.

## F-03 — Default digipot setting programs 3.33 V
**Should-fix · High confidence**

U1 and U2 share `SET_RES_NODE` (netlist: `U1.13`, `U2.13`, `R8.1`, `R36.2`) — the datasheet's Direct Paralleling recipe. **Each device sources its own 100 µA**, so the shared node sees **200 µA**. The decisive evidence is the datasheet's own numbers: Table 8 (p.31) gives 4.99 kΩ → 0.5 V for a single device, while Fig. 92's two-device circuit gives 4.99 kΩ → **1 V**. The currents add.

The AD5272 presets to midscale on power-up (~25 kΩ on the 50 kΩ part), paralleled with `R9` 50 kΩ → 16.667 kΩ. So default V_OUT = 200 µA × 16.667 kΩ = **3.3333 V**.

With J1 on 3V3_PMOD that exceeds the 2.1 V BIAS-headroom cap (F-02). Only about 27 % of the digipot's code range is legal in that configuration, and nothing in hardware enforces it.

**Fix:** choose `R9` so the power-up default lands inside the legal window for the shipped jumper configuration, rather than relying on firmware to write a safe code before anything is measured.

## F-04 — LT3074 OUT exposed-pad vias reach no copper plane
**Should-fix · High confidence · Independently reproduced**

Of 174 vias on the board, exactly four land copper on only one layer: the via-in-pad pairs on `U1.24` and `U2.24`, the **OUT** exposed pads. They connect to the pad and nothing else — they do not even touch the F.Cu OUT pour, running tangent to it at x = 129.700. The **IN** exposed pads on the same parts are done correctly: four vias each into the 1287.58 mm² In3 plane.

LT3074 p.41 requires *both* IN **and** OUT to reach large copper layers below via thermal vias. The asymmetry reads as an unfinished edit rather than a decision.

Two corrections to the original report: `OUT_1`/`OUT_2` *do* have 0.43/1.17 mm² of B.Cu copper (at `R28.2`, `R29.2`, `C15.1`) with existing F↔B vias, so the fix extends routing that is already there rather than creating a new path.

**Fix:** pour `OUT_1`/`OUT_2` on an inner or bottom layer under each LDO and land the e-pad vias in it.

## F-05 — `ALERT_N` can present up to 5.5 V on a 3.3 V host pin
**Should-fix · High confidence · Explicitly warned about in the Pmod spec**

`ALERT_N` is the one LT3074 bus signal that bypasses U8 entirely. `R5` pulls it to `BIAS`, which J1 can set to `EXT_VBIAS` at up to 5.5 V, and it goes straight to PMOD pin 3.

The Pmod spec §2 *permits* open-drain outputs provided the pull-up is on the module, which R5 is — so that part is compliant. But §3 then warns: *"Care should be taken to ensure 5 V will not damage the host's input pins."* This is the exact configuration the spec cautions against. Not destructive to this board (LT3074 ALERT is open-drain and R5 limits to ~110 µA), but it is the host that is at risk.

**Fix:** move `R5` to `3V3_PMOD`. One net change.

## F-06 — The board carries no silkscreen legends at all
**Should-fix · High confidence**

- **Zero** `gr_text` objects at board level.
- Of 124 footprint text objects, **114 are on `F.Fab`/`B.Fab`** — documentation layers that are never printed.
- Only 6 text objects reach actual silkscreen.
- **Every** connector and jumper reference designator is `(hide yes)`: `P1`, `J1`, `J2`, `J3`, `JP1`, `JP2`, `JP3`.

Two concrete consequences:

- **JP1/JP2/JP3 are unlabelled.** Per your stated intent these are solder-blobbed by hand before use — but they sit at x = 106.5, 109.0, 111.5, all at y = 107.7: three identical 3-pad patterns 2.5 mm apart with nothing printed beside them. There is no way on the physical board to tell which is which or which way round to bridge each. A wrong blob is not always obvious either: `1,0,0` gives t_WD = 30 µs, which holds both LDOs off and makes the board look dead, and `0,1,1` disables the watchdog silently.
- **J3 is an unlabelled power terminal.** It carries VBIAS/VOUT/VIN/GND with **no diode, fuse or TVS anywhere on the board**. Reversing VIN and GND on a hand-wired 3.5 mm terminal block destroys both LT3074s, and nothing on the board says which pin is which.

**Fix:** unhide the connector and jumper refdes, add pin-1/polarity legends to J1–J3, and add a short jumper table in silk or on the schematic. Reverse-polarity protection on J3 is a separate judgement call.

## F-07 — Board is oversize for the Pmod clip, with parts inside the edge keepout
**Should-fix · High confidence**

Board is **70.08 × 22.00 mm = 2.76 × 0.8661″**. The Pmod spec §4 requires modules intended to fit the Pmod mounting clip to be **0.8″ wide** with **>25 mil clearance** from the board edge to any component. This board is **1.68 mm oversize**, and three parts sit inside the keepout: `C6` at 0.450 mm, `C49` at 0.480 mm, `C27` at 0.540 mm.

The spec never mentions mounting holes, so "no mounting holes" is not itself a violation — the clip *is* the defined retention method, and this board cannot use it. On a 70 mm board cantilevered off a 12-pin header with the heavy parts at the far end, that is worth a decision rather than an accident.

**Fix:** accept it and document that the clip is unusable, or narrow to 0.8″ and move the three parts out of the keepout.

## F-08 — `R27`–`R34` are 5× the PAC1944's allowed series sense resistance
**Should-fix · High confidence**

The eight 4.99 kΩ resistors feeding the PAC1944 sense inputs. Datasheet p.6 allows 1 kΩ `RTRACE` "without measurement error", and p.1 states "No input filters are required for this device."

±6 µA input current × 4.99 kΩ = **±30 mV** V_BUS error (219 LSBs). Differentially, up to 60 µV, which on a 2 mΩ shunt is **30 mA** of error — on a board built to measure current sharing.

**Fix:** reduce to ≤1 kΩ.

## F-09 — No minimum preload
**Should-fix · Medium confidence**

The LT3074 is a PMBus 1.3 part (p.46, Table 6). Each device compares its own `READ_IOUT` against its own `MFR_IOUT_MIN_WARN_LIMIT`, default `0xA19A` = 410 × 2⁻¹² = **100.1 mA** (p.55). Below that it asserts ALERT and sets status bits.

There is no preload anywhere on the output, so an unloaded demo board raises a warning on every power-up. Note this is a *warning*, not a shutdown — the board still regulates.

**Fix:** a preload resistor sized for **>200 mA total** across the paralleled pair, or raise the limit in firmware and document that the warning is expected.

## F-10 — `C28`/`R17` violate the 74LVC1G175 input slew limit
**Should-fix · Medium confidence*

`C28` (100n) with `R17` (10k) on `/WDO` gives a ~0.65 ms transit of the forbidden input band on U4's `/CLR` — about **545 µs/V** against the part's 10 ns/V limit. The host resumes strobing WDI (U4's clock) during exactly that window, risking a metastable or indeterminate clear.

`C28`'s apparent power-on-reset role is already covered by `R20`.

**Fix:** remove `C28`, or buffer `/WDO` through a Schmitt input.

## F-11 — ERC rules disabled and DRC violations excluded
**Should-fix · High confidence**

The project reports "0 errors", but six ERC rules are set to `ignore` — including `pin_not_driven`, `power_pin_not_driven` and `single_global_label` — and nine DRC violations are excluded. Re-running with everything enabled surfaces six additional items.

**Fix:** re-enable at least the three substantive ERC rules and re-triage. Of the nine DRC exclusions, the four `via_dangling` ones on OUT_1/OUT_2 should **not** be re-excluded — they are F-04.

## F-12 — Channel 3 Kelvin tap misses `R16`'s pad
**Nice-to-have · Medium confidence**

Channel 3's high-side Kelvin tap is a via at (135.15, 109.01), **0.64 mm outside `R16`'s pad**, inside the live `OUT_2` pour. Channel 4 taps `R15`'s pad centre exactly. Estimated ~0.1 mΩ of included copper → roughly **5 % gain asymmetry** between the two channels — which is precisely the current-sharing comparison this board exists to make.

**Fix:** move the tap onto the pad, matching channel 4.

## F-13 — Silk strokes below fab minimum
**Nice-to-have · High confidence**

Silk strokes of 0.10/0.12 mm against a 0.15 mm fab minimum, including the **0.1 mm D1/D2 cathode dot**, which likely will not print at all. Combined with F-06, the LED polarity markings effectively do not exist. `min_silk_clearance` is set to 0 (check disabled), though an independent check found 0 actual overlaps.

## F-14 — `R18 = 1k` is load-bearing and undocumented
**Nice-to-have · High confidence · Per RP-1**

`R18` is 1k as built, giving 1.52 V of ENABLE margin — correct and healthy. But the constraint is invisible on the sheet: Q1's 4k7 base path loads `ENABLE`, so the obvious tidy-up to 10k collapses the margin to ~0.2 V against the LT3074's 1.32 V threshold. This is a live trap for a future editor.

**Fix — suggested schematic note beside R18:**

> R18 = 1k is load-bearing. Q1 (4k7 base path) loads ENABLE; do not raise this value. At 10k the ENABLE high level falls to ~0.2 V above the LT3074 1.32 V threshold. Recompute the divider against U1/U2 ENABLE Vih before changing.

## F-15 — Assorted schematic hygiene
**Nice-to-have · High confidence**

- `C9`/`C13` use a polarised capacitor symbol on a non-polarised 0603 footprint (they are ceramic — the symbol is wrong, not the part).
- Global label `GPIO` appears exactly once in the schematic — a label with no destination.
- `U1.6`/`U2.6` — both LT3074 **PG** outputs are unconnected on a board whose purpose is monitoring. Deliberate? 
- Net names `SENSE_n` map to PAC1944 hardware channel `5−n`. A firmware hazard; worth renaming.
- With `J2` open as shipped, PMOD pin 4 (`CNTRL`) does nothing — the host cannot turn the LDOs off on an unmodified board.
- Twelve unplugged 0.25 mm vias inside the LDO paste openings (solder-wicking risk).
- `OUT_2` copper is 32 % smaller than `OUT_1` — an asymmetry on a comparison board.
- `U1.10` SENSE is tied to OUT at the package, so the pour neck and shunt sit outside the regulation loop (≥7.5 mV uncompensated at 3 A).
- ~20–25 µF of unlimited hot-plug inrush on the PMOD rail.

---

## Considered and rejected

Claims raised during review that did **not** survive verification. Recorded so they are not re-raised.

| Claim | Verdict | Why |
|---|---|---|
| The `125b2fa` watchdog fix is incomplete | **Correct as-is** | Pre-fix netlist regenerated from `125b2fa^`; the original bug was real and severe, and the fix is complete. No node floats into a CMOS input in either jumper state |
| MAX6373 SET0/1/2 float on an as-manufactured board | **Withdrawn** | Owner states JP1–JP3 are solder-blobbed before use. Only the labelling consequence survives, as F-06 |
| Released Gerbers are stale relative to the PCB | **Refuted** | Re-exported and compared as normalised (aperture, coordinate, operation) multisets: geometric difference **0** across all 13 layers; drill byte-identical; `.gbrjob` identical; `Gerbers.zip` matches |
| No ESD/series protection on the 8 PMOD signals | **Refuted** | Pmod spec §2 places the 200 Ω series resistors and ESD diodes on the **host** port, not the peripheral. Not a violation |
| Four ERC `multiple_net_names` aliases are accidental shorts | **Refuted** | All four deliberate. `SENSE_1_N`≡`SENSE_2_N` is *required* by the paralleling recipe. Kelvin integrity verified in the PCB |
| PCA9306 missing pull-ups (the classic error) | **Refuted** | Present on both sides: R10/R41 LV, R6/R7 HV. VREF2+EN/200 kΩ/100 n is verbatim TI Fig. 8-1 |
| R8 fitted ⇒ dead board as released | **Weakened → F-01** | JLC BOM omits R8, so it is most likely not placed. The defect is the contradiction between the two BOMs, not a dead board |
| `R18` ships at 10k with 0.21 V margin | **Refuted** | R18 is **1k** as built; real margin 1.52 V. The 10k case is hypothetical — it became F-14 |
| AD5272 A-terminal clamp forward-biased at default | **Refuted** | V_A = 3.33 V against 3.6 V abs max — 270 mV of margin. Only real at codes ≥ 576 |
| I²C on In4 splits GND; 18 B.Cu segments cross | **Weakened → F-15 scope** | The 5.08 mm² pocket is stitched by two GND vias, not orphaned. The headline "3.10 mm crossing at U2" is a **parallel run**, not a crossing. Genuine crossings: 6, not 18. F.Cu actually has *more* stretches than B.Cu (91 vs 84), contradicting "F.Cu is clean". Computed crosstalk is a few tens of mV — benign |
| 0.9 mm pour neck inadequate for 3 A | **Refuted** | Transverse conducting width is **1.20 mm**, not 0.9 mm. IPC-2221 gives 12.4 °C for a long uniform trace; the neck is 1.25 mm long between wide pours, so the real rise is single-digit. R = 0.51 mΩ, 4.6 mW |
| U4/U6/U8 rotations are errors; U5 is a missed correction | **Refuted** | The +180 edits are **convention-correct** — SOT-23-6, SOT-553, VSSOP-8 all carry +180 in the JLC table; VQFN/LFCSP carry 0, so U5 needs none. No part is demonstrably assembled backwards |
| No mounting holes is the mechanical defect | **Reframed → F-07** | The Pmod spec never mentions mounting holes. The real, spec-grounded issue is the 0.8661″ width against a 0.8″ clip requirement |
| `MFR_IOUT_MIN_WARN_LIMIT` is wrong-datasheet vocabulary | **Refuted** | The LT3074 *is* a PMBus 1.3 part. The claim stands on substance; only the page number (55, not 52) and the preload sizing were wrong |
