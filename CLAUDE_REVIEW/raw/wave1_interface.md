# Wave 1 — Interface and Connector review

Scope: PMOD compliance (P1), current budget, I2C chain (U5/U7/U8), external-signal protection (P1/J1/J2/J3), the four ERC net aliases, and PAC1944 shunt sizing.

Everything below is derived from `CLAUDE_REVIEW/raw/nets.tsv`, `components.tsv`, `erc_strict.rpt`, the embedded `lib_symbols` entry and footprint in `LDO_MON_PMOD_Board_V1.kicad_sch` / `.kicad_pcb`, and the datasheet PDFs in `CLAUDE_REVIEW/datasheets/`. Datasheet page/section references are given where a claim is VERIFIED; estimates are labelled INFERRED.

---

## Topology established (needed to read the findings)

Reading the symbol + footprint + netlist, the board is:

```
J3.3 (V_IN / SENSE_4_P) --[R35 15mR]-- SENSE_4_N (= "V_IN" alias) -> U1.IN, U2.IN
                                          PAC ch2 (SENSE2+/-)

U1.OUT (OUT_1 = "SENSE_1_P") --[R15 2mR]--+
                                PAC ch4   |
U2.OUT (OUT_2 = "SENSE_2_P") --[R16 2mR]--+-- SENSE_1_N (= SENSE_2_N) --[R39 15mR]-- SENSE_3_N -> J3.2
                                PAC ch3                                   PAC ch1
```

U1 and U2 are two LT3074s **directly paralleled** (shared IN, BIAS, SETRES via `SET_RES_NODE`, SETCAP via `SET_CAP_NODE`), with R15/R16 acting simultaneously as ballast resistors and as PAC sense shunts.

Connector functions (from `nets.tsv`):

| Conn | Pin | Net | Function |
|---|---|---|---|
| J1 (3-pin) | 1 / 2 / 3 | 3V3_PMOD / BIAS / EXT_VBIAS | bias-source selector jumper |
| J2 (2-pin) | 1 / 2 | ENABLE / U6.4 | watchdog-enable bypass jumper |
| J3 (4-pin Phoenix) | 1 / 2 / 3 / 4 | EXT_VBIAS / SENSE_3_N / SENSE_4_P / GND | VBIAS in, VOUT, VIN, GND |

**J3 is not a Kelvin-sense connector** — it is the power connector (VIN, VOUT, VBIAS, GND). All Kelvin sensing is on-board via R27–R34.

---

## Checks performed

| Check | Method | Result | Notes |
|---|---|---|---|
| P1 real pinout (symbol not in lib table) | Parsed `lib_symbols` entry `klib_connectors:PMOD-Device-x2-Type-Generic-Alt` at `.kicad_sch:3505-3900` | Done | Symbol is fully generic: 12 pins named `P1`…`P12`, all type `passive`. No GND/VCC semantics in the symbol at all. |
| P1 footprint pad geometry | Parsed `pmod_pin_array_6x2` at `.kicad_pcb:493` | **Clean** | Pads 1–6 at x=+1.27, y=-6.35…+6.35 step 2.54; pads 7–12 at x=-1.27, same y. 2×6, 0.1" pitch, 0.1" row spacing. Pad 1 is `rect` (pin-1 marker). |
| PMOD GND/VCC pin convention | Footprint nets vs Pmod convention | **Clean** | P1.5 + P1.11 = GND, P1.6 + P1.12 = 3V3_PMOD. Matches the 12-pin convention (signals 1–4 and 7–10; 5/11 GND; 6/12 VCC). |
| PMOD Type identification | Signal assignment vs Digilent type table | **Non-standard** — see F-IF-9 | SCL/SDA are on pins 8/9, not the Type 6/6A I2C positions. |
| Board outline vs Pmod form factor | Edge.Cuts = single `rect 94.92 89 165 111` | 70.08 × 22.0 mm | 0.866" wide vs the 0.8" Pmod module width. Not a blocker, noted. |
| P1 board-edge alignment | Footprint `Dwgs.User` "Board Edge" guide at abs x≈94.75 vs Edge.Cuts x=94.92 | **Clean (0.17 mm)** | Designer did align to the footprint's own guide. |
| Current source for the LDO pass element | `nets.tsv` SENSE_4_P / SENSE_4_N node lists | **Clean** | LDO IN pins are fed from **J3.3**, not from PMOD VCC. The PMOD only powers logic (+ optionally BIAS). |
| PMOD VCC current budget | Datasheet IDD figures + pull-up/LED arithmetic | **Clean, ≈30 mA worst case** | See "Current budget" section below. Well inside ~100 mA. |
| PCA9306 pull-ups on BOTH sides | `nets.tsv` nets `SCL`,`SDA`,`SCL_HV`,`SDA_HV` | **Clean — the classic error is NOT present** | LV: R10 4k7 (SCL), R41 4k7 (SDA) to 3V3_PMOD. HV: R6 4k7 (SCL_HV), R7 4k7 (SDA_HV) to BIAS. |
| PCA9306 VREF1/VREF2/EN topology | Datasheet §8.1.2 Fig 8-1 (p.10–11) | **Clean** | VREF1 (U8.2) = 3V3_PMOD direct; VREF2 (U8.7) shorted to EN (U8.8), pulled to BIAS through R22 **200 k** with C51 100 n. This is exactly TI's "Normal Setup". The datasheet's §8.1.2 warning against tying VREF2 straight to VCC2 is correctly avoided. |
| PCA9306 pin assignment / translation direction | Datasheet pin table (p. ~7) vs `nets.tsv` | **Clean** | 1 GND, 2 VREF1=3V3, 3 SCL1=SCL(LV), 4 SDA1=SDA(LV), 5 SDA2=SDA_HV, 6 SCL2=SCL_HV, 7 VREF2, 8 EN. Host on side 1, LT3074s on side 2 — permitted (§8.1.6). |
| PCA9306 VREF1 ≤ VREF2 − 0.6 V | Datasheet Rec. Op. Cond. note (1), p.6 | **Conditional failure** — see F-IF-6 | Only satisfied when BIAS ≥ 3.9 V. |
| PCA9306 SCL2/SDA2 max voltage vs BIAS | Datasheet §6.3 (VI/O 0–5.5 V), §6.1 (abs max 7 V) | **Clean** | VBIAS ≤ 5.5 V (LT3074 Table 1), so SCL_HV/SDA_HV ≤ 5.5 V = rec. max exactly. |
| PCA9306 pass current | Datasheet §6.3 IPASS 64 mA | **Clean** | 4k7 pull-ups → ~0.7 mA. |
| I2C address collision | LT3074 Table 10 p.43; PAC194x Table 6-1 p.33; AD5272 Table 11 p.15 | **Clean, no collision** | U1 = **0x6F** (R4 47k5 / R2 261k), U2 = **0x6D** (R13 69k8 / R14 261k), U5 = **0x10** (R26 = 0 Ω to GND), U7 = **0x2F** (ADDR via R38 10k to GND). All four share one electrical bus through U8. |
| AD5272 ADDR strap validity | Tristate leakage ±1 µA (datasheet p.5) × R38 10 k = 10 mV ≪ VINL 0.8 V | **Clean** | 10 k to GND reliably reads as the GND state. |
| AD5272 RESET strap | Datasheet pin 7 ("tie to VDD if not used") | **Clean** | `DP_RST_N` = P1.7 + R37 10 k pull-up to 3V3_PMOD. Defaults de-asserted if host floats. |
| PAC1944 ADDRSEL resistor is a valid table value | Table 6-1 p.33 row "0 (GND)" | **Clean** | R26 = 0 Ω is an explicit table entry. |
| I2C pull-up value vs drive | 4k7 → 617 µA at 3.3 V; I2C needs ≥3 mA sink capability, R_min ≈ 970 Ω | **Clean** | Comfortably drivable; VOL margin fine. |
| I2C pull-up value vs speed | t_r ≈ 0.85·R·C | **Clean at 400 kHz**, see F-IF-11 | 4k7 with an estimated 40–60 pF gives t_r ≈ 160–240 ns (<300 ns Fast-mode limit). Caps the bus near 400 kHz. |
| Max bus speed of the slowest device | LT3074 Table 1 line "Serial Bus Operating Frequency fSCL 10–400 kHz" | See F-IF-11 | PAC194x is Fm+ / 1 MHz capable but is stuck on the same logical bus. |
| ERC alias `OUT_1 = SENSE_1_P` | `erc_strict.rpt` + net node list | **Deliberate and correct** | Same physical node = high side of ballast/shunt R15. Two names, one node. |
| ERC alias `OUT_2 = SENSE_2_P` | same | **Deliberate and correct** | High side of R16. |
| ERC alias `SENSE_4_N = V_IN` | same | **Deliberate and correct** | Low side of input shunt R35 *is* the LDO input rail. Naming is confusing but electrically right. |
| ERC alias `SENSE_1_N = SENSE_2_N` | LT3074 "Direct Paralleling for Higher Output Current" p.~40 + Fig 92 | **Deliberate and correct — NOT an accidental short** | See the dedicated section below. |
| Kelvin tap geometry, all 4 channels | Parsed PCB pads/segments/zones (see section below) | **3 of 4 correct, 1 defective** | F-IF-2. |
| Sense +/- polarity, all 4 channels | PAC194x pin table p.18 ("+ = supply side, − = load side") | **Clean, all four correct** | ch1 R39, ch2 R35, ch3 R16, ch4 R15 all have + on the source side. |
| PAC1944 common-mode range | Datasheet p.6 VBUS −0.2 V to 9 V | **Clean** | All sense nodes ≤ 5.5 V (LT3074 VIN max). |
| PAC1944 series input resistance | Datasheet p.6 `RTRACE` = 1 kΩ "allowable trace resistance without measurement error"; p.1 "No input filters are required for this device" | **Fail** | R27–R34 are 4k99 each — F-IF-1. |
| Shunt sizing vs 100 mV FSR | Datasheet §5 FSR = 100 mV unipolar; VSENSE_LSB 1.50 µV; offset ±25 µV typ / ±100 µV max | **Mixed** | R35/R39 good; R15/R16 marginal — F-IF-5. |
| Shunt power dissipation | 2512 footprint | **Clean** | R39/R35 at 6 A: 0.54 W each in a 2512. R15/R16 at 3 A: 18 mW. |
| ESD / TVS devices anywhere on the board | `components.tsv` full scan | **None present** | Only D1/D2 (LEDs). F-IF-9. |
| Series resistors between P1 and IC pins | `nets.tsv` for all 8 signal nets | **None present** | F-IF-9. |
| Reverse-polarity / overcurrent protection on J3 | `components.tsv` + `nets.tsv` (EXT_VBIAS, SENSE_4_P) | **None present** | F-IF-4. |
| Silkscreen pin labelling on J1/J2/J3 | Searched all `gr_text` and `fp_text` in `.kicad_pcb` | **None** (zero `gr_text` objects on the whole board) | F-IF-4. |
| Hot-plug inrush on PMOD VCC | Summed caps on `3V3_PMOD` (+ BIAS if jumpered) | ≈20 µF (≈25 µF with BIAS) | F-IF-10. |
| Connector part selection | `bom.csv`, `MANUFACTURING_DATA/BOM/*.csv` | **P1, J1, J2, J3 all have empty MPN/Manufacturer/LCSC** | F-IF-12. |
| Copper weight for IR-drop estimates | Stackup at `.kicad_pcb:41` — all six layers 0.035 mm | 1 oz, 0.49 mΩ/sq | Used in F-IF-2. |
| **Could not do:** exact I2C bus capacitance | Needs pin-capacitance figures for U5/U7/U1/U2 plus host cable; not in the supplied datasheets | — | t_r figures above are INFERRED from a 40–60 pF estimate. |
| **Could not do:** fetch Digilent Pmod Interface Spec 1.3.1 primary PDF | digilent.com returned HTTP 403 for all three URLs tried | — | Type-table and 100 mA / 200 Ω figures come from secondary sources (Wikipedia, grokipedia, fpgas.online) and are labelled accordingly. |
| **Could not do:** verify P1 pin-1 orientation against a real host socket | No MPN for P1, and the footprint has both a "Board Edge" guide (right-angle-like) and a symmetric 5.08×15.24 mm silk body (straight-header-like) | — | F-IF-12. |

---

## The `SENSE_1_N = SENSE_2_N` alias — verdict: deliberate, correct, and necessary

This is the one the brief singled out. It is **not** an accidental short and it does **not** defeat the Kelvin measurement. Evidence:

1. U1 and U2 share `SET_RES_NODE` (U1.13 + U2.13), `SET_CAP_NODE` (U1.12 + U2.12), `BIAS` (U1.17 + U2.17) and `SENSE_4_N`/V_IN (U1.20/21/23 + U2.20/21/23). That is verbatim the LT3074 recipe: *"Connect all SETRES, SETCAP, IN, and BIAS pins together. Connect the OUT pins together using small pieces of PCB trace or actual sense resistors (used as ballast resistors)."* (LT3074 datasheet, "Direct Paralleling for Higher Output Current").
2. The ballast value chosen, **2 mΩ**, is precisely the value in the same section: *"two LT3074 devices, each using a 2 mΩ PCB trace ballast resistor, provide better than 20% accurate current sharing"* (Figure 92).
3. Because the two LDO outputs are intentionally one node, the two shunts' low sides **must** be the same net. There is nothing to separate.
4. For the differential measurement this is benign: PAC194x SENSE inputs are fully differential with a 0–9 V common-mode range (p.6), and both channels sit at the same ~VOUT common mode, well inside it.
5. The layout honours it properly: the SENSE_1_N F.Cu zone (polygon left edge x = 141.8) covers R15 pad 2 and R16 pad 2 but stops short of the sense taps at x = 141, so R27 and R30 each reach their *own* shunt pad over a dedicated 0.15 mm trace (segments `142.4625,103 → 141.3,103 → 141,103.3 → 141,104.85` and `142.4625,107.91 → 141.49,107.91 → 141,108.4 → 141,109.84`). Each channel therefore sees only its own shunt's drop, not the summed current in the shared pour.

So: correct. The one real layout defect is on the *high* side of channel 3 — see F-IF-2.

---

## Current budget (PMOD VCC)

| Load | Current | Source |
|---|---|---|
| U5 PAC1944 VDD, 1024 SPS 4ch | 535 µA max | datasheet p.6 |
| U7 AD5272 VDD | 1 µA (4 mA for 55 ms during 50-TP store) | datasheet p.4 |
| U3 MAX6373 VCC | 8 µA typ | datasheet p.1 |
| U4 + U6 (LVC1G) | <10 µA each | — |
| U8 VREF1 | negligible | — |
| D1 power LED (R42 1 k) | ~1.4 mA continuous | calc |
| D2 enable LED (R44 1 k, Q1) | ~1.4 mA when on | calc |
| Pull-ups R10/R41 (4k7) all low | 1.4 mA | calc |
| Pull-ups R17/R18/R23/R24/R25/R37 (10 k) all low | 2.0 mA | calc |
| **BIAS, only if J1 selects 3V3_PMOD:** 2 × LT3074 IBIAS at IOUT = 3 A | **2 × 10 mA = 20 mA max** | LT3074 Table 1 |
| BIAS-side pull-ups R5/R6/R7 | 1.4 mA | calc |
| **Total worst case** | **≈ 30 mA** | |

**Result: clean.** The LDO pass current comes from J3.3, never from PMOD VCC, so there is no risk of a 3 A/6 A draw through the connector. Even with BIAS jumpered to PMOD VCC the board stays near 30 % of the ~100 mA Pmod budget. The only PMOD-rail concern is inrush, not steady state (F-IF-10).

---

## Findings

#### F-IF-1: PAC1944 sense inputs have 4.99 kΩ series resistors — 5× the datasheet's allowable input resistance, and the datasheet says no input filter is needed at all
- Severity: **Should-fix**
- Confidence: **High**
- Where: R27, R28, R29, R30, R31, R32, R33, R34 (all 4k99) on nets `SENSE_1..4_{P,N}_FILT` → U5 pins 7–14; filter caps C34–C45
- Evidence: PAC194X datasheet p.6, DC Electrical Characteristics: *"VBUS, VSENSE Input Trace Resistance (allowable trace resistance without measurement error) `RTRACE` — 1 kΩ"*. Same table: *"SENSE+, SENSE− Pin Input Current `ISENSE` −6 / 0.6 / +6 µA"*. Datasheet p.1 feature list: *"The PAC194X device family uses real-time calibration to minimize the offset error. **No input filters are required for this device.**"* Section 4.1 p.22 likewise only asks for Kelvin routing as a differential pair, not an RC.
- Why it matters: 4.99 kΩ × 6 µA worst-case input current = **30 mV** of error on the VBUS (bus-voltage) reading per pin — 219 VBUS LSBs (LSB = 137 µV) and ~0.9 % of a 3.3 V reading, which propagates straight into the VPOWER and accumulated-energy results. Differentially, if ISENSE+ and ISENSE− sit at opposite ends of their ±6 µA range the VSENSE error is 2 × 6 µA × 4.99 k = **60 µV**, on top of the device's own ±100 µV offset spec. On the 2 mΩ shunts that 60 µV alone is **30 mA** of current error. The RC network is buying nothing the device needs and costing measurable accuracy.
- Suggested fix: drop R27–R34 to **100 Ω** (or 0 Ω) and keep the 47 nF differential caps if a filter is still wanted for layout noise; that puts the series resistance at 1/50th of the spec limit and the error contribution below the device's own offset. Keep SENSE+/SENSE− routed as a differential pair per §4.1.

#### F-IF-2: Channel 3's high-side Kelvin tap is taken in the OUT_2 copper pour, not at R16's pad — the other three channels tap at the pad
- Severity: **Should-fix**
- Confidence: **Medium** (geometry is certain; the IR-drop magnitude is an estimate)
- Where: R29 (SENSE_2_P_FILT ← OUT_2), via on net OUT_2 at PCB (135.15, 109.01); R16 pad 1 centre at (136.54, 107.91)
- Evidence: Parsed from `.kicad_pcb`. OUT_2 net has exactly one via near the shunt, at (135.15, 109.01), feeding B.Cu segment `135.15,109.01 → 138,109.01` to R29 pad 2. R16 is a 2512 (`R_2512_6332Metric`), so pad 1 spans x ≈ 135.79–137.29 — **the via is 0.64 mm outside the pad's left edge**, inside the OUT_2 F.Cu zone (polygon `(129.7,106.9)…(137.3,109.6)…`), i.e. upstream in the live current path from U2's OUT pins at x ≈ 130. Contrast channel 4: OUT_1's tap trace starts at `136.5375, 103` — exactly R15's pad-1 centre — and the OUT_1 zone edge (x = 137.4) sits just past the pad's right edge, so the effective tap is the pad itself. R31/R32 (ch1) and R33/R34 (ch2) likewise tap at R39 and R35 pad centres (`147.5,102.75` / `153.425,102.75` and `147.5,97.5` / `153.425,97.5`).
- Why it matters: 0.64 mm of 1 oz pour (stackup at `.kicad_pcb:41`, all layers 0.035 mm → 0.49 mΩ/sq) over an effective ~3 mm width is roughly **0.1 mΩ** (INFERRED). Added to a 2 mΩ shunt that is a **~5 % gain error on channel 3 only** — 10× the PAC's own ±0.5 % gain spec, and a systematic one. The entire purpose of per-device 2 mΩ shunts on two directly-paralleled LT3074s is to measure current *sharing*; a 5 % channel-to-channel asymmetry will be read as a permanent sharing imbalance that does not exist, and will mask (or fabricate) the ±20 % sharing window the LT3074 datasheet quotes for 2 mΩ ballast.
- Suggested fix: move the OUT_2 via onto R16's pad-1 land (or run a 0.15 mm trace from the pad centre out to the via, mirroring exactly what R28 does on R15) so channels 3 and 4 are geometrically identical.

#### F-IF-3: ALERT_N crosses the BIAS voltage domain straight onto PMOD pin 3, bypassing the level translator
- Severity: **Should-fix**
- Confidence: **High**
- Where: net `ALERT_N` = P1.3, R5.2, U1.3, U2.3. R5 (10 k) pulls it up to `BIAS`. PCB: traced from U1/U2 to P1 pad 3 at (101.27, 98.73) with no intervening device.
- Evidence: `nets.tsv` line `ALERT_N 4 P1.3(P3_3) R5.2 U1.3(ALERT_N_3) U2.3(ALERT_N_3)`. `BIAS` net includes J1.2, so BIAS = EXT_VBIAS (up to 5.5 V, LT3074 Table 1 "BIAS Pin Voltage 2.375–5.5 V") whenever the J1 jumper selects pins 2–3. SCL and SDA from the same domain *are* translated by U8 (`SCL_HV`/`SDA_HV`); ALERT_N is the one signal that is not.
- Why it matters: with an external 5 V bias the PMOD host's pin 3 — an LVCMOS33 input — is presented with 5 V. It is not immediately destructive because LT3074 ALERT is open-drain (datasheet pin table p.~? : *"Open-Drain Digital Output… A pull-up resistor to the highest supply rail is required"*) so R5 limits the injected current to (5.0 − 3.9)/10 k ≈ 110 µA into the host's ESD clamp. But the logic level is out of spec, the host's 3.3 V rail is being back-fed, and any host that implements a bus-hold or has a weak 3.3 V rail will mis-read or latch. It also means ALERT is unusable whenever the board is run on external bias, which is the interesting case.
- Suggested fix: either route ALERT_N through a third translator channel / a small N-FET level shifter referenced to 3V3_PMOD, or move the pull-up R5 from BIAS to 3V3_PMOD (the LT3074 pin is open-drain and rated to 5.5 V, so pulling it to 3.3 V is legal and makes the signal natively host-compatible). The second option is a one-net change.

#### F-IF-4: No reverse-polarity, overvoltage or overcurrent protection on the J3 power inputs, and no silkscreen pin identification anywhere on J1/J2/J3
- Severity: **Should-fix**
- Confidence: **High**
- Where: J3 (`PhoenixContact_MC_1,5_4-G-3.5_1x04`) pins 1 (EXT_VBIAS), 3 (SENSE_4_P/VIN), 4 (GND); J1, J2
- Evidence: `nets.tsv`: `EXT_VBIAS 2 J1.3 J3.1` — two nodes, nothing in between. `SENSE_4_P 3 J3.3 R33.2 R35.2` — straight to the shunt and thence to U1/U2 IN. `components.tsv` contains no diode other than D1/D2 (LEDs), no fuse, no polyfuse, no TVS. Searching `.kicad_pcb` for `gr_text` returns **zero objects**, and the only `fp_text user` strings on the board are `${REFERENCE}` ×114 plus the P1 footprint's own "GND"/"VCC"/"Board Edge"/dimension marks — so J1/J2/J3 carry nothing but a refdes.
- Why it matters: J3 is a removable screw terminal that an operator wires by hand, with four pins carrying four different things (VBIAS in, VOUT, VIN, GND) and no markings. Reversing VIN and GND forward-biases the LT3074 parasitic diodes — datasheet Abs Max note 1: *"Parasitic diodes exist internally between IN, OUT, SENSE, BIAS… and GND. Do not drive these pins more than 0.3 V below the GND pin"* — destroying U1 and U2, and simultaneously driving U5's SENSE pins below their −0.2 V minimum (PAC194x p.6). There is no series element to limit the fault current; the supply's own current limit is the only protection. A bench supply set to 5 V at 6 A will do this instantly.
- Suggested fix: (a) add silkscreen legends `VBIAS / VOUT / VIN / GND` next to J3 and `3V3 / BIAS / EXT` next to J1 — zero cost, biggest single risk reduction; (b) add a series Schottky or an ideal-diode/P-FET on `SENSE_4_P` ahead of R35 (note it must be ahead of the shunt so it does not corrupt the ch2 measurement), or at minimum a reverse-biased TVS from VIN to GND plus a fuse; (c) the same TVS treatment on EXT_VBIAS.

#### F-IF-5: R15/R16 at 2 mΩ use only 6 % of the PAC1944's 100 mV full-scale range
- Severity: **Should-fix**
- Confidence: **High**
- Where: R15, R16 (2 mΩ, 2512) → PAC channels 4 and 3
- Evidence: PAC194X datasheet §5 / p.6: FSR = 100 mV unipolar; `VSENSE_LSB` = 1.50 µV at 16-bit; `VSENSE_OFFSET_ERR` = ±25 µV typ, **±100 µV max**; `VSENSE_GAIN_ERR` ±0.5 % at 25 °C, ±0.3 % typ over temperature. LT3074 internal current limit 4.5 A typ, programmable limit 3.04 A.
  - R15/R16: 3 A × 2 mΩ = **6 mV = 6 % of FSR**. Max offset ±100 µV = **±50 mA**. At a 100 mA load (200 µV of signal) the offset is **±50 % of reading**.
  - R39/R35: 6 A × 15 mΩ = **90 mV = 90 % of FSR**, offset ±100 µV = ±6.7 mA. Well sized.
- Why it matters: the board throws away 94 % of the ADC range on exactly the two channels whose job is per-device current sharing, while the two summed channels use 90 %. Light-load current-sharing data — the regime where LT3074 offset-driven sharing error is worst and most interesting — will be buried in offset. It also makes F-IF-2's ~0.1 mΩ layout error a 5 % effect instead of a 0.7 % one.
- Nuance: the 2 mΩ value is **not arbitrary** — it is the ballast value from the LT3074 "Direct Paralleling" section (Figure 92), so there is a real constraint here: raising it increases load-regulation droop (15 mΩ × 3 A = 45 mV of droop per device). This is a genuine trade-off, not an oversight.
- Suggested fix: if the droop can be absorbed, go to 5 mΩ (15 % FSR, 15 mV at 3 A, droop 15 mV) as a compromise; otherwise accept the range loss but configure the PAC for **bipolar ±100 mV FSR off, 8× averaging mode** (datasheet p.1 feature list: *"8X Averaging Mode for Single-Shot Measurements to Reduce Noise and Offset"*) and document the ±50 mA floor on channels 3 and 4 so nobody trusts low-current sharing numbers.

#### F-IF-6: When J1 selects BIAS = 3V3_PMOD, the PCA9306 is outside its translation range and the LDOs are capped at VOUT ≈ 2.1 V
- Severity: **Should-fix**
- Confidence: **High**
- Where: J1 (pins 1–2 shunt) → `BIAS` = 3V3_PMOD; U8 VREF1 = 3V3_PMOD, VREF2 pulled to BIAS via R22
- Evidence: PCA9306 datasheet §6.3 Recommended Operating Conditions, note (1), p.6: *"To support translation, VREF1 supports 1.2 V to **VREF2 − 0.6 V**. VREF2 must be between VREF1 + 0.6 V to 5.5 V."* With BIAS = 3.3 V, VREF1 = VREF2 = 3.3 V, which is §8.1.5 "Switch Configuration", not translation. §8.1.5's Figure 8-5 shows that configuration with **EN driven by a GPIO**, annotated *"high logic does not exceed Vref2 + Vth"* — i.e. TI expects a separate enable in switch mode, not the 200 kΩ-to-VCC2 arrangement this board uses. Separately, LT3074 Table 1: BIAS Pin Voltage min 2.375 V with the condition **`Max[2.375, VOUT + 1.2 V] ≤ VBIAS ≤ 5.5 V`**, so VBIAS = 3.3 V ⇒ VOUT ≤ 2.1 V.
- Why it matters: the board silently has two incompatible operating modes behind an unlabelled 3-pin jumper. In the 3V3_PMOD position the translator degrades to a pass switch with reduced Vgs on the pass FET (higher Ron, different and asymmetric propagation delay per §8.1.5) and the LDOs cannot be used above 2.1 V out. A user who sets VOUT = 3.3 V with the jumper in the wrong position gets an out-of-regulation LDO and may spend a long time blaming the digipot.
- Suggested fix: document the constraint on silkscreen/in the manual; if the 3V3_PMOD bias position is meant to be the default, note that only VOUT ≤ 2.1 V is supported there. If translation-mode operation matters, the 3V3_PMOD position should be removed and BIAS required to be ≥ 3.9 V from J3.1.

#### F-IF-7: LT3074 SCL/SDA/ALERT pull up to VBIAS, which at the maximum legal VBIAS sits exactly at the pins' absolute maximum
- Severity: **Nice-to-have**
- Confidence: **High**
- Where: R6 (4k7, SCL_HV→BIAS), R7 (4k7, SDA_HV→BIAS), R5 (10 k, ALERT_N→BIAS)
- Evidence: LT3074 Abs Max table, p.9: *"BIAS, BIASAF, BIASDF Pin Voltage −0.3 V to 6 V"* but *"**SCL, SDA, ALERT Pin Voltage −0.3 V to 5.5 V**"*. LT3074 Table 1: BIAS operating max = 5.5 V. The pin description for SCL says *"A pull-up resistor to the highest supply rail is required"*, so the design follows the datasheet's own instruction — but at VBIAS = 5.5 V the I/O pins land precisely on the abs-max limit with zero margin for supply tolerance, ringing or overshoot.
- Why it matters: a user running the documented maximum 5.5 V bias from J3.1, with a supply that overshoots 2 % on turn-on, exceeds the abs-max rating of six I/O pins across two devices. The pull-ups are on exposed, cable-length nets so overshoot is plausible.
- Suggested fix: move R5/R6/R7 to a 3.3 V rail (legal — the pins are open-drain and the PCA9306 side-2 reference just needs to be ≥ VREF1 + 0.6 V for translation, which is a separate node), or derate the documented EXT_VBIAS maximum to ~5.0 V in the user documentation.

#### F-IF-8: Net-name sense-channel numbering is the exact reverse of the PAC1944 hardware channel numbering
- Severity: **Nice-to-have**
- Confidence: **High**
- Where: U5 pins 7–14 vs the `SENSE_n_*` net names
- Evidence: from `nets.tsv`: `SENSE_3_P_FILT → U5.11 (SENSE1+)`, `SENSE_4_P_FILT → U5.13 (SENSE2+)`, `SENSE_2_P_FILT → U5.8 (SENSE3+)`, `SENSE_1_P_FILT(=OUT_1 branch via R28) → U5.10 (SENSE4+)`. The mapping is net index *n* → PAC channel *5 − n*, with no exception.
- Why it matters: firmware reads PAC registers by hardware channel (VSENSE1…VSENSE4). Anyone cross-referencing the schematic's `SENSE_1_*` labels to "channel 1" will swap U1's output measurement with the combined-output measurement and the input measurement with U2's — a silent, plausible-looking wrong answer rather than an obvious failure. Given that the board's purpose is current accounting, swapped channels produce an efficiency number that looks almost right.
- Suggested fix: rename the nets to match the silicon (`SENSE_1_*` ↔ `SENSE_4_*`, `SENSE_2_*` ↔ `SENSE_3_*`), or add an explicit mapping table to the schematic title block. Renaming is the safer option.

#### F-IF-9: P1 is not a standard Pmod type, and no PMOD signal has series or ESD protection
- Severity: **Nice-to-have**
- Confidence: **High** for the facts; **Medium** for the Digilent spec citations (primary PDF returned HTTP 403; figures below are from secondary sources)
- Where: P1 pins 1–4, 7–10
- Evidence: Actual assignment from the footprint nets — P1.1 PAC_EN, P1.2 SLOW, P1.3 ALERT_N, P1.4 CNTRL, P1.5 GND, P1.6 VCC, P1.7 DP_RST_N, P1.8 SCL, P1.9 SDA, P1.10 WDI, P1.11 GND, P1.12 VCC. The GND/VCC positions (5/11 and 6/12) are **correct and compliant**. However the I2C pair sits on pins **8 and 9**, whereas Pmod Type 6 / 6A (I2C) places SCL and SDA on the first two signal pins of a row. **This design is therefore a one-off**: it is functionally closest to Type 1A (expanded GPIO, eight general-purpose signals) with I2C bit-banged or routed onto two of those GPIOs. Separately, `nets.tsv` shows every one of the eight signals going straight from P1 to an IC input with only a pull-up/pull-down in parallel — no series resistor, and `components.tsv` contains no ESD/TVS part. Secondary sources for the spec report *"Series Resistors: 200-ohm resistors on I/O pins recommended"* and *"ESD Protection: diodes and resistors included in standard ports"*.
- Why it matters: (a) a host with a *dedicated* I2C Pmod port will not work with this board without a pin remap, and the board cannot be described as "a Type 6 Pmod"; (b) with no series resistance, a hot-plug or an ESD strike on P1.8/P1.9 goes directly into U5, U7 and U8 (PCA9306 HBM rating is only ±2 kV, §6.2 p.6), and a host that drives a pin while the board is unpowered injects current straight into IC input protection diodes.
- Suggested fix: document the pinout explicitly as a custom/GPIO-style Pmod rather than Type 6. Add 100–200 Ω series resistors on the six non-I2C signals (they are all low-speed), and if the board will be handled or cabled, a small ESD array on SCL/SDA/WDI.

#### F-IF-10: ~20–25 µF of hot-plug inrush on the PMOD 3.3 V rail with no limiting
- Severity: **Nice-to-have**
- Confidence: **Medium** (capacitance total is exact; host susceptibility is INFERRED)
- Where: `3V3_PMOD` net — C25 4u7, C32 4u7, C48 10u, plus C26/C27/C29/C30/C31/C33/C47/C52 100 n and C46 10 n; plus C20–C24 (≈5 µF) on BIAS when J1 selects 3V3_PMOD
- Evidence: `nets.tsv` node list for 3V3_PMOD cross-referenced against `components.tsv` values. No series element between P1.6/P1.12 and the bulk.
- Why it matters: a Pmod host supplies on the order of 100 mA and its 3.3 V rail is often a small LDO with a few µF of output cap. Plugging 20–25 µF of discharged ceramic across it draws a multi-amp inrush spike limited only by trace and connector resistance, which can brown out the host and reset the FPGA/MCU it is plugged into. This is a plug-event failure, not a steady-state one, so it will not show up in any current budget.
- Suggested fix: a small series element on the 3V3_PMOD feed (a 1–2 Ω resistor would cost 30–60 mV at 30 mA and halve the peak), or an inrush-limiting load switch, or simply reduce the bulk to what is actually needed — C48 10 µF plus C25/C32 4.7 µF is a lot for a ~2 mA digital load.

#### F-IF-11: The PCA9306 EN pin is hardwired, so the one feature that would let the bus run faster than the LT3074's 400 kHz is unavailable
- Severity: **Nice-to-have**
- Confidence: **High**
- Where: U8.8 EN, tied to U8.7 VREF2 and pulled to BIAS through R22; no connection to P1
- Evidence: LT3074 Table 1: *"Serial Bus Operating Frequency fSCL 10 kHz min, 400 kHz max"*. PAC194X datasheet §6.3: *"compatible with the SMBus 3.1 1 MHz class and the I2C Fast mode Plus"*. AD5272 p.14: standard and fast modes, 400 kHz. PCA9306 §8.1 p.10: *"The PCA9306 device can also be used to run two buses, one at 400 kHz and the other at 100 kHz… the 100 kHz bus must be disconnected by using the EN pin when the 400 kHz operation of the main bus is required"*, and §9.2 Figure 9-2 shows the EN-from-GPIO variant. This board uses Figure 9-1 (always enabled).
- Why it matters: U5 is the one device worth clocking fast — it is the measurement engine and the host will poll it continuously — but because the LT3074s hang permanently off the same logical bus, the whole bus is capped at 400 kHz. The 4k7 pull-ups independently cap it near 400 kHz as well (t_r ≈ 160–240 ns for an estimated 40–60 pF; the Fast-mode-Plus limit is 120 ns, needing ≲2.4 kΩ). Also note the C51 100 nF on the EN/VREF2 node charges through R22 200 kΩ, so the translator takes ~20 ms (1 τ) to enable after BIAS comes up — a host that starts talking to the LT3074s immediately on power-up will get NACKs.
- Suggested fix: if faster PAC polling matters, bring EN out to a spare host pin (there are none free on P1 as drawn) or accept 400 kHz and document it. Reduce R10/R41 to 2k2 if Fast-mode-Plus on the LV side is ever wanted. Reducing C51 to 10 nF cuts the enable delay to ~2 ms at no cost.

#### F-IF-12: All four connectors (P1, J1, J2, J3) have no manufacturer part number, and P1's footprint is ambiguous between a straight and a right-angle header
- Severity: **Nice-to-have**
- Confidence: **High**
- Where: `CLAUDE_REVIEW/raw/bom.csv` and `MANUFACTURING_DATA/BOM/LDO_MON_PMOD_Board_V1_BOM.csv`; footprint `klib_connectors:pmod_pin_array_6x2` at `.kicad_pcb:493`
- Evidence: all four BOM rows have empty Manufacturer / MPN / LCSC fields; all four are marked `${EXCLUDE_FROM_POS_FILES}`. The P1 footprint carries a `Dwgs.User` marker literally reading `"Board Edge"` at local (−5.25, 9.5) — absolute x ≈ 94.75, matching the actual Edge.Cuts left edge at x = 94.92 — which implies a right-angle header overhanging the edge; but its F.SilkS body outline is a symmetric rectangle from (−2.54, −7.62) to (2.54, 7.62), i.e. 5.08 × 15.24 mm, which is the body of a **straight** 2×6 0.1" header entirely on-board. The two are inconsistent.
- Why it matters: a Pmod device board needs a specific male header (conventionally right-angle, so the module plugs edge-on into the host socket). Buying a straight header when the layout assumed right-angle (or vice versa) makes the board unmountable, and with no MPN the assembler has no way to get it right. The same ambiguity means **pin-1 orientation relative to the host socket cannot be verified from the files** — pads 7–12 are the row nearer the board edge (3.81 mm) and pads 1–6 the far row (6.35 mm), and which of those mates with host pin 1 depends on the part.
- Suggested fix: specify the P1 part number, then re-check that pin 1 lands on the host's pin 1. Specify J1/J2 (Harwin values are given but no MPN) and the Phoenix MC 1,5/4-ST-3,5 mating plug for J3.

#### F-IF-13: The PAC1944's second alert output is stranded, so the host has no interrupt path from the power monitor
- Severity: **Nice-to-have**
- Confidence: **High**
- Where: `GPIO` net = R25.2 + U5.15 (GPIO/ALERT2) only; `SLOW` net = P1.2 + R24 + U5.1
- Evidence: `nets.tsv`. PAC194X datasheet §3.9 p.19: *"GPIO/ALERT2 — In default mode, this pin is a GPIO input pin. It can be configured to be an output pin, as well as the ALERT2 function. This pin is an open-drain configuration and needs a pull-up resistor to VDD."* §3.8 p.19 for SLOW/ALERT1 similarly. Only SLOW reaches P1.
- Why it matters: the PAC1944's whole comparator/alert feature set (over/under-voltage, over-current, over-power — datasheet feature list p.1) can only reach the host if P1.2 is reconfigured from SLOW to ALERT1, which then forfeits the hardware sample-rate control that R24 and P1.2 exist to provide. As drawn, the host must poll. Beyond the known dangling-label ERC warning, the substantive point is that **one of the two alert pins is physically unroutable to the host** — R25 pulls it up and it goes nowhere.
- Suggested fix: if alerts matter, route U5.15 to a host pin (P1.1's PAC_EN could arguably be strapped locally instead, freeing pin 1), or document that P1.2 must be reconfigured as ALERT1 in firmware and that hardware SLOW control is then lost.

#### F-IF-14: Two smaller interface items
- Severity: **Nice-to-have**
- Confidence: **High**
- Where / Evidence / Why:
  - **R19 (1 kΩ) pulls WDI to GND.** `nets.tsv`: `WDI 4 P1.10 R19.1 U3.1 U4.1`. The host must sink/source 3.3 mA continuously whenever it holds WDI high — a large DC load for an LVCMOS33 Pmod pin (host drive is typically ±5–24 mA on FPGAs, ±5–10 mA on MCUs, so it is legal but it is 1/3 of an MCU's budget for one pin). The fail-safe direction is correct though: a floating/tri-stated host pulls WDI low and the MAX6373 times out, which is the safe default. Consider 10 kΩ, matching every other strap on the board.
  - **J2 exposes a push-pull CMOS output on an accessible 2-pin header.** `nets.tsv`: `Net-(J2-Pin_2) 2 J2.2 U6.4(output)`. U6 is a 74LVC1G08; shorting J2.2 to an adjacent GND or to the 3V3 on J1.1 with a stray probe drives the output into a hard short with no series resistance. A 100 Ω series resistor between U6.4 and J2.2 would cost nothing (the load is R18's 10 kΩ pull-up and two high-impedance EN pins).
  - **J3 has one ground pin shared by the supply return and the load return.** `nets.tsv`: `GND … J3.4(Pin_4_4) …`. The two currents largely cancel in the pin itself, but the single shared contact is a common-impedance path between the source loop and the load loop, and it is the only safety-ground connection for a terminal block that may carry 6 A. A 5- or 6-way block with separate supply- and load-ground pins would be cleaner.

---

## Summary

The I2C subsystem is, on the whole, **done correctly** — and specifically, the single most common PCA9306 design error (pull-ups missing on one side) is **not present**: R10/R41 pull up the LV side to 3V3_PMOD and R6/R7 pull up the HV side to BIAS. The VREF2/EN/200 kΩ/100 nF arrangement matches TI's Figure 8-1 exactly, the pin assignment and translation direction are right, and the four I2C addresses (0x10, 0x2F, 0x6D, 0x6F) do not collide. The one conditional problem is that the J1 jumper can put VREF1 = VREF2, which is switch mode rather than translation (F-IF-6).

All four ERC net aliases are **deliberate and correct**. In particular `SENSE_1_N = SENSE_2_N` is required, not accidental: U1 and U2 are directly paralleled per the LT3074 datasheet's own recipe, with 2 mΩ ballast resistors taken verbatim from Figure 92, and the layout correctly taps each shunt's own pad rather than the shared pour.

The highest-value findings are F-IF-1 (4.99 kΩ series resistors are 5× the PAC1944's allowable 1 kΩ, on a device whose datasheet says no input filter is required), F-IF-2 (channel 3's high-side Kelvin tap sits 0.64 mm upstream of R16's pad, giving an estimated 5 % channel-to-channel gain asymmetry that corrupts the current-sharing measurement the board exists to make), and F-IF-3 (ALERT_N takes the BIAS domain straight to a 3.3 V host pin).

Current budget is clean: the LDO pass current comes from J3, not the PMOD, and worst-case PMOD draw is ~30 mA against a ~100 mA budget. The only PMOD-rail risk is ~20–25 µF of unlimited hot-plug inrush.
