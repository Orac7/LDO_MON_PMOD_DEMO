# Review log — LDO_MON_PMOD_Board_V1

Append-only. Each check is logged as it completes. Method tags: `tool` (kicad-cli, authoritative), `parse` (deterministic script), `judgement` (opinion).

Design under review: commit `ec3514f` ("Updated gerber zip file."), working tree otherwise clean apart from untracked `.DS_Store` files and the nested `.history/` repo.

Scale: **118 components, 65 nets, 6-layer board, single schematic sheet.**

---

## Wave 0 — tool-driven ground truth

| # | Area | Check | Method | Result | Notes |
|---|---|---|---|---|---|
| 0.1 | Toolchain | `kicad-cli` available and matches file format | tool | ✅ | v10.0.6, opens project without migration warnings |
| 0.2 | Schematic | ERC at project severities | tool | ⚠️ 10 warnings, 0 errors | 4× library-not-configured, 4× `multiple_net_names`, see 0.6 |
| 0.3 | Layout | DRC at project severities | tool | ⚠️ 12 warnings, 0 errors | 8 of the 12 are user-excluded; see 0.7 |
| 0.4 | Layout | Unconnected pads | tool | ✅ 0 | Board is fully routed |
| 0.5 | Both | **Schematic ↔ PCB netlist parity** | tool | ✅ 0 net issues | No netlist drift. The watchdog-bypass fix in `125b2fa` is consistently applied to both schematic and layout |
| 0.6 | Schematic | Rule severities audit | parse | ⚠️ **finding** | `pin_not_driven`, `power_pin_not_driven`, `single_global_label`, `four_way_junction`, `footprint_filter`, `simulation_model_issue` set to `ignore`. The first three are substantive checks |
| 0.7 | Layout | Exclusions audit | parse | ⚠️ **finding** | 9 DRC exclusions in the project file: 4× `via_dangling` (OUT_1, OUT_2), 5× `lib_footprint_mismatch` |
| 0.8 | Both | Re-run with all rules enabled, exclusions cleared | tool | ⚠️ 16 ERC / 14 DRC | Script `02_strict_checks.sh`, on a temp copy. New: 1× `single_global_label` (`GPIO`), 3× `power_pin_not_driven`, 2× `footprint_filter` (C9, C13) |
| 0.9 | Both | Parity under strict settings | tool | ⚠️ 2 | Both are `footprint_filters_mismatch` on C9/C13 — polarised symbol, non-polarised footprint. Not netlist drift |
| 0.10 | Netlist | Single-node (floating) nets | parse | ⚠️ 3, all deliberate NC | `U1.6 PG`, `U2.6 PG`, `U3.3 NC`. U3.3 is a genuine NC pin. The two LDO PG pins being unconnected is a **design question**, logged for Wave 1 |
| 0.11 | Netlist | Nets with more than one driver | parse | ✅ 0 | No output contention |
| 0.12 | Netlist | Pin-type census | parse | ℹ️ | 239 passive, 46 unspecified, 24 input, 14 power_in, 7 bidirectional, 2 output, 1 open_collector. The 46 `unspecified` pins are mostly from the two custom `klib_*` symbols — these defeat ERC pin-conflict checking (see Wave 1) |
| 0.13 | Parts | Identify active devices | parse | ✅ | U1/U2 LT3074 LDO, U3 MAX6373 watchdog, U4 74LVC1G175 D-FF, U5 PAC1944 4-ch power monitor, U6 74LVC1G08 AND, U7 AD5272 digipot, U8 PCA9306 I²C translator, Q1 MMBT3904, P1 PMOD 6×2 |
| 0.14 | Datasheets | Fetch vendor datasheets | tool | ⚠️ partial | TI parts OK (PCA9306, 74LVC1G175, 74LVC1G08). **Blocked by vendor anti-scraping: LT3074, MAX6373, PAC1944, AD5272.** Links given to the user to download by hand; dependent checks are held in Wave 1 |

### Wave 0 verdict

The design is in good mechanical shape: fully routed, zero unconnected pads, **zero schematic/PCB netlist parity issues**, zero output contention. Nothing here is a blocker.

The substantive Wave 0 result is about the *checking*, not the circuit: six ERC rules are set to `ignore` and nine DRC violations are excluded. Re-running strict surfaces six additional items. None of the newly surfaced items is itself alarming, but the suppressions mean the design is currently being checked more loosely than its reported "0 errors" suggests.

### Carried into Wave 1

- `GPIO` global label appears exactly once — destination unknown
- C9 / C13 polarised symbol on a non-polarised 0603 footprint
- U1.6 / U2.6 — LDO PG (power-good) outputs unconnected on a *monitoring* board
- Four aliased global-label pairs: `OUT_1`≡`SENSE_1_P`, `OUT_2`≡`SENSE_2_P`, `SENSE_4_N`≡`V_IN`, `SENSE_1_N`≡`SENSE_2_N`
- Four dangling vias on OUT_1/OUT_2, currently excluded
- The custom `klib_logic` / `klib_connectors` libraries are not in the project's library table — these symbols' pins are typed `unspecified`

---

## Design intent supplied by the owner

| # | Item | Statement | Effect on review |
|---|---|---|---|
| DI-1 | JP1/JP2/JP3 | Intended to be solder-blobbed as appropriate by the user before use; shipping open is deliberate | MAX6373 SET0/1/2 floating on an unconfigured board is **not** a defect. Reclassified from Blocker to a documentation/discoverability question. Recorded in `raw/DESIGN_INTENT.md` and passed to Wave 2 |
| RP-1 | Annotation policy | Non-obvious load-bearing values should be fixed by adding a schematic text note beside the part, not only flagged in the report | R18 = 1k becomes an actionable finding with suggested note wording; same treatment applied to any other value Wave 1 finds constrained by a non-local interaction |

---

## Wave 1b — PMOD spec verification (owner supplied spec v1.2.0, 2017-10-05)

Three interface claims were sourced secondhand because the spec could not be fetched. Now verified against the primary document.

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1b.1 | Pins 5/11 = GND, 6/12 = VCC on 12-pin | ✅ **confirmed** | §5.1 Type 1A table, p.6. Design matches: P1.5/P1.11 = GND, P1.6/P1.12 = 3V3_PMOD |
| 1b.2 | ~100 mA host current limit | ✅ **confirmed, verbatim** | §3 p.2: "should not be assumed to be more than approximately 100 mA". Design's ~30 mA worst case is comfortably inside |
| 1b.3 | 200 Ω series + ESD diodes | ❌ **reviewer finding CORRECTED** | §2 p.1 places these on the **host system board** port ("The I/O pins on standard system board Pmod ports generally have ESD protection diodes and 200-ohm series resistors... to limit short circuit currents"), **not** on the peripheral. A peripheral module omitting them is NOT a spec violation. F-IF-4's PMOD component is withdrawn; its J3 component stands |
| 1b.4 | Pinout is a one-off | ✅ **confirmed** | Type 6 (I²C) is a **6-pin** interface with SCL/SDA on pins 3/4 (§5.5 p.11). This design puts SCL/SDA on pins 8/9 — the 12-pin Type 1A expanded-GPIO layout (§5.1 p.6) used for I²C. Legal as GPIO, but it will not mate with a host expecting a Type 6 I²C Pmod |
| 1b.5 | Open-drain ALERT_N on a Pmod pin | ✅ **permitted, with a caveat that strengthens F-IF-3** | §2 p.2 allows open-drain "unless the pull-up is provided on the peripheral module itself" — R5 does provide it, so compliant. But §3 p.2 warns "Care should be taken to ensure 5 V will not damage the host's input pins". R5 pulls ALERT_N to BIAS, which J1 can set to EXT_VBIAS (up to 5.5 V). **The spec explicitly names this hazard** |

---

## Wave 1 — four parallel domain reviewers (complete)

Reports: `raw/wave1_power.md`, `wave1_logic.md`, `wave1_interface.md`, `wave1_layout.md`

### Verified clean (recorded so it is not re-reviewed)

| Area | Confirmed correct | Method |
|---|---|---|
| Watchdog fix `125b2fa` | Pre-fix netlist regenerated from `125b2fa^`; the original bug was real (J2 would have shorted 3V3 onto U6.4's push-pull output, >±50 mA abs-max). Fix is correct and complete; no node floats into a CMOS input in either jumper state | tool + parse |
| LT3074 paralleling | Topology matches datasheet Fig. 92 item-for-item: shared SETRES/SETCAP/IN/BIAS, 2 mΩ ballast, SENSE tap placement. 24-pin symbol map matches Table 5 exactly | judgement + datasheet |
| ERC label aliases | All four `multiple_net_names` pairs are deliberate and correct. `SENSE_1_N`≡`SENSE_2_N` is *required* by the paralleling recipe, not an accidental short. Kelvin integrity verified in the PCB — pour stops short of the taps | parse |
| PCA9306 | Pull-ups present on **both** sides (R10/R41 LV, R6/R7 HV); VREF2+EN/200 kΩ/100 n is verbatim TI Fig. 8-1. The classic PCA9306 error is absent | judgement + datasheet |
| I²C addressing | All four addresses distinct: U5 0x10, U7 0x2F, U1 0x6F, U2 0x6D. ASEL dividers match LT3074 Table 10 and agree with the schematic annotations | parse + datasheet |
| Logic inputs | U4 and U6 pinouts verified pin-by-pin; no floating CMOS inputs. R17 = 10k matches the MAX6373's own recommendation | parse + datasheet |
| PMOD current budget | ~30 mA worst case against the spec's ~100 mA. LDO pass current comes from J3.3, never PMOD VCC | parse |
| **Gerber release currency** | Re-exported from the current PCB and compared as a normalised multiset of (aperture, coordinate, operation). **Geometric difference = 0 across all 13 layers**; drill files byte-identical; `.gbrjob` identical; `Gerbers.zip` matches the loose directory. The split commits did *not* leave a stale release | tool |
| Stackup | 1.600 mm exact; GND plane adjacent to both routing layers at 0.100 mm; all 174 vias are through vias (no HDI cost class) | parse |
| Fab rules | 0 clearance/width/edge violations; min copper-to-edge 0.550 mm; no silk over pads | tool + parse |
| Board-level power | Every 0.15 mm trace on a power net is a Kelvin sense tap — load current path is entirely plane copper, no narrow-trace bottleneck. All six logic/monitor supply pins legal at 3.3 V | parse |

### Carried into Wave 2 for adversarial verification

Claims strong enough to act on but severe enough to deserve a refutation attempt — see `raw/WAVE2_BRIEF.md`.

| Claim | Alleged severity | Why it needs attacking |
|---|---|---|
| R8 0R fitted → both LDOs programmed to 0 V | Blocker | Already independently confirmed by the lead; Wave 2 is looking for anything that *excuses* it |
| Paralleled SETRES sources 200 µA → default V_OUT 3.33 V | Blocker | Depends on reading Fig. 92 correctly rather than the EC table |
| J1 strapping BIAS to 3V3 caps V_OUT at 2.1 V | Blocker | Headroom spec needs confirming as min vs typ |
| LT3074 OUT e-pad vias land copper on only one layer | Blocker | Could be a false negative if the Wave 1 script ignored zone `filled_polygon` geometry |
| 100 mA preload required or the part faults | Should-fix | **Suspect** — cites `MFR_IOUT_MIN_WARN_LIMIT`, which is PMBus vocabulary; the LT3074 is not a PMBus device |
| In4 I²C routing splits GND, 18 B.Cu segments cross | Should-fix | A track on a plane layer does not necessarily sever it; depends on real fill geometry |
| JLC BOM omits R8; U3/U7 lack LCSC; U4/U6/U8 rotations | Should-fix | Rotation edits may be *correct* JLC convention rather than errors; needs per-package checking |
| ALERT_N pulled to BIAS reaches PMOD pin 3 at up to 5.5 V | Should-fix | Already strengthened by the PMOD spec (§3 warns of exactly this) |

---

## Wave 2 — adversarial verification (complete)

Three refuters, briefed to attack rather than confirm. Reports: `raw/wave2_power.md`, `wave2_layout.md`, `wave2_mfg.md`.

| Claim attacked | Verdict | Effect |
|---|---|---|
| Paralleled SETRES sources 200 µA → 3.3333 V default | **CONFIRMED** | Decisive evidence Wave 1 missed: Table 8 p.31 gives 4.99 kΩ → 0.5 V single-device vs Fig. 92's 1 V two-device. Currents add. → F-03 |
| `V_BIAS ≥ 1.2 + V_OUT` caps V_OUT at 2.1 V | **CONFIRMED** | Hard requirement over full temp, encoded in the EC table as `Max[2.375, V_OUT+1.2]`. → F-02 |
| 100 mA preload or the part faults | **CONFIRMED on substance** | My PMBus objection was wrong — the LT3074 *is* PMBus 1.3. But page is 55 not 52, it is a *warning* not a shutdown, and the proposed fix was undersized 4×. → F-09 |
| BIASAF/BIASDF caps on datasheet minimums | **CONFIRMED** | Real pins 16/18; "requires a minimum" language twice. Reframed: the defect is the missing dielectric spec, not the values. → F-01 |
| OUT e-pad vias land on one layer | **CONFIRMED** | Independently reproduced: 4 of 174 vias. My `filled_polygon` hypothesis was **wrong** — both Wave 1 scripts parse zone fills correctly, and zones are not stale. → F-04 |
| R8 fitted ⇒ dead board | **WEAKENED** | JLC BOM omits R8 (verified directly: `['0R','R26,R36',…]`), so it is most likely not placed. Severity Blocker → Should-fix. → F-01 |
| In4 I²C routing splits GND, 18 crossings | **WEAKENED** | Pocket is stitched; the headline "crossing" is a parallel run; 6 genuine crossings not 18; F.Cu has *more* stretches than B.Cu, contradicting Wave 1's own clean finding. Crosstalk computes to tens of mV. → demoted |
| 0.9 mm neck inadequate for 3 A | **REFUTED** | Transverse width is 1.20 mm; real rise single-digit °C |
| U4/U6/U8 rotations are errors | **REFUTED** | The +180 edits are convention-correct per the JLC rotation table |
| No mounting holes | **REFRAMED** | Spec never mentions them. Real issue is 0.8661″ width vs the 0.8″ clip requirement, 3 parts in keepout. → F-07 |
| R18 ships at 10k, 0.21 V margin | **REFUTED** | R18 is **1k** as built (verified in schematic); margin 1.52 V. → became F-14 per RP-1 |
| AD5272 clamp forward-biased at default | **REFUTED** | 270 mV of margin at 3.33 V; only real at codes ≥ 576 |

### Inter-reviewer conflict resolved by the lead

The manufacturing refuter tried to correct the power refuter, asserting Table 8 gives 4.99 kΩ → 0.5 V so the 1 V figure is wrong. **The correction is itself wrong** — it applies the single-device table to a paralleled pair. Both numbers are right in context (0.5 V one device, 1.0 V two), and the discrepancy *is* the evidence that the currents add. Power refuter's reading stands.

### Lead's own corrections

- I hypothesised the OUT-via finding might be a false negative from scripts ignoring `filled_polygon`. **Wrong** — both scripts handle zone fills correctly. The finding is real.
- I judged the `MFR_IOUT_MIN_WARN_LIMIT` citation suspect on the grounds that the LT3074 is not a PMBus device. **Wrong** — it is (p.46, Table 6).

---

## Final state

**6 reviewers, 2 waves, 15 findings retained, 13 claims rejected or materially weakened.**

No blockers. Highest severity is Should-fix. The released manufacturing data was verified current against the design, and the most recent schematic change (`125b2fa`) was verified correct.

Deliverable: `FINDINGS.md`.

---

## Review hygiene

`kicad-cli` writes to the project files it opens even for read-only operations. After the review, `.kicad_pro` (a reordered `used_designators` string) and `.kicad_prl` (UI state) showed as modified. Both changes were cosmetic and both were reverted with `git checkout --`. Stray `~*.lck` lock files were also removed. **The design files are byte-identical to commit `ec3514f`.**

`02_strict_checks.sh` was written to operate on a temporary copy specifically to avoid this; the incidental writes came from the plain ERC/DRC/export runs in `01_run_kicad_checks.sh`. If re-running, expect the same and revert afterwards.
