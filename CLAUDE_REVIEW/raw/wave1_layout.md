# Wave 1 — Layout and Manufacturing review

Design under review: `LDO_MON_PMOD_Board_V1/LDO_MON_PMOD_Board_V1.kicad_pcb` (KiCad 10.0.6, generator_version 10.0, board file version 20260206).
Everything below was measured by parsing the `.kicad_pcb` and the released Gerber/drill/BOM/placement files. Scripts kept:

- `CLAUDE_REVIEW/scripts/05_plane_return_path.py` — plane coverage, island count, and signal-vs-reference-plane continuity test (shapely).
- `CLAUDE_REVIEW/scripts/06_pcb_geometry.py` — pad transform (validated against the Gerber `%TO.P` flashes), via landing analysis, thermal-via census, silkscreen checks.

## Checks performed

| Check | Method (tool/parse/judgement) | Result | Notes |
|---|---|---|---|
| Stackup extraction | parse `setup/stackup` block | Done | 6 Cu, 1.600 mm total, arithmetic verified against `(general (thickness 1.6))` |
| Inner-layer purpose (copper area + nets) | shapely area of every `filled_polygon` per layer | Done | In1=GND, In2=3V3_PMOD, In3=SENSE_4_N (LDO VIN), In4=GND |
| Solid GND reference adjacent to both signal layers | stackup order + per-layer zone net | **Clean** | F.Cu→In1 GND at 0.100 mm prepreg; B.Cu→In4 GND at 0.100 mm prepreg |
| Impedance-relevant geometry | `dielectric_constraints`, netclass `diff_pair_*`, εr/thickness | No controlled-impedance class declared | εr 4.5, tanδ 0.02 declared; 0.1 mm trace over 0.1 mm FR4 ≈ 59 Ω single-ended (IPC microstrip approximation, my calculation) |
| Plane island/split count per inner layer | shapely `unary_union` + `MultiPolygon` geom count | In1/In2/In3 = 1 island each; **In4 GND = 2 islands** | 1264.7 mm² main + 5.1 mm² severed pocket at (109.0–111.8, 93.0–99.3) |
| Signal traces crossing a reference-plane gap | geometric difference of every F.Cu/B.Cu segment against the adjacent GND plane fill | **18 real crossings on B.Cu** | see F-LAY-2; the rest of the "unbacked" stretches are via/THT anti-pads, which are normal |
| SENSE_* lines vs reference plane | same test, filtered to SENSE nets | **Clean** | every SENSE_*/SENSE_*_FILT segment is fully over In1/In4 GND except ≤0.45 mm via anti-pad transitions |
| I2C lines vs reference plane | same test | **Not clean** | SCL/SDA/SCL_HV/SDA_HV are routed *on* In4, i.e. they *are* the gap — see F-LAY-2 |
| Kelvin sense tap geometry at R15/R16/R35/R39 | pad coordinate extraction | **Clean** | all four shunts tapped symmetrically 1.46–1.83 mm from the power-pad centres, into pour fingers in the inter-pad gap that carry no load current |
| Design rules in the project file | parse `.kicad_pro` `design_settings.rules` + `net_settings` | Done | see "Design rules vs fab" below |
| Actual minima used on the board | scan all 703 segments / 174 vias / PTH drill tool table | Done | min track 0.100 mm, min via 0.400/0.150 mm, min annulus 0.125 mm, min drill 0.150 mm |
| Clearance actually achieved | `drc_strict.rpt` (all rules enabled, exclusions shown) | **Clean** | 0 clearance, 0 track-width, 0 hole-size, 0 copper-to-edge violations |
| Min copper-to-board-edge | shapely distance, all tracks + pads vs Edge.Cuts rect | **Clean** | 0.550 mm (F.Cu `GPIO` track) vs 0.5 mm rule |
| The 4 DRC-excluded vias | per-layer landing test vs zones/tracks/pads | **Real defect, see F-LAY-1** | they are via-in-pad on U1.24/U2.24 that land copper on F.Cu *only* |
| LT3074 thermal layout | pad/via/zone geometry + LT3074 datasheet p.41 | Partially compliant — see F-LAY-1 / F-LAY-10 | IN e-pad path is good, OUT e-pad path is not |
| Silk graphics over pads | shapely intersection, all footprint silk shapes vs all exposed pads | **Clean** | 0 overlaps >0.002 mm² on either side |
| Silk text over pads | shapely intersection, text bounding boxes (approximate) vs pads | **Clean** | 0 overlaps >0.01 mm² |
| Missing/illegible refdes | parse `property "Reference"` layer + hide + font | **20 hidden refdes** — see F-LAY-8 | smallest visible refdes 0.8 mm high / 0.10 mm thick (U1, U2) |
| Silk stroke widths actually plotted | Gerber aperture census of the released silk layers | **0.10 and 0.12 mm strokes present** — see F-LAY-7 | 53 draws at 0.10 mm, 343 draws at 0.12 mm |
| D1/D2 pin-1 / polarity | footprint silk primitives | Marker present but 0.1 mm diameter — see F-LAY-7 | `fp_circle` centre (-1.09, 0), radius 0.05 mm |
| C9/C13 polarity | footprint silk primitives | No polarity marker (already-known footprint issue) | compounded: both are on B.Cu with *hidden* refdes — see F-LAY-8 |
| Connector pin-1 markers | pad shape + silk | **Clean** | P1.1, J1.1, J2.1, J3.1 are all `rect` pads (pin-1 convention); J3 has 11 silk primitives, P1 has 16 |
| Board outline | parse Edge.Cuts | **Clean, single `gr_rect`** | 94.92,89.00 → 165.00,111.00 = 70.08 × 22.00 mm, no slots/cutouts |
| Mounting holes | NPTH drill file + footprint scan | **None exist** — see F-LAY-13 | `-NPTH.drl` contains only the M48 header and M30 |
| PMOD edge geometry | P1 pad coordinates vs board edge | **Clean on pinout** | 2×6 on 2.54 mm pitch, 1.016 mm drill / 1.524 mm pad; GND on P1.5+P1.11 and VCC on P1.6+P1.12 — matches the 12-pin Pmod convention; header row is 3.81 mm (0.150") in from the left edge |
| Footprint courtyards vs board | shapely difference vs outline | 1 overhang (J3, 0.57 mm) — **expected** for a horizontal wire-entry terminal block |
| **Gerber release vs current PCB** | real re-export with `kicad-cli pcb export gerbers --no-protel-ext --check-zones` + `export drill`, then normalised geometric diff | **Clean — released Gerbers match the current board exactly** | see "Manufacturing data integrity" |
| Drill file release vs current PCB | re-export + byte diff | **Clean — byte-identical** (PTH and NPTH) |
| `Gerbers.zip` vs loose `Gerbers/` | unzip + diff | **Clean — identical** (zip copies use CRLF; content identical) |
| BOM ↔ schematic ↔ placement cross-check | csv/xlsx parse vs `components.tsv` | **2 real problems** — see F-LAY-3, F-LAY-4 | plus a rotation discrepancy, F-LAY-5 |
| Current-carrying pour bottlenecks | shapely negative-buffer erosion until the pour splits | **0.9 mm neck on OUT_1 and OUT_2** — see F-LAY-6 |
| Blind/buried/micro vias | via `layers` scan | **Clean — none** | all 174 vias are F.Cu–B.Cu through vias, so no HDI process class |

### Checks I could not do
- **Pmod mechanical mating depth.** `P1` uses the private library footprint `klib_connectors:pmod_pin_array_6x2`, which is not on the library path (`drc_strict.rpt` line: *"does not include the footprint library 'klib_connectors'"*). I can confirm the pad grid and the 3.81 mm edge setback, but I cannot tell from the board file whether the intended part is a vertical or a right-angle male header, so I cannot confirm the host mating geometry.
- **Actual θJA.** No thermal simulation was run; the thermal conclusions below are copper-area/via-count arguments against the LT3074 datasheet's stated layout requirement, not a computed junction temperature.
- **Exact JLCPCB price-tier boundaries.** I compared against JLCPCB's published 4/6-layer process capability (min trace/space 3.5 mil, min via 0.3 mm pad / 0.15 mm hole, min silk line 0.15 mm, min silk text 0.8 mm). Tier pricing changes; the numbers below are capability comparisons, and anything I call a "tier" risk is flagged as something to confirm with the fab.

---

## 1. Stackup

Read from the `(setup (stackup ...))` block, top to bottom:

| # | Layer | Type | Thickness (mm) | Material |
|---|---|---|---|---|
| | F.SilkS / F.Paste | — | — | |
| | F.Mask | mask | 0.010 | |
| L1 | **F.Cu** | copper | 0.035 (1 oz) | signal + pours |
| | dielectric 1 | **prepreg** | **0.100** | FR4, εr 4.5, tanδ 0.02 |
| L2 | **In1.Cu** | copper | 0.035 | **GND plane** |
| | dielectric 2 | core | 0.535 | FR4, εr 4.5 |
| L3 | **In2.Cu** | copper | 0.035 | **3V3_PMOD plane** |
| | dielectric 3 | prepreg | 0.100 | FR4, εr 4.5 |
| L4 | **In3.Cu** | copper | 0.035 | **SENSE_4_N plane** (= the LDO input rail) |
| | dielectric 4 | core | 0.535 | FR4, εr 4.5 |
| L5 | **In4.Cu** | copper | 0.035 | **GND plane** |
| | dielectric 5 | **prepreg** | **0.100** | FR4, εr 4.5 |
| L6 | **B.Cu** | copper | 0.035 | signal + small pours |
| | B.Mask | mask | 0.010 | |

Total = 6 × 0.035 + (0.100 + 0.535 + 0.100 + 0.535 + 0.100) + 2 × 0.010 = **1.600 mm**, matching `(general (thickness 1.6))`. `copper_finish "None"`, `dielectric_constraints no`.

Measured copper on each layer (board area = 70.08 × 22.00 = 1541.8 mm²):

| Layer | Zone net | Zone copper | Coverage | Islands | Routed tracks on the layer |
|---|---|---|---|---|---|
| F.Cu | 8 nets (SENSE_4_N 82.2, GND 57.4, SENSE_1_N 33.5, OUT_1 26.7, 3V3_PMOD 19.3, OUT_2 18.2, SENSE_3_N 16.3, SENSE_4_P 15.7 mm²) | 269.2 mm² | 17% | — | 350 segments |
| In1.Cu | GND | 1314.4 mm² | 85.3% | **1** | 2 segments, `Net-(U2-BIASAF)`, 4.57 mm |
| In2.Cu | 3V3_PMOD | 1254.4 mm² | 81.4% | 1 | 17 segments: BIAS (0.4 mm, 44.13 mm) + SET_RES_NODE (0.2 mm, 11.12 mm) |
| In3.Cu | SENSE_4_N | 1287.6 mm² | 83.5% | 1 | none |
| In4.Cu | GND | 1269.7 mm² | 82.4% | **2** | 43 segments: SCL, SDA, SCL_HV, SDA_HV — 94.4 mm of 0.1 mm track |
| B.Cu | SENSE_1_N 11.0, GND 7.6 mm² | 18.7 mm² | 1.2% | — | 291 segments |

**The reference-plane arrangement is correct and worth saying so explicitly:** both routing layers sit directly against a GND plane across a 0.100 mm prepreg (F.Cu↔In1, B.Cu↔In4), and the two power planes (3V3 on In2, VIN on In3) are sandwiched between the two GND planes. That is the right choice for a 6-layer board of this kind, and the GND planes are 82–85% filled with no large intentional splits. The problem is not the stackup; it is what has been routed *through* In4 (F-LAY-2).

Impedance-relevant geometry: no impedance class is declared (`dielectric_constraints no`, no netclass patterns, the Default netclass's `diff_pair_*` values are unused). For reference, the dominant 0.1 mm trace over the 0.100 mm prepreg to In1/In4 works out at roughly 59 Ω single-ended by the standard microstrip approximation (εr 4.5, t 35 µm) — my calculation, not a fab-verified number. Nothing on this board needs it (the fastest bus is 400 kHz–1 MHz I²C), so not ordering impedance control is correct and saves money.

## 2. Design rules vs JLCPCB 6-layer capability

| Parameter | Rule in the project | **Actual minimum used on the board** | JLCPCB 4/6-layer capability | Verdict |
|---|---|---|---|---|
| Track width | netclass 0.100 mm; `min_track_width` 0.100 | **0.100 mm** (349 of 703 segments) | 0.0889 mm (3.5 mil) | Within capability, ~11 µm of margin |
| Clearance | netclass 0.100 mm (`rules.min_clearance` is 0.0, so the netclass governs) | ≥0.100 mm (0 DRC clearance violations with all rules on) | 0.0889 mm | Within capability, ~11 µm of margin |
| Via diameter / drill | 0.400 / 0.150 mm | **0.400 / 0.150 mm** (35 vias); majority are 0.600 / 0.250 | 0.30 mm pad / **0.15 mm hole minimum** | Drill is **exactly at the fab minimum** |
| Annular ring | `min_via_annular_width` 0.100 | **0.125 mm** | 0.075 mm implied by 0.30/0.15 | Comfortable |
| PTH drills present | — | 0.150 (×43), 0.250 (×130), 0.300 (×1), 1.000 (×5), 1.016 (×12), 1.200 (×4) | 0.15 mm min | OK, 0.15 at the limit |
| Hole-to-hole | 0.250 mm | no violations | 0.25 mm | At the limit, passes |
| Copper to board edge | 0.500 mm | **0.550 mm** | ≥0.2 mm typical | Comfortable |
| Silk line width | project default `silk_line_width` 0.100 | **0.100 mm (53 draws) / 0.120 mm (343 draws)** | **0.15 mm minimum** | **Below the fab minimum — F-LAY-7** |
| Silk text | `min_text_height` 0.800, `min_text_thickness` 0.080 | 0.80 mm high, **0.10 mm thick** (U1, U2) | 0.8 mm high / 0.15 mm wide | Height at the limit, thickness below — F-LAY-7 |
| Via type | — | all 174 vias are F.Cu–B.Cu through vias | — | **No blind/buried/microvias — stays in the cheap process class** |
| Inner copper weight | stackup declares **0.035 mm (1 oz)** on In1–In4 | — | JLC's 6-layer default inner copper is 0.5 oz | **F-LAY-11** |

Nothing on this board pushes it into HDI, back-drill, or impedance-control pricing. The two things that do carry fab risk are the 0.15 mm drill (exactly at the limit) and the sub-0.15 mm silkscreen strokes.

## 3. Manufacturing data integrity (the high-value check)

I re-exported from the current `.kicad_pcb`:

```
kicad-cli pcb export gerbers --no-protel-ext --check-zones \
  --layers F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts
kicad-cli pcb export drill --format excellon --drill-origin absolute --excellon-separate-th --excellon-units mm
```

and compared against `MANUFACTURING_DATA/Gerbers/`. Raw text diff is misleading because the X2 aperture D-codes are renumbered and the per-net blocks are emitted in a different order, so I normalised each file to the multiset of `(aperture definition, coordinate, operation)` tuples with the `%TO`/`%TD` attributes stripped:

| File | ops in release | ops in re-export | **geometric difference** |
|---|---|---|---|
| F_Cu | 1583 | 1583 | **0** |
| In1_Cu | 5659 | 5659 | **0** |
| In2_Cu | 7718 | 7718 | **0** |
| In3_Cu | 8094 | 8094 | **0** |
| In4_Cu | 5171 | 5171 | **0** |
| B_Cu | 960 | 960 | **0** |
| F/B_Mask, F/B_Paste, F/B_Silkscreen, Edge_Cuts | — | — | **0** each |
| `-PTH.drl`, `-NPTH.drl` | — | — | **byte-identical** after stripping the date comment |
| `-job.gbrjob` | — | — | **identical** after stripping the date |

The *only* difference anywhere is the `G04 Created by KiCad ... date` comment line and, in `F_Cu`, the order in which the `ENABLE` and `Net-(J2-Pin_2)` track blocks are emitted — same segments, same apertures, same coordinates, just grouped differently by the plotter.

`MANUFACTURING_DATA/Gerbers.zip` unpacks to 16 files that are identical to the loose `MANUFACTURING_DATA/Gerbers/` directory (the zipped copies use CRLF line endings; content matches line-for-line).

**Conclusion: the released manufacturing data is current.** Despite the Gerbers being committed in `402f743`/`ec3514f` separately from the PCB edits, commit `125b2fa` ("Fixed problem with watchdog enable bypass") re-exported them, and what is in the repo today is a faithful plot of today's `.kicad_pcb`. The fabricated board will match the design. This is a clean result and I want it on the record as having been verified concretely rather than assumed.

One minor note: `pcbplotparams.outputdirectory` is `"../MANUFACTURING_DATA/Gerbers/"`, so the GUI export lands in the right place — that is why the two stayed in sync. Good practice, keep it.

---

## Findings

### F-LAY-1: U1/U2 OUT exposed-pad thermal vias land on copper on the top layer only — the DRC exclusion should be removed, not kept
- **Severity:** Should-fix
- **Confidence:** High
- **Where:** vias at (129.4, 98.1), (129.4, 98.9) net `OUT_1`; (129.4, 107.1), (129.4, 107.9) net `OUT_2`. Pads `U1.24 OUT3_EPAD_24` at (129.385, 98.500) and `U2.24 OUT3_EPAD_24` at (129.385, 107.500). Exclusions recorded in `LDO_MON_PMOD_Board_V1.kicad_pro` → `design_settings.drc_exclusions` (the four `via_dangling|129400000|...` entries).
- **Evidence:** The brief's hypothesis was that these are LDO thermal/current vias, and that is exactly what they are *meant* to be — but they do not work. Pad `U1.24` is plotted in the released `F_Cu.gbr` at `X129385000Y-98500000` with aperture `%ADD23RoundRect,...0.4464...0.8314...`, i.e. 0.93 × 1.70 mm spanning x 128.92–129.85, y 97.65–99.35. Both vias sit well inside that rectangle, so they *are* connected at the top. Running the per-layer landing test (`06_pcb_geometry.py`) over all 174 vias, these four are the only ones in the design that land copper on exactly one layer:
  ```
  (129.4,98.9)  net=OUT_1  size=0.6/0.25  lands=['F.Cu:pad U1.24']
  (129.4,98.1)  net=OUT_1  size=0.6/0.25  lands=['F.Cu:pad U1.24']
  (129.4,107.1) net=OUT_2  size=0.6/0.25  lands=['F.Cu:pad U2.24']
  (129.4,107.9) net=OUT_2  size=0.6/0.25  lands=['F.Cu:pad U2.24']
  ```
  There is no `OUT_1`/`OUT_2` copper on In1, In2, In3, In4 or B.Cu anywhere on the board (total `OUT_1` zone copper = 26.7 mm², all on F.Cu; `OUT_2` = 18.2 mm², all on F.Cu). KiCad's own message is precise about this: *"Via is not connected **or connected on only one layer**"* — it is the second clause that applies. Contrast the IN e-pad on the same parts, which is done correctly: the four vias inside `U1.23`/`U2.23` at (127.6/128.3, 98.1/98.9) and (127.6/128.3, 107.1/107.9) all land on the In3 `SENSE_4_N` plane (1287.6 mm²).
  LT3074 datasheet p.41, *Thermal Considerations*: *"The IN and OUT pins at the bottom of the package should be soldered to IN and OUT planes accordingly. In addition, the IN **and OUT** must be connected to large copper layers below with thermal vias; these layers spread heat dissipated by the LT3074."* (Verified against the datasheet; the IN half is satisfied, the OUT half is not.)
- **Why it matters:** θJCBOT for this package is 3.5 °C/W versus θJCTOP 47 °C/W (datasheet Table 3, p.10), so essentially all the heat leaves through the two bottom e-pads. Half of that path — the OUT e-pad — currently terminates in 26.7 mm² (U1) / 18.2 mm² (U2) of 35 µm top-layer copper plus two vias that are open-circuit at the far end and spread nothing. For a 3 A LDO the device will run hotter than the datasheet's 33 °C/W demo-board figure; worse, the exclusion makes the problem invisible to future DRC runs, so it will survive the next revision. Mechanically the four holes also punch anti-pads through all four planes immediately beside the hottest part on the board, for no benefit.
- **Suggested fix:** Do **not** keep the exclusion. Either (a) give `OUT_1`/`OUT_2` real destination copper — a B.Cu pour under each LDO on the OUT net, stitched with these vias plus a few more under `U1.24`/`U2.24` — which is what the datasheet asks for and is cheap here because B.Cu is only 1.2% covered; or (b) if there is genuinely nowhere for OUT copper to go, delete the four vias so they stop perforating the planes, and delete the four `via_dangling` entries from `drc_exclusions`. Option (a) is strongly preferred.

### F-LAY-2: the whole I²C bus is routed *on* the In4 GND plane, severing it into two islands and breaking the return path of 18 B.Cu signal segments
- **Severity:** Should-fix
- **Confidence:** High
- **Where:** In4.Cu — nets `SCL` (9 segments, 24.62 mm), `SDA` (10 segments, 26.98 mm), `SCL_HV` (13 segments, 20.93 mm), `SDA_HV` (11 segments, 21.86 mm), all at 0.100 mm width. Affected B.Cu nets listed below.
- **Evidence:** In4.Cu is the GND reference plane for B.Cu (0.100 mm prepreg, `dielectric 5`). Running `05_plane_return_path.py`, the In4 GND fill resolves to **two** disjoint islands — 1264.7 mm² plus a 5.1 mm² pocket bounded by (109.0, 93.0)–(111.8, 99.3) — whereas In1, In2 and In3 are each a single island. The pocket is cut off by the `SCL`/`SDA` pair running up through that area; it does still have 2 GND vias in it, so it is not floating copper, but it is a severed piece of reference plane.
  Testing every B.Cu segment against the In4 GND fill and attributing each unbacked stretch to its nearest cause gives 18 crossings of ≥0.3 mm whose nearest feature is an In4 I²C track (not a via or through-hole anti-pad):
  ```
   3.10 mm  B.Cu ALERT_N          mid=(130.20,106.65)  0.20 mm from SDA_HV-on-In4
   1.56 mm  B.Cu ALERT_N          mid=(128.80,109.25)  0.05 mm from SCL_HV-on-In4
   1.38 mm  B.Cu SET_CAP_NODE     mid=(128.89,104.00)  0.36 mm from SDA_HV-on-In4
   1.34 mm  B.Cu Net-(U1-CLKDIS)  mid=(126.33,100.55)  0.05 mm from SCL_HV-on-In4
   1.13 mm  B.Cu ALERT_N          mid=(122.40,100.40)  0.20 mm from SCL_HV/SDA_HV-on-In4
   1.08 mm  B.Cu Net-(U1-VIOC)    mid=(126.46, 99.70)  0.00 mm from SDA_HV-on-In4
   1.07 mm  B.Cu ENABLE           mid=(114.45, 98.10)  0.18 mm from SCL/SDA-on-In4
   1.06 mm  B.Cu Net-(U1-VIOC)    mid=(127.38,100.08)  0.22 mm from SCL_HV-on-In4
   1.06 mm  B.Cu Net-(U2-ASEL)    mid=(127.18,104.68)  0.33 mm from SCL_HV-on-In4
   1.00 mm  B.Cu ALERT_N          mid=(127.70,103.90)  0.15 mm from SCL_HV-on-In4
   0.99 mm  B.Cu ALERT_N          mid=(118.05, 96.05)  0.15 mm from SCL/SDA-on-In4
   0.85 mm  B.Cu Net-(U2-EN)      mid=(126.30,107.60)  0.07 mm from SCL_HV-on-In4
   0.85 mm  B.Cu Net-(U1-VIOC)    mid=(118.50, 96.10)  0.10 mm from SDA-on-In4
   0.80 mm  B.Cu BIAS             mid=(126.40,105.40)  0.20 mm from SCL_HV-on-In4
   (+ 4 more between 0.3 and 0.8 mm: ALERT_N ×2, Net-(U2-IMON) ×2)
  ```
  For contrast, the F.Cu↔In1 reference came back essentially perfect: In1 carries only 4.57 mm of routing (`Net-(U2-BIASAF)`), and **every** F.Cu "unbacked" stretch the test found is a ≤0.45 mm via anti-pad or a P1/J2/J3 through-hole anti-pad, which is normal and unavoidable. The SENSE_* nets are likewise clean on both layers.
- **Why it matters:** This is the classic return-path error and it lands on the two things that matter most here. (i) `ALERT_N` is the LDO/PAC1944 open-drain interrupt and it crosses the slot seven times, including one 3.10 mm stretch at (130.2, 106.65) right at U2 — its return current has to detour around the slot, enlarging the loop and coupling into whatever else shares the detour. (ii) The victim list is almost entirely LT3074 control pins — `Net-(U1-VIOC)`, `Net-(U1-CLKDIS)`, `Net-(U2-EN)`, `Net-(U2-ASEL)`, `SET_CAP_NODE`, `ENABLE`, `BIAS` — i.e. high-impedance analogue and configuration nodes next to a 3 A regulator, which is exactly where injected noise turns into output ripple or spurious enable/disable. And the aggressor is the I²C bus itself, which on this board is the measurement channel: noise coupled from SCL/SDA edges into `SET_CAP_NODE` or `VIOC` corrupts the very thing the PAC1944 is measuring.
- **Suggested fix:** Move SCL, SDA, SCL_HV and SDA_HV off In4. There is plenty of room: B.Cu is only 1.2% covered by zones and F.Cu 17%, and In2 (3V3 plane) is *not* a reference layer for any routing layer, so it is a far better place to bury a slow bus if an inner layer is really needed. If the I²C must stay on In4, at minimum reroute it so the four nets run as one bundled channel hugging the board edge rather than crossing the U1/U2 control-pin fan-out area, and add GND stitching vias along both sides of the resulting slot. Re-run `05_plane_return_path.py` afterwards; the target is zero crossings attributable to an In4 track.

### F-LAY-3: R8 is missing from the JLC-formatted BOM, so the LT3074 SET-resistor network will not be populated
- **Severity:** Should-fix
- **Confidence:** High
- **Where:** `MANUFACTURING_DATA/BOM/LDO_MON_PMOD_Board_V1_BOM_JLC_FORMATTED.xlsx`, the `0R` row. R8 at (130.2, 95.8) on F.Cu, `Resistor_SMD:R_0402_1005Metric`.
- **Evidence:** Cross-checking the three sources:
  - `CLAUDE_REVIEW/raw/components.tsv`: `R8  0R  Resistor_SMD:R_0402_1005Metric`
  - `MANUFACTURING_DATA/BOM/..._BOM.csv` line 26: `"R8,R26,R36","3","0R",...` — R8 **is** present, qty 3
  - `..._BOM_JLC_FORMATTED.xlsx`: `('0R', 'R26,R36', 'Resistor_SMD:R_0402_1005Metric', 'C60485')` — **R8 dropped, qty effectively 2**
  - `..._POSITION_JLC_FORMATTED.xlsx` / `-all-pos.csv`: R8 **is** present
  R8 is the only designator in the whole placement file with no row in the JLC BOM (`set(placement) - set(jlc_bom) == {'R8'}`). From `nets.tsv`, `SET_RES_NODE  4  R36.2 R8.1 U1.13(SETRES_13) U2.13(SETRES_13)` and R8.2 is on `GND`.
  Everything else cross-checks clean: 0 value mismatches, 0 footprint mismatches, 0 quantity-vs-designator-count mismatches across 35 BOM rows, and no part in the BOM that is absent from the schematic.
- **Why it matters:** `SET_RES_NODE` is the LT3074 SETRES pin for *both* regulators, and R8 is the 0 Ω link from that node to GND. Order this BOM as-is and JLC ships the board with R8 unpopulated, leaving the SETRES network open-circuit at the GND end for U1 and U2 simultaneously. That is a both-channels-wrong assembly defect on the board's primary function, discovered only at bring-up.
- **Suggested fix:** Change the `0R` row's Designator cell to `R8,R26,R36` (LCSC C60485 already selected). Then re-run the three-way cross-check — the script in this review is the eight lines of `csv`/`openpyxl` set arithmetic in the Checks table; it is worth saving as a release gate because the hand-maintained xlsx is clearly diverging from the KiCad-generated CSV.

### F-LAY-4: U3 (MAX6373) and U7 (AD5272) have no LCSC part number in the JLC BOM
- **Severity:** Should-fix
- **Confidence:** High
- **Where:** `..._BOM_JLC_FORMATTED.xlsx` rows `('MAX6373', 'U3', 'Package_TO_SOT_SMD:SOT-23-8', None)` and `('AD5272BCP', 'U7', 'Package_CSP:LFCSP-WD-10-1EP_3x3mm_P0.5mm_EP1.64x2.38mm', None)`.
- **Evidence:** Those are the only two of the 35 BOM rows with an empty `JLCPCB Part #` column. Every other row has one (the LT3074 itself is C44238296, the PAC1944 is C3688047). `components.tsv` has no MPN or LCSC column populated for any of the 118 parts, so the xlsx is the only place part numbers exist.
- **Why it matters:** These are not passives — U3 is the watchdog and U7 is the digital potentiometer, i.e. two of the eight active devices. JLC will either reject the order or return the boards with both ICs unpopulated, and both are fine-pitch (SOT-23-8 and a 3×3 mm LFCSP with a 1.64 × 2.38 mm exposed pad) so hand-fitting U7 afterwards is genuinely difficult. The LFCSP in particular has an exposed pad that cannot be reworked with an iron.
- **Suggested fix:** Either source them on LCSC and fill the cells, or mark both rows explicitly as customer-supplied / "do not place" in the order notes so the e-pad part is at least reflowed with the rest if you consign the parts. Do not leave the cell blank and silent.

### F-LAY-5: U4, U6 and U8 have different rotations in the JLC placement xlsx than in the KiCad placement CSV
- **Severity:** Should-fix
- **Confidence:** Medium
- **Where:** `MANUFACTURING_DATA/Placement/LDO_MON_PMOD_Board_V1_POSITION_JLC_FORMATTED.xlsx` vs `..._-all-pos.csv`.
- **Evidence:** Comparing all 107 rows field-by-field, X, Y and Layer agree exactly everywhere, and **only** the rotation differs, on exactly three parts:
  | Ref | Part | `.kicad_pcb` placement | CSV rotation | **xlsx rotation** |
  |---|---|---|---|---|
  | U4 | 74LVC1G175, SOT-23-6 | `(at 113.51 103.2)` — no angle, i.e. 0° | 0 | **180** |
  | U6 | 74LVC1G08, Texas R-PDSO-N5 (SOT-553) | `(at 118 104.2)` — 0° | 0 | **180** |
  | U8 | PCA9306, VSSOP-8 | `(at 114.4 98.7)` — 0° | 0 | **180** |
  The board file confirms all three are placed at 0°, so the xlsx was hand-edited after export. Note that the other three 0°-placed actives (U5 VQFN-16 at 0°, and U3 SOT-23-8 at 0°) were *not* adjusted, and U7/Q1, which are genuinely at 180° in the board, carry 180 in both files.
- **Why it matters:** Either reading is defensible — LCSC's reel orientation for some packages differs from KiCad's footprint pin-1 convention, and adding 180° is the standard workaround — but the edit was applied to three parts and not to the other same-situation parts, which is the signature of an ad-hoc fix rather than a systematic one. If the 180° is wrong, U4 (the watchdog D flip-flop), U6 (the AND gate in the enable path) and U8 (the I²C level translator) are all assembled backwards, which on a SOT-23-6/SOT-553/VSSOP-8 means power and ground are swapped on at least one of them. If the 180° is right, U3 and U5 may be the ones that are wrong.
- **Suggested fix:** Decide the rule once, per package, against the LCSC product page's reel drawing for each specific part number, write it down next to the BOM, and apply it consistently to every part in that package — then regenerate the xlsx from the CSV by script rather than editing it by hand. Until that is resolved, ask JLC for a placement preview and check these five parts (U3, U4, U5, U6, U8) on it before releasing to production.

### F-LAY-6: the OUT_1 / OUT_2 pours neck down to ~0.9 mm immediately at the LDO outputs, and that is the only path for the full load current
- **Severity:** Should-fix
- **Confidence:** Medium
- **Where:** `F.Cu` zone on `OUT_1` (priority 5, 26.7 mm², bounds 129.7–137.4 × 97.9–104.9) and the matching `OUT_2` zone (priority 4, 18.2 mm², bounds 129.7–137.3 × 106.1–109.8). Neck located at approximately (131.1, 99.2) for U1 and (131.4, 107.5) for U2.
- **Evidence:** Eroding each pour until it splits (negative buffer, 0.05 mm steps) gives a first split at r = 0.45 mm on both, i.e. a minimum width of **≈0.9 mm**; at r = 0.45 the pour separates into a small piece bounded by (130.1, 98.4)–(131.0, 98.7) and the main body from (131.5, 99.2) outward. The OUT_1 zone outline confirms the pinch — the vertex list runs `(129.7, 99.1) → (130.9, 99.1) → (131.1, 99.3) → (131.1, 100.5)` with the opposite side cutting across at `(130.9, 97.9) → (132.0, 99.0)`. There is no `OUT_1`/`OUT_2` copper on any other layer (see F-LAY-1), so this 0.9 mm × 35 µm cross-section is the entire conductor between U1's output pins (`U1.8/9/10` at x 130.4 and e-pad `U1.24`) and the 2 mΩ shunt R15 at (136.537, 103.000).
- **Why it matters:** The LT3074 is specified to 3 A and the datasheet's worked example (p.41) uses 3 A. By IPC-2221 for an external layer, 0.9 mm of 1 oz copper at 3 A is about a 20 °C rise — and this particular 0.9 mm sits a millimetre from a part that is itself dissipating ~1 W, so the local ambient for that neck is already elevated. It also adds series resistance inside the sense loop's supply path. For a demonstration board whose purpose is accurate current measurement, a self-heating bottleneck in the output path is the wrong kind of surprise.
- **Suggested fix:** Redraw the OUT pour outlines to carry the full pad width straight out to the shunt — the space is there, the neck is caused by the zone outline clipping diagonally around (131, 99) rather than by any obstruction. Combining this with F-LAY-1 (add a B.Cu OUT pour stitched through the e-pad vias) fixes both the thermal and the current-density problem with the same edit.

### F-LAY-7: silkscreen stroke widths of 0.10 and 0.12 mm are below the fab's 0.15 mm minimum; the D1/D2 cathode marker is a 0.1 mm dot
- **Severity:** Nice-to-have
- **Confidence:** High
- **Where:** project `defaults.silk_line_width` = 0.100; `LDO_MON_PMOD_Board_V1-F_Silkscreen.gbr` and `-B_Silkscreen.gbr`. D1 at (105.8, 90.81), D2 at (105.8, 93.1), both `LED_SMD:LED_0402_1005Metric`.
- **Evidence:** Aperture census of the released silk Gerbers (these are the actual plotted widths, not the project default):
  ```
  F_Silkscreen:  0.100 mm → 53 draws   0.120 mm → 228 draws   0.150 mm → 1651   0.200 mm → 15   0.3048 mm → 5
  B_Silkscreen:                        0.120 mm → 115 draws   0.150 mm → 1470                   0.3048 mm → 5
  ```
  So 396 of ~3500 silk draws are thinner than 0.15 mm. The D1/D2 polarity marker is `(fp_circle (center -1.09 0) (end -1.04 0) (layer "F.SilkS"))` — a circle of **0.05 mm radius**, i.e. a 0.1 mm dot, which is the only cathode indication on either LED (the remaining D1/D2 polarity graphics are all on F.Fab, which is not plotted for fabrication). U1 and U2 are also the only two refdes in the design at 0.10 mm stroke (0.8 × 0.8 mm text).
- **Why it matters:** JLCPCB's stated minimum silkscreen line width is 0.15 mm; below that they either drop the feature or print it inconsistently. The realistic outcome is that the 0.1 mm LED cathode dots do not appear at all, leaving D1 and D2 with no visible polarity indication on a board where both are 0402 — so a hand-reworked or hand-assembled LED has a 50% chance of being fitted backwards with nothing on the board to catch it. The 0.12 mm strokes are the component outlines on most of the passives; they will print but thin and inconsistently. U1/U2's 0.10 mm refdes is the one on the two most important parts.
- **Suggested fix:** Set `silk_line_width` to 0.15 and `silk_text_thickness` to 0.15 in Board Setup, then use *Edit → Edit Text and Graphic Properties* to push 0.15 mm onto all existing silk items (this does not move anything, so it will not disturb the layout). For D1/D2, replace the 0.1 mm dot with a proper cathode bar or a "K"/triangle at ≥0.15 mm stroke. After the change, re-export and re-run the Gerber aperture census — it should show no aperture below 0.15 mm.

### F-LAY-8: 20 reference designators are hidden, including all three user-configurable solder jumpers and both bottom-side polarised capacitors
- **Severity:** Nice-to-have
- **Confidence:** High
- **Where:** 20 footprints with `(property "Reference" ... (hide yes))`:
  - F.SilkS hidden (11): **JP1, JP2, JP3**, C11, C48, C51, R7, R17, R20, R23, R26
  - B.SilkS hidden (9): **C9, C13**, C17, C19, C35, C36, C40, C41, C42
- **Evidence:** Parsed directly from the `.kicad_pcb`; every one of these is `(layer "F.SilkS"/"B.SilkS")` with `(hide yes)`, so the designator exists but is not plotted. Confirmed against the released silk Gerbers. Separately, every footprint on the board does have *some* silk outline (0 footprints with zero silk graphics), so the outlines are fine — it is specifically the refdes text that is suppressed.
- **Why it matters:** Three cases are materially worse than the rest:
  - **JP1, JP2, JP3** are `SolderJumper-3_P1.3mm_Open` three-pad jumpers selecting between GND and 3V3_PMOD (from `nets.tsv`: `JP1.1/JP2.1/JP3.1` on GND, `JP1.3/JP2.3/JP3.3` on 3V3_PMOD, centres on `Net-(JPn-C)`). These are the board's configuration straps — the one class of feature a user physically has to find and modify — and they are at (106.5, 107.7), (109.0, 107.7) and (111.5, 107.7), i.e. three identical jumpers in a row 2.5 mm apart with nothing on the silk to tell them apart. They are also `exclude_from_bom`, so there is no BOM line to disambiguate them either.
  - **C9 and C13** are the two parts already known to carry a polarised symbol on a non-polarised 0603 footprint. On top of that they are on the **bottom** side with their refdes hidden and no polarity marker in their silk (`fp_line` ×2 only, the standard 0603 side bars). So for those two specific parts there is no identification *and* no orientation information anywhere on the physical board.
  - The remaining 15 are ordinary passives; hiding them is a legitimate density choice but it makes rework and debug harder on a board that is 52/55 double-sided.
- **Suggested fix:** At minimum un-hide JP1/JP2/JP3 and add a short silk label for what each selects, and un-hide C9/C13. For the rest, un-hide where there is room; where there genuinely is not, that is an accepted trade-off — but record it, because the assembly drawing is the only remaining identification.

### F-LAY-9: twelve unplugged 0.25 mm vias sit inside the LT3074 solder-paste openings
- **Severity:** Nice-to-have
- **Confidence:** Medium
- **Where:** `U1.23`/`U2.23` (4 vias each, net `SENSE_4_N`) and `U1.24`/`U2.24` (2 vias each, nets `OUT_1`/`OUT_2`). Board setup: `(tenting (front yes) (back yes))`, `(covering (front no) (back no))`, `(plugging (front no) (back no))`, `(capping no)`, `(filling no)`.
- **Evidence:** All twelve vias are 0.6 mm pad / **0.25 mm drill** and all twelve fall inside the exposed-pad rectangles (`06_pcb_geometry.py` thermal-via census). The released `F_Paste.gbr` flashes a single solid aperture over each e-pad — `%ADD20RoundRect,0.000000X0.415000X-0.800000X...` over `X129385000Y-98500000`, i.e. 0.83 × 1.60 mm of paste on a 0.93 × 1.70 mm pad, about **84% paste coverage with no windowpaning**. `F_Mask.gbr` has a matching full opening at the same coordinate, so front tenting does not apply inside the pad; the back annuli are tented by `B_Mask`.
- **Why it matters:** 84% solid paste over a small e-pad already tends to float the part; adding six open 0.25 mm barrels per device gives the molten solder somewhere to run during reflow. The usual results are voiding under the e-pad (which directly degrades the θJCBOT = 3.5 °C/W path that this layout depends on) and inconsistent standoff between U1 and U2 — unhelpful on a board whose purpose is to compare two supposedly identical channels. Note this is an inference from standard assembly practice plus the measured geometry, not something the LT3074 datasheet states.
- **Suggested fix:** Pick one: order JLC's via-in-pad option (epoxy-filled and capped) for these twelve, or tent them from the top and move them just outside the pad with short fat spokes, or split the e-pad paste into 2–4 windows at ~60–70% coverage placed to avoid the barrels. The first is the cleanest given the vias are load-bearing for the thermal path.

### F-LAY-10: U1 and U2 are not treated consistently — OUT_2's copper is 32% smaller than OUT_1's
- **Severity:** Nice-to-have
- **Confidence:** High
- **Where:** F.Cu zone on `OUT_1` (uuid priority 5) = **26.7 mm²**; F.Cu zone on `OUT_2` (priority 4) = **18.2 mm²**.
- **Evidence:** Side-by-side, the two channels are identical in every respect I measured *except* this: both LDOs are the same footprint at the same orientation (`(at 128.5 98.5 90)` and `(at 128.5 107.5 90)`), both IN e-pads have 4 vias to the same In3 plane, both OUT e-pads have the same 2 dead vias, both OUT pours have the same ~0.9 mm neck, and both feed an identical 2 mΩ shunt (R15 at y 103.000, R16 at y 107.910). The output pour area is the one asymmetry.
- **Why it matters:** The entire point of the board is to compare two LT3074 channels through a 4-channel monitor. A 32% difference in output-side copper means a different thermal environment and a slightly different series resistance between the two channels, so any measured difference between channel 1 and channel 2 is partly an artefact of the layout rather than of the parts. For a demo/characterisation board that is a measurement-credibility problem, not just an aesthetic one.
- **Suggested fix:** Make the two OUT pours the same shape and area. Since F-LAY-1 and F-LAY-6 both want these pours reworked anyway, do all three in one edit and mirror U2's copper from U1's.

### F-LAY-11: the stackup declares 1 oz inner copper and a non-catalogue dielectric split
- **Severity:** Nice-to-have
- **Confidence:** Medium
- **Where:** `setup/stackup` — In1–In4 each `(thickness 0.035)`; dielectrics 0.100 / 0.535 / 0.100 / 0.535 / 0.100 mm.
- **Evidence:** All six copper layers are declared at 35 µm. JLCPCB's 6-layer boards ship from a fixed set of published stackups and the default inner-layer copper weight for 6-layer is 0.5 oz (≈17 µm), with 1 oz inner as a chargeable option; the dielectric thicknesses are likewise fixed per stackup and are not customer-specified. The board's 0.1/0.535/0.1/0.535/0.1 split sums correctly to 1.6 mm but was almost certainly typed in rather than copied from a fab stackup.
- **Why it matters:** Two consequences, both small but real. (i) If the order goes through with default 0.5 oz inners, the GND and power planes have half the declared copper — which matters most for In3, the `SENSE_4_N` VIN plane that carries the input current for both 3 A LDOs and doubles as the IN e-pad heatsink (F-LAY-1). (ii) The F.Cu→In1 and B.Cu→In4 prepreg is declared at 0.100 mm; if the delivered stackup uses a different prepreg there, the ~59 Ω microstrip figure moves. Nothing here needs controlled impedance, so (ii) is informational — but (i) is worth getting right.
- **Suggested fix:** Pick JLC's actual 6-layer 1.6 mm stackup from their stackup page, enter those exact dielectric thicknesses and copper weights in Board Setup, and if the 1 oz inners are wanted for the VIN plane, order them explicitly. Then re-export the Gerbers so the `.gbrjob` carries the right `BoardThickness`/layer data.

### F-LAY-12: `min_silk_clearance` is 0, so KiCad never checked silk against pads
- **Severity:** Nice-to-have
- **Confidence:** High
- **Where:** `.kicad_pro` → `design_settings.rules.min_silk_clearance: 0.0`.
- **Evidence:** With the value at 0 the silk-overlap rule is inert, which is why `drc_strict.rpt` shows no silk findings despite being run with all rules enabled. I therefore did the check independently: intersecting every footprint silk primitive and every silk text bounding box against every exposed pad returned **0 overlaps** on F.SilkS and 0 on B.SilkS. So the board is in fact clean — but it is clean by luck of good footprints, not because anything verified it.
- **Why it matters:** The next layout edit that nudges a refdes over a pad will not be caught. Silk on a pad causes solder defects and is one of the cheapest classes of error to catch automatically.
- **Suggested fix:** Set `min_silk_clearance` to 0.15 mm and re-run DRC. Expect a handful of new warnings on the denser 0402 clusters; they are worth triaging once.

### F-LAY-13: no mounting holes — a 70 mm board cantilevered off a 12-pin header
- **Severity:** Nice-to-have
- **Confidence:** High
- **Where:** `LDO_MON_PMOD_Board_V1-NPTH.drl` contains only `M48 / FMAT,2 / METRIC / % / G90 / G05 / M30` — zero holes. Board outline is a single `gr_rect` 94.92,89.00 → 165.00,111.00 = **70.08 × 22.00 mm**. P1 pads are at x 98.73 / 101.27, i.e. the outer row is 3.81 mm from the left edge.
- **Evidence:** The Pmod electrical interface itself checks out — 2×6 on 2.54 mm pitch, 1.016 mm drill in 1.524 mm pads, pin 1 marked by a `rect` pad at (101.27, 93.65), and GND on P1.5/P1.11 with VCC on P1.6/P1.12, which is the standard 12-pin Pmod arrangement. The issue is purely mechanical: the board extends 63.7 mm to the right of the connector with nothing supporting it, and carries a `CP_Elec_8x10` 220 µF can (C6 at 139.9, 94.7) plus a Phoenix MC 1,5/4-G-3.5 screw terminal (J3 at 157.07, 105.195) whose courtyard overhangs the right edge by 0.57 mm — i.e. the heaviest parts and the one connector that will be tugged by field wiring are both at the far end of the cantilever.
- **Why it matters:** Tightening wires into J3, or any sideways force on it, levers directly on P1's twelve 1.016 mm through-holes. This is how Pmod headers get torn off their pads. For a demo board that people will repeatedly rewire, it is a predictable field failure.
- **Suggested fix:** Add two M2.5 or M3 NPTH mounting holes — one near J3 and one mid-board — with a `(keepout)` zone around each so the planes stay clear, and re-export (the NPTH file is currently empty, so this is the one change that will actually add a file's worth of content). If board area is too tight, at least add one near J3 so the terminal block's reaction force goes into a standoff rather than into P1.

### F-LAY-14: cosmetic defects in the released BOM/placement files
- **Severity:** Nice-to-have
- **Confidence:** High
- **Where:** `MANUFACTURING_DATA/BOM/LDO_MON_PMOD_Board_V1_BOM.csv`, `MANUFACTURING_DATA/Placement/`.
- **Evidence:**
  - Every row of the CSV BOM has the literal string `${EXCLUDE_FROM_POS_FILES}` in the *"Exclude from Position Files"* column — an unresolved KiCad field variable, not a value.
  - `J1, J2, J3, P1, TP1, TP2, TP3, TP4` appear in the CSV BOM but in **neither** placement file. For TP1–TP4 (test pads) that is correct. For P1 (the Pmod header) and J1/J2/J3 (two pin headers and the Phoenix terminal) it means four real, orderable, through-hole parts have no position data at all.
  - `JP1, JP2, JP3` are in the schematic but in no BOM — correct, they are `exclude_from_bom` solder jumpers.
  - No part in either BOM is flagged DNP, and `components.tsv` has no DNP flags either, so DNP is consistent (vacuously) across all three sources.
- **Why it matters:** The `${EXCLUDE_FROM_POS_FILES}` string will confuse anyone reading the CSV and suggests the BOM preset is misconfigured. The missing THT positions are fine if hand-assembly of the four connectors is the plan, but that intent is nowhere recorded — and P1 in particular has no LCSC number either (it is not in the JLC BOM at all), so there is currently no document that tells anyone what the Pmod header actually is.
- **Suggested fix:** Fix the BOM field template so the column resolves. Add a short `MANUFACTURING_DATA/README` stating that P1/J1/J2/J3 are customer-fitted through-hole parts with their manufacturer part numbers, and that TP1–TP4 and JP1–JP3 are board features rather than parts.

---

## Summary

The release is in better shape than the brief's priors suggested in one important respect and worse in another.

**The Gerber release is current** — I re-exported from today's `.kicad_pcb` and the geometric content of all thirteen copper/mask/paste/silk/outline layers plus both drill files is identical to what is committed, and `Gerbers.zip` matches the loose directory. The split commits did not leave a stale release behind.

**The four DRC-excluded vias are a real defect, not a false positive.** They are via-in-pad on the LT3074 OUT exposed pads — so the brief's "likely LDO thermal vias" reading was right about intent — but they land copper on the top layer only, because `OUT_1` and `OUT_2` have no copper anywhere except a small F.Cu pour. The IN exposed pad on the same parts is done correctly (4 vias into the 1288 mm² In3 plane), which makes the OUT side look like an unfinished edit. The exclusion should be removed and the OUT thermal path completed.

The one genuinely structural layout problem is the **I²C bus routed on the In4 GND plane**, which splits that plane into two islands and leaves 18 B.Cu segments — mostly LT3074 control pins and the `ALERT_N` interrupt — crossing the resulting slots. The F.Cu/In1 side of the board, by contrast, is clean.

On the manufacturing data, **R8 is missing from the JLC BOM** (both LDOs' SETRES-to-GND link), two active ICs have no LCSC part number, and three ICs carry a hand-edited 180° rotation that is inconsistent with how the other same-situation parts were treated. Those three are the items to fix before placing an order.

Everything else checked clean and is listed as such in the table above: clearances, copper-to-edge, silk-over-pad, the Kelvin sense tap geometry at all four shunts, the SENSE_* return paths, the Pmod pinout, and the absence of any blind/buried vias or impedance requirements that would raise the process class.
