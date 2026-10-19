# Wave 1 — Power Integrity review

Reviewer scope: power rails, decoupling, LT3074 application-circuit compliance, passive derating, supply-pin legality for U4/U5/U6/U7/U8.

Datasheet used for U1/U2: `CLAUDE_REVIEW/datasheets/LT3074_LDO.pdf` — ADI **LT3074** Rev 0, 10/2024, 62 pp. "5.5V, 3A Ultralow Noise, High PSRR, 45mV Dropout Linear Regulator with PMBus", 22-lead 3mm x 4mm LQFN. (Note this is *not* the older non-PMBus LT3074 some may remember; the PMBus/ASEL/CLKDIS/SETRES pinout in the schematic matches this datasheet exactly.)

---

## Rail inventory

| Rail (net) | Source | Nominal V | Established by the circuit? | Loads |
|---|---|---|---|---|
| `3V3_PMOD` | P1.6 + P1.12 (PMOD host VCC); also J1.1 | 3.3 V | **No** — assumed from the PMOD standard. Nothing on this board regulates or validates it. | U3.8, U4.5 (+U4.3 D-input tied high), U5.2, U6.5, U7.1, U8.2 (VREF1), D1/D2, pull-ups R10/R17/R18/R23/R24/R25/R37/R41, 12 bypass caps. In2.Cu is a full-board 3V3 plane (3200 mm²). |
| `SENSE_4_N` (= global label `V_IN`) | External, J3.3 → R35 (15 mΩ shunt) → V_IN | **Undefined** | **No.** No regulator, no silkscreen marking, no schematic note, no protection. Must be ≤ 5.5 V (LT3074 rec. op.), 6 V abs max (p.10). In3.Cu is a full-board V_IN plane. | U1.20/21/EP23, U2.20/21/EP23, C6 220 µF, C7/C10/C50 47 µF, C8/C11 4u7 |
| `OUT_1` | U1 (LT3074 #1) | 200 µA × R_SETRES — see F-PWR-1/2 | **No** — see findings | C4 22 µF, C5 100 n, U1.10 SENSE (Kelvin), R15 2 mΩ ballast, R28 sense tap |
| `OUT_2` | U2 (LT3074 #2) | same shared SETRES node | **No** | C12 22 µF, C15 100 n, U2.10 SENSE, R16 2 mΩ ballast, R29 sense tap |
| `SENSE_1_N` (= `SENSE_2_N`) | OUT_1 ∥ OUT_2 via R15/R16 — the combined paralleled output | = OUT minus ballast drop | derived | C9/C13 4u7, C17 470 n, C18/C19 100 n, R27/R30/R31 sense taps, R39 15 mΩ → `SENSE_3_N` → **J3.2 (user output)** |
| `BIAS` | J1.2 — jumper-selected to J1.1 (`3V3_PMOD`) **or** J1.3 (`EXT_VBIAS` from J3.1) | 2.375–5.5 V required, **and ≥ V_OUT + 1.2 V** (p.14) | Partly — the 3V3 option is established; the EXT option is not | U1.17, U2.17, R5 (ALERT pull-up), R6/R7 (SCL_HV/SDA_HV pull-ups), R22 → U8 VREF2/EN, C20–C24 |
| `EXT_VBIAS` | J3.1 → J1.3 only | Undefined | **No** | J1.3 only (selectable BIAS source) |
| `Net-(U1/U2-BIASAF)`, `-BIASDF` | internal LT3074 bias filters | internal | n/a | C2/C16 (2u2), C1/C14 (470 n); BIASAF also feeds the ASEL dividers and the PGFB tie |
| `Net-(U8-EN)` = PCA9306 VREF2 | BIAS via R22 200 kΩ | BIAS − (leakage × 200 k) | yes | U8.7, U8.8, C51 100 n |

Verified: `GND` is a single net, 81 nodes, with full inner planes on **In1.Cu and In4.Cu** (3200 mm² each). Stackup is 6-layer, all copper 0.035 mm (1 oz), board 80 × 40 mm.

---

## Decoupling audit — every IC power pin

Distances are centre-of-pad to centre-of-pad, computed from `LDO_MON_PMOD_Board_V1.kicad_pcb` with footprint rotation applied. "(B)" = part on B.Cu (opposite side).

| Ref | Pin | Net | Caps on that net (nearest first) | Datasheet requirement | Verdict |
|---|---|---|---|---|---|
| U1 | 20/21/EP23 IN | SENSE_4_N | C50 47u@3.4 mm, C10 47u@11.1, C11 4u7@12.1, C6 220u@13.3, C7 47u@20.9, C8 4u7 | ≥10 µF ceramic; "if a distant supply powers the LT3074, use … on the order of 220 µF" (p.35) | **OK** — 47 µF local + 220 µF electrolytic bulk. Matches Fig. 92 (47 µF) and the distant-supply advice. |
| U1 | 8/9/EP24 OUT | OUT_1 | C4 22u@2.8 mm, C5 100n@5.0 | ≥10 µF, X5R/X7R, low ESR (p.13, p.33); Fig. 92 uses 22 µF | **OK nominally** — see F-PWR-4 on derating |
| U1 | 17 BIAS | BIAS | C20 100n(B)@0.2 mm, C21@8.5, C22 4u7, C23, C24 | "This pin does not require any bypass capacitor" (p.14) | **OK** (over-provisioned, harmless) |
| U1 | 16 BIASAF | Net-(U1-BIASAF) | **C2 2u2 0603 (B) @5.4 mm** | "requires a **minimum 2.2 µF**" (p.14) | **Marginal** — exactly at minimum, 0603, no voltage rating → F-PWR-4 |
| U1 | 18 BIASDF | Net-(U1-BIASDF) | C1 470n 0402 @1.9 mm | "requires a **minimum 0.47 µF**" (p.14) | **Marginal** — exactly at minimum, 0402 → F-PWR-4 |
| U1 | 12 SETCAP | SET_CAP_NODE | C3 4u7 0603 @6.9 mm (**shared with U2**) | 4.7 µF, "high quality, low leakage" (p.13); Fig. 92 shows one shared 4.7 µF for a parallel pair | **Correct topology**, value correct; 0603 derating → F-PWR-4 |
| U1 | 13 SETRES | SET_RES_NODE | none (correct — resistive) | — | see F-PWR-1 |
| U2 | 20/21/EP23 IN | SENSE_4_N | C10 47u@3.3 mm, C11 4u7@5.9, C50@7.8 | as above | **OK** |
| U2 | 8/9/EP24 OUT | OUT_2 | C12 22u@2.8 mm, C15 100n(B)@3.9 | ≥10 µF | **OK nominally** |
| U2 | 17 BIAS | BIAS | C21 100n(B)@1.9 mm | none required | **OK** |
| U2 | 16 BIASAF | Net-(U2-BIASAF) | C16 2u2 0603 @3.2 mm | min 2.2 µF | **Marginal** |
| U2 | 18 BIASDF | Net-(U2-BIASDF) | C14 470n 0402 @2.0 mm | min 0.47 µF | **Marginal** |
| U2 | 12 SETCAP | SET_CAP_NODE | C3 @2.2 mm | 4.7 µF | **OK** |
| U3 MAX6373 | 8 VCC | 3V3_PMOD | C29 100n @1.3 mm, C52, C48 10u | — (VCC 2.5–5.5 V, p. "Electrical Characteristics") | **OK** |
| U4 74LVC1G175 | 5 VCC | 3V3_PMOD | C30 100n(B) @0.7 mm, C31, C29 | "0.1 µF bypass capacitor is recommended" (§10) | **OK** |
| U5 PAC1944 | 2 VDD | 3V3_PMOD | C33 100n @1.3 mm, C32 4u7 @2.9 | "bypass with 100 nF ceramic capacitor to ground near…" | **OK** |
| U6 74LVC1G08 | 5 VCC | 3V3_PMOD | C31 100n @1.8 mm, C30(B)@4.8 | "a 0.1 µF bypass capacitor is recommended" (§8.3) | **OK** |
| U7 AD5272 | 1 VDD | 3V3_PMOD | C46 10n(B)@3.2 mm, C48 10u@3.6, **C47 100n(B)@4.0** | "Decouple this pin with 0.1 µF ceramic capacitors **and** 10 µF capacitors" (Table 10) | **Weak** → F-PWR-13 |
| U7 AD5272 | 5 EXT_CAP | Net-(U7-EXT_CAP) | C49 1u 0402 @1.5 mm | "Connect a 1 µF capacitor… **This capacitor must have a voltage rating of ≥7 V**" (Table 10) | **Unverifiable / at risk** → F-PWR-5 |
| U8 PCA9306 | 2 VREF1 | 3V3_PMOD | C52 100n @1.8 mm, C47(B)@2.9, C48 10u@3.3 | — | **OK** |
| U8 PCA9306 | 7 VREF2 | Net-(U8-EN) | C51 100n @1.6 mm | Fig. 8-1: EN and VREF2 shorted, tied to VCC2 through 200 kΩ | **OK — wiring verified correct** |

No IC power pin is without a local bypass. Every `power_in` pin in `nets.tsv` is accounted for above.

---

## LT3074 application-circuit compliance (U1, U2)

**Topology verified:** this is the datasheet's *Direct Paralleling* configuration (p.39 and Fig. 92, p.57). The datasheet instruction is "Connect all SETRES, SETCAP, IN, and BIAS pins together. Connect the OUT pins together using… actual sense resistors (used as ballast resistors) **beyond the feedback SENSE tap** of each regulator."

- `SET_RES_NODE` ties U1.13 + U2.13 ✓
- `SET_CAP_NODE` ties U1.12 + U2.12 with one 4.7 µF ✓
- `SENSE_4_N` ties all IN pins ✓, `BIAS` ties both BIAS pins ✓
- U1.10 SENSE on `OUT_1` *before* R15, U2.10 SENSE on `OUT_2` *before* R16 ✓ ("connect the SENSE pin directly to the output capacitor")
- R15/R16 = **2 mΩ**, exactly the Fig. 92 ballast value ✓
- Symbol pin map checked against Table 5 (pp.12–14): 1 CLKDIS, 2 VIOC, 3 ALERT, 4 SCL, 5 SDA, 6 PG, 7 PGFB, 8/9 OUT, 10 SENSE, 11 AGND, 12 SETCAP, 13 SETRES, 14 IMON, 15 ASEL, 16 BIASAF, 17 BIAS, 18 BIASDF, 19 DGND, 20/21 IN, 22 EN, 23 IN-EPAD, 24 OUT-EPAD — **exact match, no pin errors.**
- CLKDIS: "If not used, tie this pin to DGND. DO NOT FLOAT" — R1/R11 200 Ω to GND. With ≤100 nA leakage this is 20 µV above GND. ✓
- PGFB: "Tie PGFB to BIASAF if power good functionality is not required" — R3/R12 1 kΩ PGFB→BIASAF. ✓ (PG left NC, which the datasheet permits: "float the PG pin".)
- ASEL: Table 10 (p.42). U1 = 47.5 k / 261 k → **7'h6F**; U2 = 69.8 k / 261 k → **7'h6D**. Both match the schematic annotations exactly. ✓
- EN: "pull-up resistor must be less than 200 kΩ" — R18 = 10 kΩ ✓ (but see F-PWR-9).
- VIOC: both floating. Datasheet p.39: when paralleling, connect one VIOC and "float all other VIOC pins". With no upstream switcher on this board, floating both is acceptable. ✓
- IMON: TP1/TP4 only — "minimize the external loading on this pin and do not drive the pin externally". ✓

**Output voltage programming.** SETRES sources **100 µA** per device (p.3). With two devices on one node the total is **200 µA**. Cross-checked against the datasheet's own figures: Fig. 89 (single device) uses R_SETRES = 5 kΩ for V_OUT = 0.5 V (0.5 V / 100 µA); Fig. 92 (two paralleled) uses **4.99 kΩ for V_OUT = 1 V** (1 V / 200 µA). So for this board:

**V_OUT = 200 µA × R(SET_RES_NODE → GND)**

R(SET_RES_NODE → GND) in this design = **R8 (0 Ω) ∥ [ R36 (0 Ω) + ( R9 50 kΩ ∥ R_AW(U7) ) ]**. See F-PWR-1 and F-PWR-2.

**Dropout.** Typical V_DO = 45 mV at 3 A, 100 mV max (p.4). V_IN is user-supplied, so dropout compliance cannot be judged — but note R35 (15 mΩ) sits between J3.3 and the IN pins and R39 (15 mΩ) sits in the output path, adding 90 mV each at 6 A: **180 mV of series resistance around a 45 mV-dropout regulator** (F-PWR-10).

**Thermal.** θJA = 33 °C/W, θJC(bot) = 3.5 °C/W, T_J(max) = 125 °C (p.11). Measured from the PCB:

| | U1 | U2 | Datasheet expectation |
|---|---|---|---|
| IN exposed pad (23) | 1.7 × 1.57 mm, **4 vias** (0.25 mm drill) → In3.Cu V_IN plane, 3200 mm² | same | "IN and OUT must be connected to large copper layers below with thermal vias" (p.41) |
| OUT exposed pad (24) | 1.7 × 0.93 mm, **2 vias** → **F.Cu island only, 26.7 mm²**, no inner-layer OUT pour | **18.2 mm²** island, 2 vias | same |

Power dissipation per device = I_OUT × (V_IN − V_OUT) + I_GND × V_BIAS, I_GND ≈ 5 mA (p.4). At θJA = 33 °C/W and T_A = 25 °C the per-device budget is ~3.0 W. At 3 A that caps V_IN − V_OUT at ~1.0 V; at the measured OUT-pad copper it will be worse than 33 °C/W. See F-PWR-7.

---

## Checks performed

| Check | Method | Result | Notes |
|---|---|---|---|
| Enumerate all power rails + sources/loads | parse `nets.tsv` + `.kicad_sch` + zone parse of `.kicad_pcb` | Done | 9 rails; 2 of them (`V_IN`, `EXT_VBIAS`) have **no** voltage established anywhere in the design |
| Local bypass on every IC power pin (U1–U8) | PCB pad-position script, footprint rotation applied, nearest-cap-on-same-net | **All power pins bypassed**; 3 marginal, 1 weak | table above |
| LT3074 parallel topology vs datasheet p.39 / Fig. 92 | datasheet read + net trace | **Correct** | SETRES/SETCAP/IN/BIAS tied, 2 mΩ ballast beyond SENSE tap |
| LT3074 symbol pinout vs Table 5 (pp.12–14) | manual compare of all 24 pins | **Correct, no errors** | |
| LT3074 ASEL divider vs Table 10 (p.42) | compute + compare | **Correct** | U1 = 0x6F, U2 = 0x6D, matches schematic text |
| LT3074 C_OUT ≥ 10 µF | BOM + net trace | **Pass nominally** (22 µF each) | derating unverifiable, F-PWR-4 |
| LT3074 C_IN ≥ 10 µF | BOM + net trace | **Pass** (47 µF local, 220 µF bulk) | matches Fig. 92 and p.35 distant-supply advice |
| LT3074 C_BIASAF ≥ 2.2 µF, C_BIASDF ≥ 0.47 µF, C_SETCAP = 4.7 µF | BOM + net trace | **Values nominally correct, all exactly at the stated minimum** | F-PWR-4 |
| LT3074 BIAS pin: required? headroom? bypassed? connected? | datasheet p.14 + `BIAS` net | **Connected (J1-selectable). Headroom rule violated in the default state** | F-PWR-2 |
| LT3074 SET resistor → V_OUT computation | datasheet p.3 + Figs. 89/92 cross-check + net trace + BOM + released POS file | **Blocker** | F-PWR-1, F-PWR-2 |
| LT3074 CLKDIS / PGFB / PG / VIOC / IMON handling | datasheet Table 5 | **All correct** | |
| LT3074 minimum load current | datasheet p.4 + p.52 + load census of `SENSE_1_N` | **Fail** | F-PWR-3 |
| Thermal: EP size, via count, copper area | PCB pad + via + zone parse | **Asymmetric; OUT path well below reference layout** | F-PWR-7 |
| High-current path trace widths | segment parse of all power nets | **Clean** — all 0.15 mm segments are Kelvin sense taps to R28–R34 (µA). Main current path is entirely zone/plane copper. | explicitly verified, not an issue |
| Capacitor voltage derating vs rail | BOM/schematic property scan | **Could not be done** — no `Voltage`, `Dielectric`, `Tolerance` or `MPN` property exists on any passive in the schematic or the released BOM | F-PWR-4 |
| 74LVC1G175 (U4) VCC | datasheet §6.3: 1.65–5.5 V | **Pass** (3.3 V) | |
| 74LVC1G08 (U6) VCC | datasheet §5.3: 1.65–5.5 V | **Pass** (3.3 V) | |
| MAX6373 (U3) VCC | datasheet Elec. Char.: 2.5–5.5 V | **Pass** (3.3 V) | |
| PAC1944 (U5) VDD + sense-pin limits | datasheet p.—: VDD 2.7–5.5 V; SENSE ±40 V abs max, 0–9 V op; \|SENSE+ − SENSE−\| ≤ 500 mV | **Pass** (3.3 V; max differential = 15 mΩ × 6 A = 90 mV) | |
| AD5272 (U7) VDD, VSS, EPAD, terminal limits | datasheet Table 8/10 | **VDD pass (2.7–5.5 V). Terminal A limit violated in the default state** | F-PWR-2 |
| PCA9306 (U8) VREF1/VREF2/EN topology | datasheet §8.1.2 Fig. 8-1, §8.1.5 Fig. 8-5/8-6 | **Wiring correct** (EN+VREF2 shorted, 200 kΩ to VCC2) | mode caveat in F-PWR-12 |
| 3V3_PMOD current budget | sum of datasheet I_CC figures | ~25–45 mA worst case | INFER — PMOD connector current spec is not in the supplied datasheet set, so "within budget" is not verified |

---

## Findings

#### F-PWR-1: R8 (0 Ω) shorts the shared SETRES node to ground — both LDO outputs are programmed to 0 V in the as-released build
- **Severity:** Blocker
- **Confidence:** High
- **Where:** R8, net `SET_RES_NODE`; `MANUFACTURING_DATA/BOM/LDO_MON_PMOD_Board_V1_BOM.csv:26`; `MANUFACTURING_DATA/Placement/LDO_MON_PMOD_Board_V1-all-pos.csv:82`
- **Evidence:**
  - `nets.tsv`: `SET_RES_NODE   4   R36.2(:passive) R8.1(:passive) U1.13(SETRES_13:unspecified) U2.13(SETRES_13:unspecified)`; `GND` contains `R8.2`.
  - LT3074 p.13, pin 13: "Reference. This pin sources the 100 µA precision current. Placing a resistor from this pin to the AGND pin of the LT3074 sets the output regulation voltage." → V_OUT = I_SETRES × R.
  - R8 value is `0R` and its schematic `(dnp no)` — verified by parsing `LDO_MON_PMOD_Board_V1.kicad_sch`. There is a bare graphic text object `"DNF"` at schematic (267.462, 115.824), 3.1 mm from R8 at (270.51, 115.57) — i.e. the intent *was* do-not-fit, but it was expressed as decoration, not as the DNP attribute.
  - Released BOM line 26: `"R8,R26,R36","3","0R","","",...` — the DNP column is **empty**.
  - Released position file line 82: `"R8","0R","R_0402_1005Metric",130.2,-95.8,0,top` — R8 **is** in the pick-and-place.
  - Grep of `LDO_MON_PMOD_Board_V1.kicad_pcb` for "DNF": **0 hits**. There is no silkscreen marking either.
- **Why it matters:** The assembler will fit R8. R(SET_RES_NODE→GND) then equals 0 Ω, so the programmed output is 0 V for *both* U1 and U2 regardless of anything the AD5272 does. The board does not produce an output voltage. This is the one thing the board exists to do. It also defeats the entire digipot subsystem (U7, R9, R36) with a single 0402.
- **Suggested fix:** Set R8's DNP attribute (`(dnp yes)` + exclude from position files) so it propagates into the BOM and CPL, and add a `DNF` / `NO FIT` silkscreen legend next to R8 on the PCB. Keep the pad so the 0 Ω can be stuffed deliberately for a 0 V test. Better still, replace it with a fixed resistor option that gives a sane default (e.g. 4.99 kΩ → 1.0 V, exactly the Fig. 92 value) and make the digipot the DNF alternative.

#### F-PWR-2: With R8 removed, the default digipot setting programs ~3.33 V — which breaks the BIAS headroom rule and exceeds the AD5272's own terminal-voltage limit
- **Severity:** Blocker
- **Confidence:** High
- **Where:** U7 (AD5272), R9, R36, net `SET_RES_NODE`, net `BIAS`, J1
- **Evidence:**
  - Schematic text at (209.55, 142.494): `"NOTE: AD5272 VERSION - 50K NOMINAL RESISTANCE"`. AD5272 datasheet, *Power-Up Sequence* (p.25): "As soon as VDD is powered, the power-on preset activates, which first sets the RDAC to **midscale**…" → R_AW ≈ 25 kΩ at power-on.
  - `nets.tsv` `Net-(U7-A)`: `R36.1 R9.1 U7.2(A_2)`; `GND` contains `R9.2` and `U7.3(W_3)`. So R(SET→GND) = 50 kΩ ∥ 25 kΩ = **16.67 kΩ**.
  - Two paralleled SETRES pins → 200 µA (LT3074 p.3 "SETRES Pin Current … 100 µA"; cross-checked against Fig. 89, single device, 5 kΩ for 0.5 V, and Fig. 92, two devices, **4.99 kΩ for 1 V**).
  - **V_OUT(default) = 200 µA × 16.67 kΩ = 3.33 V.**
  - LT3074 p.14, pin 17 BIAS: "2.375 V ≤ V_BIAS ≤ 5.5 V **and V_BIAS ≥ 1.2 + V_OUT**." With J1 strapped 1–2, `BIAS` = `3V3_PMOD` = 3.3 V → **maximum legal V_OUT = 2.1 V**.
  - AD5272 Table 8 (p.9): "V_A, V_W to GND: V_SS − 0.3 V, **V_DD + 0.3 V**"; Table 10 pin 2: "Terminal A of RDAC. **V_SS ≤ V_A ≤ V_DD**". U7.1 VDD = `3V3_PMOD` = 3.3 V, and U7.2 A sits at V_SETRES = V_OUT. Datasheet p.25: "Supply signals present on Terminal A and Terminal W that exceed VDD or VSS are clamped by the internal forward-biased diodes."
  - R9 = 50 kΩ limits R(SET→GND) to ≤ 25 kΩ, i.e. V_OUT ≤ **5.0 V**, above the LT3074's specified V_OUT range (the electrical table is specified only over 0.5 V ≤ V_OUT ≤ 4.2 V) and above anything V_BIAS ≤ 5.5 V can support (needs 6.2 V).
- **Why it matters:** Out of the box with BIAS on the PMOD 3.3 V rail, the LDOs are commanded to 3.33 V but can only support 2.1 V — they will not regulate. Simultaneously the AD5272's A-terminal ESD diode forward-biases into the 3.3 V rail, clamping the SETRES node and injecting the reference current into `3V3_PMOD`, which both corrupts the reference and is an abs-max violation of U7. Nothing in the design constrains the digipot code to the legal window, and the legal window depends on which J1 position the user chose — so the failure is silent and configuration-dependent. Even with EXT_VBIAS at 5.5 V, only codes giving V_OUT ≤ 4.2 V are valid.
- **Suggested fix:** (a) Reduce R9 so the *maximum* programmable V_OUT is safe for the worst-case BIAS. For BIAS = 3.3 V the limit is V_OUT ≤ 2.1 V → R ≤ 10.5 kΩ → R9 ≈ 13 kΩ (50 k ∥ 13 k = 10.3 kΩ → 2.06 V). (b) Either raise U7's VDD to the BIAS rail (AD5272 VDD range is 2.7–5.5 V, so it can run from BIAS) so V_A ≤ V_DD always holds, or keep R9 small enough that V_OUT can never exceed 3.3 V. (c) Add a schematic note stating the legal digipot code range per J1 position.

#### F-PWR-3: No minimum preload on the output — the LT3074 asserts a fault on every power-up of an unloaded board
- **Severity:** Should-fix
- **Confidence:** High
- **Where:** nets `OUT_1`, `OUT_2`, `SENSE_1_N`
- **Evidence:**
  - LT3074 p.52 (MFR_IOUT_MIN_WARN_LIMIT): "**If the LT3074 is powered on without a preload greater than the default value set by MFR_MIN_IOUT_WARN_LIMIT register, the LT3074 asserts a fault once it completes the start-up procedure.**" Default MFR_IOUT_MIN_WARN_LIMIT = 0xA19A = **0.1001 A** (Table 6, p.30).
  - LT3074 p.4: "Minimum Load Current I_OUT(MIN): V_OUT ≥ 0.8 V → 10 mA; V_OUT < 0.8 V → **50 mA**."
  - Load census of the output: `OUT_1` = C4, C5, R15, R28 (4k99 into a PAC1944 high-Z input); `OUT_2` = C12, C15, R16, R29; `SENSE_1_N` = C9, C13, C17, C18, C19, R27/R30/R31 (4k99 sense taps), R39 → J3.2. **There is no DC load anywhere.** The PGFB divider (R3/R12) hangs off BIASAF, not OUT.
- **Why it matters:** A demo board will be powered with nothing wired to J3 pins 2/4 most of the time. In that state both devices will flag a fault on `ALERT_N` at every start-up, which is exactly the signal a user would be evaluating, and the output regulation itself is out of spec below 10 mA. If the digipot is ever set below 0.8 V the requirement jumps to 50 mA.
- **Suggested fix:** Fit a preload resistor from `SENSE_1_N` to GND sized for ≥ 100 mA at the lowest intended V_OUT (e.g. 10 Ω for 0.5 V → 50 mA, or 5 Ω for 100 mA at 0.5 V — budget the dissipation), or at minimum document that the host must raise MFR_IOUT_MIN_WARN_LIMIT and that a load is required. A jumper-selectable preload would suit a demo board.

#### F-PWR-4: No voltage rating, dielectric or tolerance is specified for any capacitor — and three LT3074 minimum-capacitance requirements sit exactly on the minimum in small packages
- **Severity:** Should-fix
- **Confidence:** High (the omission); Medium (the resulting violation, which depends on the part actually bought)
- **Where:** every C in `LDO_MON_PMOD_Board_V1.kicad_sch`; `MANUFACTURING_DATA/BOM/LDO_MON_PMOD_Board_V1_BOM.csv`
- **Evidence:**
  - Property census of the schematic: the only properties present on any symbol are `Value`, `Reference`, `Footprint`, `Description`, `Datasheet`, `Intersheetrefs`. There is **no** `Voltage`, `Dielectric`, `Tolerance` or `MPN` field on any passive. The released BOM has columns `Reference, Qty, Value, DNP, Exclude*, Footprint, Datasheet` only.
  - LT3074 p.33 warns about exactly this: "Give extra consideration to the type of ceramic capacitors used… When used with a 5 V regulator, a 16 V, 10 µF Y5V capacitor can exhibit an effective value as low as 1 µF to 3 µF."
  - The at-risk parts, all sitting on a DC rail of ~3.3 V and all specified by the datasheet as *minimums*:
    - **C2, C16 — 2u2 in 0603 on BIASAF.** Requirement: "The LT3074 requires a **minimum 2.2 µF** bypass capacitor on this pin" (p.14). A 2.2 µF/6.3 V X5R 0603 typically loses 35–50 % at 3.3 V DC bias → ~1.1–1.4 µF, **below the minimum**. A 2.2 µF/25 V X7R 0603 would lose ~10 % and be fine. The BOM does not say which.
    - **C1, C14 — 470n in 0402 on BIASDF.** Requirement: "minimum 0.47 µF" (p.14). Same exposure, 0402 is worse.
    - **C3 — 4u7 in 0603 on SETCAP.** Datasheet p.13: "Bypassing the SETCAP pin to AGND with a 4.7 µF capacitor decreases output voltage noise… Analog Devices recommends the use of a **high quality, low leakage** capacitor." Noise spec (p.6): 4.7 µF → 1.2 µV_RMS, 0.47 µF → 1.6 µV_RMS. An 0603 4u7/6.3 V at 3.3 V bias can fall to ~2.3 µF, degrading the headline ultralow-noise figure this board is built to demonstrate.
    - **C4, C12 — 22u in 1210 on OUT.** Requirement ≥10 µF. 1210 derates far less; even a 6.3 V X5R at 3.3 V (~40 % loss) leaves ~13 µF. **This one passes** even under pessimistic assumptions.
- **Why it matters:** As released, nothing stops the assembler from choosing the cheapest 6.3 V X5R for every line item. For C2/C16 and C1/C14 that silently puts the part below a stated datasheet minimum on the internal bias filters, which is where bias-rail noise and PSRR come from. For C3 it costs the noise spec. None of this is detectable without pulling the actual assembled parts.
- **Suggested fix:** Add `Voltage`, `Dielectric` and `MPN` fields to every capacitor and emit them in the BOM. Specify ≥16 V X7R for C1/C2/C3/C14/C16 (or go up a case size), ≥16 V X7R/X5R for C4/C12, and an explicit rating for C6 (220 µF electrolytic on V_IN). Where the datasheet states a minimum, choose the nominal value so the *post-derating* value still clears it.

#### F-PWR-5: C49 (AD5272 EXT_CAP) has an explicit ≥7 V rating requirement that the BOM does not carry
- **Severity:** Should-fix
- **Confidence:** High
- **Where:** C49 (1u, 0402), net `Net-(U7-EXT_CAP)`, U7.5
- **Evidence:** AD5272 datasheet Table 10, pin 5: "External Capacitor. Connect a 1 µF capacitor between EXT_CAP and VSS. **This capacitor must have a voltage rating of ≥7 V.**" Also Table 8: "EXT_CAP to VSS … 7 V". The requirement exists because EXT_CAP carries the internally generated 50-TP programming voltage (datasheet Figure 36, "V_EXT_CAP Waveform While Writing Fuse"), which rises well above VDD.
- **Why it matters:** 1 µF in 0402 is very commonly stocked only as 6.3 V. Fitting a 6.3 V part risks damaging the capacitor the first time a 50-TP wiper value is burned, and the AD5272 requires this capacitor "on power-up and **throughout the operation**" (p.25) — losing it takes the digipot, and hence the output voltage setting, with it. A 1 µF/10 V in 0402 also derates hard; at the internal programming voltage the effective capacitance will be a fraction of 1 µF.
- **Suggested fix:** Specify a 1 µF ≥10 V X7R, and move C49 to 0603 so a 10 V/16 V part with usable effective capacitance is actually obtainable.

#### F-PWR-6: The V_IN rail is a bare user-accessible screw terminal into a 6 V abs-max pin pair, with no protection and no marking
- **Severity:** Should-fix
- **Confidence:** High
- **Where:** J3.3 → R35 → net `SENSE_4_N` (= `V_IN`) → U1.20/21/EP23, U2.20/21/EP23
- **Evidence:**
  - `nets.tsv`: `SENSE_4_P  3  J3.2(Pin_3_3) R33.2 R35.2`; `SENSE_4_N  14  … U1.20 U1.21 U1.23 U2.20 U2.21 U2.23`.
  - J3 footprint is `Connector_Phoenix_MC:PhoenixContact_MC_1,5_4-G-3.5_1x04_P3.50mm_Horizontal` — a user-wirable screw/spring terminal.
  - LT3074 Table 2 (p.10): "IN Pin Voltage: **−0.3 V to 6 V**"; recommended max V_IN = 5.5 V (p.3).
  - `components.tsv` contains no TVS, no series FET, no fuse, no reverse-polarity device.
  - Text-object enumeration of `LDO_MON_PMOD_Board_V1.kicad_pcb` silkscreen returns only `"1"`, `"GND"`, `"VCC"` — there is no silk legend naming J3's pin functions or stating a voltage limit, and no voltage limit appears anywhere in the schematic text either.
  - Note the same exposure applies to J3.1 `EXT_VBIAS` → J1.3 → `BIAS`, abs max 6 V (p.10), and `EXT_VBIAS` has no protection either.
- **Why it matters:** A 12 V bench supply on the wrong terminal destroys both LT3074s, and the parasitic diodes noted on p.10 mean a reverse connection takes them out too. On a demo board handed to evaluators this is the most likely field failure, and nothing on the board warns the user.
- **Suggested fix:** Add a 5.5–6 V TVS/Zener clamp plus a series fuse (or a reverse-polarity P-FET) on `SENSE_4_P` and on `EXT_VBIAS`, and silkscreen `V_IN 0–5.5 V MAX` and the pin-function legend next to J3.

#### F-PWR-7: The OUT exposed pad has no inner-layer copper and only 2 thermal vias — well short of the datasheet's reference layout
- **Severity:** Should-fix
- **Confidence:** Medium (the geometry is measured; the resulting θJA is inferred)
- **Where:** U1 pad 24 / net `OUT_1`, U2 pad 24 / net `OUT_2`, PCB zones
- **Evidence (measured from `LDO_MON_PMOD_Board_V1.kicad_pcb`):**

| | IN side (pad 23) | OUT side (pad 24) |
|---|---|---|
| EP size | 1.70 × 1.57 mm | 1.70 × 0.93 mm |
| Vias in package body | 4 × ⌀0.25 mm (both U1 and U2) | **2 × ⌀0.25 mm** |
| Copper reached | `SENSE_4_N` **full In3.Cu plane, 3200 mm²** + 61.6 mm² F.Cu zone | F.Cu island only — **OUT_1 26.7 mm², OUT_2 18.2 mm²**, no inner-layer pour |

  - LT3074 p.11: θJA = 33 °C/W, θJC(bot) = **3.5 °C/W** — i.e. the dominant heat path is out of the bottom pads, both of them.
  - LT3074 p.41 *Thermal Considerations*: "The IN **and OUT** pins at the bottom of the package should be soldered to IN and OUT planes accordingly. In addition, the IN **and OUT** must be connected to large copper layers below with thermal vias… Placing additional vias can reduce thermal resistance further."
  - Note the 33 °C/W figure is footnoted "θJA value is obtained with **demo board**" (p.11); p.41 gives 30–36 °C/W for a 4-layer 3×4 LQFN and warns "the θJA numbers vary beyond the 30 °C/W to 36 °C/W depending on board composition and layout".
  - Worked budget at θJA = 33 °C/W, T_J(max) = 125 °C, T_A = 25 °C → 3.0 W per device. P = I_OUT × (V_IN − V_OUT) + I_GND × V_BIAS, I_GND ≈ 5 mA (p.4). At 3 A that allows V_IN − V_OUT ≈ 1.0 V. At V_IN − V_OUT = 0.3 V and 3 A, P = 0.92 W (the datasheet's own worked example, p.41) and the rise is ~30 °C — comfortable.
  - U1 and U2 are 9.0 mm apart on the PCB (128.5, 98.5) and (128.5, 107.5) and share the same In3 V_IN plane, so they heat each other; the "spreading heat on the PCB" benefit the datasheet cites for paralleling (p.39) is only partly realised at that pitch.
- **Why it matters:** With only ~20–27 mm² of 1 oz front copper and two vias on the OUT pad, roughly half the designed bottom-side heat path is missing. The practical consequence is that the safe V_IN − V_OUT at 3 A is lower than the 1.0 V the datasheet's θJA would suggest, and there is nothing on the board (no VIOC loop — both VIOC pins float) holding the input-to-output differential down. A user sweeping V_OUT down with the digipot while holding V_IN fixed walks straight into thermal shutdown at 168 °C (p.5).
- **Suggested fix:** Add OUT_1/OUT_2 pours on at least one inner layer under each package and raise the OUT EP via count from 2 to 6–9 (the pad is 1.7 × 0.93 mm, so ⌀0.2 mm vias on a 0.5 mm grid fit). Add a schematic/user-guide note giving the maximum V_IN − V_OUT versus load. Also consider marking pads 23/24 with `pad_prop_heatsink` in the footprint (U7's EP has it; U1/U2's do not) so KiCad's thermal handling and the fab's documentation treat them correctly.

#### F-PWR-8: `ALERT_N` carries the BIAS-domain pull-up straight to the PMOD connector with no level translation
- **Severity:** Should-fix
- **Confidence:** High
- **Where:** net `ALERT_N`, R5, P1.3, U1.3, U2.3, U8
- **Evidence:**
  - `nets.tsv`: `ALERT_N  4  P1.3(P3_3:passive) R5.2(:passive) U1.3(ALERT_N_3) U2.3(ALERT_N_3)`; `BIAS` contains `R5.1`.
  - So R5 (10 kΩ) pulls `ALERT_N` up to `BIAS`, and `ALERT_N` goes directly to PMOD pin 3.
  - Every other LT3074 bus signal *is* translated: `SCL_HV`/`SDA_HV` (pulled up to BIAS via R6/R7) go only to U8.6/U8.5, and the PMOD side `SCL`/`SDA` are pulled to `3V3_PMOD` via R10/R41. ALERT is the single exception.
  - LT3074 p.13, pin 3: "Open-Drain Digital Output… A pull-up resistor to **the highest supply rail** is required."
  - `BIAS` is user-selectable to `EXT_VBIAS` (J1.3 ← J3.1), legal up to 5.5 V (p.3).
- **Why it matters:** If a user straps J1 to EXT_VBIAS and feeds it 5 V — which the LT3074 explicitly permits and which the PCA9306 translation mode actually wants (TI §8.1.2 needs VCC2 ≥ VREF1 + 0.7 V ≈ 4.0 V for translation) — then PMOD pin 3 idles at 5 V into a 3.3 V host FPGA/MCU pin. The PCA9306 has two channels, both already used by SCL/SDA, so the translator cannot absorb ALERT.
- **Suggested fix:** Pull `ALERT_N` up to `3V3_PMOD` instead of `BIAS` (it is open-drain, so a 3.3 V pull-up is sufficient to be read by both the host and nothing else), or add a third translation channel / a single-FET translator for ALERT.

#### F-PWR-9: The ENABLE pull-up is loaded by the Q1 LED driver base, leaving ~0.1–0.2 V of margin over the LT3074 EN threshold when J2 is open
- **Severity:** Nice-to-have
- **Confidence:** Medium
- **Where:** net `ENABLE` — R18, R40, R43, Q1, J2.1, U1.22
- **Evidence:**
  - `nets.tsv`: `ENABLE  5  J2.1 R18.2 R40.1 R43.1 U1.22(EN_22)`; `3V3_PMOD` contains `R18.1`; `Net-(Q1-B)  2  Q1.1(B_1:input) R43.2`.
  - R18 = 10 kΩ to 3V3, R43 = 4.7 kΩ into Q1's base. With Q1 conducting (V_BE ≈ 0.7 V) the node solves to V_ENABLE = (4.7 × 3.3 + 10 × 0.7) / 14.7 = **1.53 V**.
  - LT3074 p.6: "EN Pin Threshold, EN_VTHR, EN Trip Point Rising: min 1.20, typ 1.26, **max 1.32 V**."
  - Margin at 25 °C = 1.53 − 1.32 = **0.21 V**. At +125 °C V_BE falls to ≈0.5 V, giving V_ENABLE ≈ 1.40 V and a margin of **0.08 V** before resistor tolerance.
- **Why it matters:** This only bites when J2 is left open (the AND-gate/watchdog path disconnected), i.e. the "always-on, LED shows enabled" standalone mode — which is the obvious default for a demo board. With ~80 mV of worst-case margin, part-to-part V_BE spread plus 1 % resistors could leave a board that will not enable, or that sits near the trip point and chatters on the 80 mV hysteresis (p.6).
- **Suggested fix:** Drive the LED from `3V3_PMOD` through a buffer, or take Q1's base from a point other than the EN node, or raise R43 to ~47 kΩ (V_ENABLE rises to ~2.7 V; Q1 base current drops to ~55 µA, still enough to saturate Q1 into the ~1.3 mA the R44 1 kΩ LED branch draws).

#### F-PWR-10: R35 and R39 (15 mΩ) put 180 mV of series drop around a 45 mV-dropout regulator, and dissipate 0.54 W each at full load
- **Severity:** Nice-to-have
- **Confidence:** High
- **Where:** R35, R39 (`15mR`, `R_2512_6332Metric`, schematic text `WSL2512R0150FEA`)
- **Evidence:**
  - `nets.tsv`: R35 sits between `SENSE_4_P` (J3.3, the user's input) and `SENSE_4_N` (= V_IN, the LDO IN pins). R39 sits between `SENSE_1_N` (the combined LDO output) and `SENSE_3_N` (J3.2, the user's output).
  - LT3074 p.4: V_DO = 45 mV typ / 100 mV max at 3 A. The two paralleled devices support 6 A, so each 15 mΩ shunt drops 15 mΩ × 6 A = **90 mV** and dissipates 15 mΩ × 36 = **0.54 W**.
  - The schematic names the part WSL2512R0150FEA — a Vishay WSL2512, 1 W rated. 0.54 W is 54 % of rating, so derating is acceptable but the part will run hot in a 2512.
- **Why it matters:** The headline feature of the LT3074 is 45 mV dropout. Two monitoring shunts in the path add four times that in series resistance, so the voltage the user actually sees at J3.2 is 180 mV below what READ_VOUT reports, and the usable V_IN at the connector has to be 180 mV higher than the LDO needs. For a board whose purpose is to *demonstrate* the dropout figure, this measurably works against the demo.
- **Suggested fix:** Either reduce R35/R39 toward 5 mΩ (accepting the reduced PAC1944 full-scale signal — at 6 A, 5 mΩ still gives 30 mV, well within the PAC1944's range) or document the offset explicitly so users subtract it. Note the per-LDO shunts R15/R16 are 2 mΩ and dissipate only 18 mW at 3 A each — those are fine.

#### F-PWR-11: R9 (50 kΩ) sets a maximum programmable output of 5.0 V, above the LT3074's specified 4.2 V ceiling and above anything V_BIAS can support
- **Severity:** Nice-to-have
- **Confidence:** High
- **Where:** R9, net `Net-(U7-A)`
- **Evidence:** R9 50 kΩ ∥ R_AW(max) 50 kΩ = 25 kΩ; × 200 µA = **5.0 V**. The LT3074 electrical table (pp.3–4) is specified only over 0.5 V ≤ V_OUT ≤ 4.2 V, and V_BIAS ≥ V_OUT + 1.2 V (p.14) would demand 6.2 V against a 5.5 V maximum. At the other extreme, code 0 gives R_AW = the 35–70 Ω wiper resistance (AD5272 spec table) → V_OUT ≈ 14 mV, also outside the 0.5 V floor and below the 0.8 V point where the minimum load requirement jumps to 50 mA (p.4).
- **Why it matters:** The digipot's useful range is a narrow slice of its 1024 codes, and both ends of the sweep are out of specification. With BIAS on the PMOD 3.3 V rail, only codes up to ~272/1024 (V_OUT ≤ 2.1 V) are legal — 27 % of the range. Nothing in the design or the silkscreen says so.
- **Suggested fix:** Covered by F-PWR-2(a): pick R9 so the top of the digipot range lands at the maximum V_OUT the chosen BIAS can support, which simultaneously improves the per-code resolution across the usable range.

#### F-PWR-12: PCA9306 operates as a plain switch, not a translator, in the J1 = 3V3_PMOD position — and the intermediate BIAS band is neither
- **Severity:** Nice-to-have
- **Confidence:** High
- **Where:** U8, net `BIAS`, net `3V3_PMOD`, J1
- **Evidence:**
  - Wiring is **correct** per TI §8.1.2 Figure 8-1: `nets.tsv` `Net-(U8-EN)  4  C51.1 R22.2 U8.7(VREF2_7:power_in) U8.8(EN_8:input)` with R22 = 200 kΩ to `BIAS`. "the enable pin and VREF2 are shorted together and tied to a 200-kΩ resistor" — exactly as built. The warning in §8.1.2 ("Care should be taken to make sure VREF2 has an external resistor tied between it and VCC2") is satisfied.
  - PCA9306 §6.3 note: "To support translation, VREF1 supports 1.2 V to **VREF2 − 0.6 V**. VREF2 must be between VREF1 + 0.6 V to 5.5 V." §8.1.5: "PCA9306 has the capability of being used with its VREF1 voltage equal to VREF2. This essentially turns the device from a translator to a device which can be used as a switch."
  - With J1 = 1–2, VREF1 = VREF2 = 3.3 V → the documented switch configuration (Figure 8-5). Legal, but prop delays differ (§8.1.5) and there is no level shift.
  - With J1 = 2–3 and EXT_VBIAS between ~3.4 V and 4.0 V, the part is in neither regime: VREF2 − VREF1 is below the 0.6–0.7 V the translator needs but above zero.
- **Why it matters:** Not a defect, but the board behaves differently on the I2C bus depending on a jumper that is primarily about LDO bias, and the 3.4–4.0 V EXT_VBIAS window gives marginal translator behaviour. Worth documenting rather than changing.
- **Suggested fix:** Note on the schematic / in the user guide: "J1 = 3V3: PCA9306 in switch mode. J1 = EXT: use EXT_VBIAS ≥ 4.0 V for proper level translation (and ≥ V_OUT + 1.2 V for the LT3074)."

#### F-PWR-13: AD5272 VDD decoupling is weaker than the datasheet asks, with the nearest 100 nF 4.0 mm away on the opposite side of the board
- **Severity:** Nice-to-have
- **Confidence:** High
- **Where:** U7.1, net `3V3_PMOD`
- **Evidence:** AD5272 Table 10, pin 1: "Positive Power Supply. **Decouple this pin with 0.1 µF ceramic capacitors and 10 µF capacitors.**" Measured nearest caps on `3V3_PMOD` to U7's VDD pad: C46 (10n, B.Cu) @3.2 mm, C48 (10u, F.Cu) @3.6 mm, C47 (100n, B.Cu) @4.0 mm, C52 (100n) @5.5 mm. There is no 0.1 µF on the same side within 4 mm. By contrast U4 has C30 at 0.7 mm, U5 has C33 at 1.3 mm, U6 has C31 at 1.8 mm — the rest of the board is done well.
- **Why it matters:** Low risk in practice (the AD5272 is a 400 kHz I2C part), but U7 sets the output voltage of both LDOs, and a glitch on its supply during a 50-TP write is the one place a supply disturbance has a persistent consequence. The In2.Cu 3V3 plane plus C48 at 3.6 mm mitigates it.
- **Suggested fix:** Move C47 (or add a 100 nF 0402) onto F.Cu within ~1.5 mm of U7 pin 1.

---

## Explicitly clean results

These were checked against the named datasheet page and found correct — reported so they are not re-reviewed:

1. **LT3074 parallel topology** matches the datasheet's *Direct Paralleling for Higher Output Current* (p.39) and Figure 92 (p.57) item by item, including the 2 mΩ ballast value and the placement of the SENSE taps upstream of the ballast.
2. **LT3074 symbol pin map** (24 pins including both exposed pads) matches Table 5 (pp.12–14) exactly. No swapped or missing power pins.
3. **ASEL address dividers** match Table 10 (p.42) exactly: U1 47.5 k/261 k = 0x6F, U2 69.8 k/261 k = 0x6D, both agreeing with the schematic's own annotations.
4. **CLKDIS, PGFB, PG, VIOC, IMON** are all handled exactly as Table 5 prescribes for unused/paralleled operation.
5. **Input capacitance** (47 µF local ceramic per device + 220 µF electrolytic bulk) satisfies both the ≥10 µF stability minimum and the "on the order of 220 µF" guidance for a distant supply (p.35). C6's polarised symbol is correctly paired with a polarised `CP_Elec_8x10` footprint.
6. **Output capacitance** C4/C12 = 22 µF/1210 clears the ≥10 µF minimum even under pessimistic DC-bias derating, and matches Fig. 92's 22 µF.
7. **PCA9306 EN/VREF2/200 kΩ topology** is the textbook TI Figure 8-1 arrangement, including the §8.1.2 warning about needing a series resistor to VCC2.
8. **Logic and monitor supply voltages are all legal at 3.3 V:** 74LVC1G175 1.65–5.5 V (§6.3), 74LVC1G08 1.65–5.5 V (§5.3), MAX6373 2.5–5.5 V, PAC1944 2.7–5.5 V, AD5272 2.7–5.5 V, PCA9306 VREF1 0–5.5 V.
9. **PAC1944 sense-pin limits** are satisfied with margin: common mode ≤ 5.5 V against a 0–9 V operating / 40 V abs-max rating, and the maximum differential (15 mΩ × 6 A = 90 mV) is well inside the 500 mV abs max.
10. **No narrow traces in any high-current path.** Every 0.15 mm segment on `SENSE_4_N`, `SENSE_4_P`, `OUT_1`, `OUT_2`, `SENSE_1_N` and `SENSE_3_N` was traced to its endpoints and all of them are Kelvin sense taps into R28–R34 (4k99 into PAC1944 high-impedance inputs, microamps). The load current path runs entirely on zone and plane copper.
11. **Ground and 3V3 distribution:** full-board GND planes on In1.Cu and In4.Cu, full-board 3V3 plane on In2.Cu, full-board V_IN plane on In3.Cu, all 1 oz. A good stackup for this board.
12. **AD5272 pin usage:** EPAD (pin 11) tied to VSS/GND, which Table 10 permits ("Leave floating or tie to VSS"); W (pin 3) to GND, A (pin 2) to the SET node — correct 2-terminal rheostat connection; the 200 µA through it is far inside the ±2 mA continuous limit for the 50 kΩ option (Table 8).

## Checks I could not complete

| Check | Reason |
|---|---|
| Actual DC-bias derating of every ceramic | No voltage rating or dielectric is specified anywhere in the schematic or the released BOM (F-PWR-4). All derating statements above are bounded estimates for the stated case size, flagged as such. |
| Whether V_IN is within the LT3074's range in practice | V_IN is user-supplied at J3.3; nothing in the design, schematic text or silkscreen states an intended value (F-PWR-6). |
| 3V3_PMOD current-budget compliance | The PMOD connector specification is not in the supplied datasheet set. Computed load is ~25 mA typical / ~45 mA worst case from the component datasheets, which is comfortable against the commonly cited 100 mA PMOD guideline, but I have not verified that figure against a primary source. |
| Precise minimum neck width of the zone-routed power path at J3 | Would need a geometric minimum-width analysis of the filled polygons; bounding boxes (SENSE_4_P 6.2 × 3.4 mm, SENSE_3_N zone 16.3 mm²) suggest ≥2 mm of 1 oz copper, which is adequate for 6 A, but this is an estimate, not a measurement. |
| Actual θJA of the assembled board | Requires thermal simulation. F-PWR-7 reports measured copper/via geometry and compares it to the datasheet's reference layout rather than asserting a number. |
