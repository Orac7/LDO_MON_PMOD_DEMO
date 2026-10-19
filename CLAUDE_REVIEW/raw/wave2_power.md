# Wave 2 — adversarial verification of `wave1_power.md`

Role: REFUTER. Every datasheet quotation below was re-extracted from the PDF bytes in `CLAUDE_REVIEW/datasheets/` with `pdftotext -layout`, page-located with `-f N -l N`. Every number was re-derived. Page numbers cited as "p.N" are the **printed page N of 62** shown in the LT3074 footer, which for this PDF is also the physical PDF page (verified: the footer on PDF page 54 reads "54 of 62").

Headline: **three of the four claims survive, but not all of the reasoning does.** The two findings I was told to suspect hardest (C) and attack (A) both turn out to be correct on substance, with citation and remedy errors. The real casualties are two *adjacent* claims Wave 1 made that I checked in passing: **F-PWR-9 is built on a wrong component value**, and **the AD5272 abs-max part of F-PWR-2 is false at the default setting**.

---

## CLAIM A — "two paralleled SETRES pins source 200 µA; default V_OUT = 3.33 V"

### Verdict: **CONFIRMED**
Corrected severity: **Blocker** (conditional on R8 being unfitted — see note A5). Confidence: **High**.

I tried hard to break this and could not. The datasheet corroborates it in three independent places, one of which Wave 1 did not cite and which is the strongest of the three.

**A1. I_SETRES from the ELECTRICAL CHARACTERISTICS table, not a figure (p.3), as instructed:**

| Parameter | Symbol | Conditions | Min | Typ | Max | Unit |
|---|---|---|---|---|---|---|
| SETRES Pin Current³ | I_SETRES | Max [2.375, V_OUT + 1.2 V] ≤ V_BIAS ≤ 5.5 V, V_OUT + 0.2 V ≤ V_IN ≤ 5.5 V, 0.5 V ≤ V_OUT ≤ 4.2 V, 50 mA ≤ I_OUT ≤ 3 A, MFR_MARGIN = 8'h00, **T_J = 25 °C** | 99.5 | **100** | 100.5 | µA |
| SETRES Pin Current | I_SETRES | same, **over the full operating temperature range** | 99 | **100** | 101 | µA |

So: typical **100.0 µA**, tolerance **±0.5 % at 25 °C, ±1 % over temperature**, *per device*. Wave 1's "100 µA (p.3)" is exact and the page is right. Wave 1 did not state the tolerance; for a pair the worst case is **198–202 µA**.

Caveat Wave 1 missed and that matters for this board: that ±1 % is only guaranteed inside the stated window, which includes `50 mA ≤ I_OUT ≤ 3 A` and `V_BIAS ≥ V_OUT + 1.2 V`. On an unloaded board with BIAS = 3.3 V and V_OUT commanded to 3.33 V, **neither condition holds**, so the 200 µA is nominal-physics, not a guaranteed number, in exactly the default state being analysed.

**A2. Figure 89 — checked, says what Wave 1 claims.** PDF p.41, "Figure 89. Programming Input-to-Output Voltage Differential". Single LT3074. Schematic text extraction: `RSETRES 5kΩ` ... `VOUTLDO = 0.5V`, `IOUT(MAX) = 3A`. 0.5 V / 5 kΩ = 100 µA. ✔

**A3. Figure 92 — checked, says what Wave 1 claims, and the 4.99 kΩ *is* the SETRES resistor.** PDF p.57, "Figure 92. Paralleling Multiple LT3074s for Higher Output Current". Two LT3074 blocks. The extracted label block reads:

```
            RSETRES       CSETCAP
             4.99kΩ        4.7µF
                 1%
```

drawn on the common SETRES/SETCAP rail below the second device, alongside `VOUT = 1V`, `IOUT(MAX) = 6A`, `RBALLAST1/2 2mΩ`. It is explicitly named `RSETRES` and it is the only resistor on that node, so no, it is not something else (the ASEL divider in the same figure is separately labelled `47.5kΩ / 261kΩ`). The body text on p.39 independently confirms the 1 V figure: *"The two 2 mΩ external resistors only add 6 mV of output regulation drop with 6 A maximum current. **With a 1 V output**, this voltage drop only adds 0.6 % to the regulation accuracy."* ✔

**A4. The decisive corroboration Wave 1 did not cite — Table 8, p.31.** "1% Resistors for Common Output Voltages": **0.5 V → 4.99 kΩ**, 0.8 V → 8.06 kΩ, 1.0 V → 10.0 kΩ, 1.2 V → 12.1 kΩ, 2.5 V → 24.9 kΩ, 3.3 V → 33.2 kΩ. This table is for a single device. So the *same* 4.99 kΩ resistor yields 0.5 V with one device (Table 8) and 1 V with two (Fig. 92). The doubling is proven by the datasheet contradicting itself unless the currents add. This is stronger evidence than the Fig. 89 / Fig. 92 pair Wave 1 used, because it removes the possibility that Fig. 89's "5 kΩ" is a rounded stand-in for something else.

**A5. Is SETRES genuinely shared in *this* design?** Yes. `netlist.net` line 9934, net `SET_RES_NODE`, nodes = R36.2, R8.1, **U1.13, U2.13**. `nets.tsv` line 61 agrees. There is one SETRES node, not two. ✔

**A6. Independent re-derivation of the default output voltage.**

- *Is the AD5272 really preset to midscale?* Partly. The verbatim text, AD5272 **p.25**, *Power-Up Sequence*: *"As soon as V_DD is powered, the power-on preset activates, which **first sets the RDAC to midscale and then restores the last programmed 50-TP value** to the RDAC register."* Corroborated by p.24 (RESET description) and Table 10 pin 7: *"Factory default loads midscale **until the first 50-TP wiper memory location is programmed**."* So midscale is correct **for a virgin part only**. Once anyone burns a 50-TP location, the power-up default becomes that burned value permanently and irreversibly. Wave 1's quotation is accurate but it truncated the sentence before the clause that changes the behaviour. Practically this does not rescue the board — a factory-fresh assembly powers up at midscale — but it does mean the "default" is not a fixed property of the design.
- *R_WA at midscale.* AD5272 p.24 eq. (1): `R_WA(D) = (D/1024) × R_WA`. At D = 512, R_WA = **25.00 kΩ**. Note the resistance is **proportional** to code (not inverse) and the wiper is at GND here, so code 0 → wiper resistance only (35–70 Ω, Table 2) and code 1023 → 49.95 kΩ. (Wave 1's F-PWR-11 got this orientation right.)
- *Does R9 really parallel the digipot?* Yes, read from `nets.tsv`: `Net-(U7-A) = R36.1, R9.1, U7.2(A_2)`; `GND` contains **both** `R9.2` **and** `U7.3(W_3)`. So R9 (A→GND) and the RDAC A–W path (A→W→GND) are two paths between the same two nodes. Parallel, not series. ✔ Full expression `R8 ∥ [R36 + (R9 ∥ R_WA)]` is correct.
- *Arithmetic, re-derived:* 50 kΩ ∥ 25 kΩ = (50×25)/75 = **16.667 kΩ**. 200 µA × 16.667 kΩ = **3.3333 V**. ✔ Wave 1's 3.33 V reproduces exactly.
- *Tolerance band:* 198–202 µA × 16.667 kΩ = 3.30–3.37 V, before AD5272 ±1 % and R9 tolerance (unspecified — see Claim D).

**A7. The one thing that weakens the finding as written:** it only bites with **R8 unfitted**, and the released BOM/CPL fit R8 (F-PWR-1). Wave 1 states this dependency explicitly in F-PWR-2's title, so the two findings are consistent — but they are mutually exclusive in any single build, and the report presents both as independent Blockers. They should be a single Blocker with two branches: *R8 fitted → 0 V; R8 removed → 3.33 V*. Neither branch produces a working board. The conclusion survives either way.

**Adjacent real issue A8 — the 50 kΩ variant is not in the buildable data.** This is a better-framed Blocker than F-PWR-2 and Wave 1 missed it.
- Schematic symbol `Value = "AD5272BCP"` (`LDO_MON_PMOD_Board_V1.kicad_sch:4057`). No `-20` / `-50` / `-100` suffix. The `Manufacturer`, `MPN` and `LCSC` columns in `components.tsv` are **empty** for U7, and the released BOM has no MPN column at all.
- The only statement that it is the 50 kΩ part is a **free-floating graphic text object** at schematic (209.55, 142.494): `"NOTE: AD5272 VERSION - 50K NOMINAL RESISTANCE"` — the same class of object as the `"DNF"` that F-PWR-1 correctly flags as non-propagating.
- Consequence, computed: with R9 = 50 kΩ fixed and the part at midscale, the default output is **1.67 V (20 kΩ part: 10 k ∥ 50 k = 8.33 k)**, **3.33 V (50 kΩ part)**, or **5.00 V (100 kΩ part: 50 k ∥ 50 k = 25 k)**. An assembler buying "AD5272BCP" can legitimately fit any of the three, and two of those three outputs are outside the LT3074's specified 0.5–4.2 V range or its BIAS headroom.
- **Severity: Blocker. Suggested fix:** put the orderable part number (e.g. `AD5272BCPZ-50-RL7`) in the symbol `Value` or a populated `MPN` field so it reaches the BOM, and keep the text note as a comment only.

---

## CLAIM B — "V_BIAS ≥ V_OUT + 1.2 V caps V_OUT at 2.1 V when J1 straps BIAS to 3V3_PMOD"

### Verdict: **CONFIRMED**
Corrected severity: **Blocker**. Confidence: **High**.

**B1. Exact wording and page.** LT3074 **p.14**, Table 5, pin 17 BIAS — verbatim:

> *"Bias Supply. This pin supplies current to the internal control circuitry and the output stage driving the pass transistor. This pin does not require any bypass capacitor. **To ensure proper operation, the BIAS voltage must satisfy the following conditions: 2.375 V ≤ V_BIAS ≤ 5.5 V and V_BIAS ≥ 1.2 + V_OUT.**"*

Page confirmed by `pdftotext -f 14 -l 14`. Wave 1's citation is exact and the page is right.

**B2. Is it a minimum, a typical, or a maximum?** It is a **hard requirement**, and it is the form the brief asked me to check for — "a fixed minimum, whichever is greater":
- Restated identically on **p.37**, *BIAS/BIASAF/BIASDF Pin Requirements*: *"To ensure proper operation, the BIAS voltage must satisfy the following conditions: 2.375 V ≤ V_BIAS ≤ 5.5 V and V_BIAS ≥ V_OUT + 1.2 V."* ("must", twice, in two independent sections.)
- The ELECTRICAL CHARACTERISTICS table (p.3) encodes it as the test condition **`Max [2.375, V_OUT + 1.2 V] ≤ V_BIAS ≤ 5.5 V`** — i.e. exactly `max(fixed floor, V_OUT + 1.2 V)` — and that condition gates I_SETRES, V_OS, line/load regulation and essentially every guaranteed spec.
- The Dropout Voltage rows (p.4) are separately conditioned `V_BIAS ≥ V_OUT + 1.2 V`.
- There is **no** min/typ/max column for the 1.2 V itself and no temperature qualifier — it is a boundary of the guaranteed operating region over the full temperature range, not a typical.

**B3. Is BIAS optional?** No. There is no "if BIAS is not used" language anywhere in the datasheet (I grepped the full text). Contrary evidence that it is mandatory: BIAS drives the pass-transistor gate driver (p.14); the part has a BIAS UVLO (`MFR_BIAS_UV_WARN_LIMIT` 0xC8, default 0xC91A, p.30) and `MFR_DEFAULT_CONFIG` is documented as *"can be used to detect a BIAS UVLO event"*; and every application figure (87, 89, 92, 93) shows BIAS driven. Wave 1 is right not to treat it as optional.

**B4. Arithmetic.** 3.3 V − 1.2 V = **2.1 V**. ✔ And it is worse than Wave 1 says: 3V3_PMOD is the host's rail with no regulation on this board (Wave 1's own rail table), so at the low end of a ±5 % host rail (3.135 V) the ceiling is **1.94 V**, and after the PMOD connector/plane drop, lower still. Nothing on the board measures or guards this.

**B5. One wording downgrade.** Wave 1 writes "they will not regulate". The datasheet does not say the part fails below the headroom — it says operation outside the window is simply not guaranteed. Physically, insufficient BIAS starves the pass-device driver and the part behaves as if in dropout: the output comes up short and quietly, with full PMBus telemetry still running and reporting the shortfall. The practical outcome matches Wave 1's conclusion; the mechanism is "silently undershoots", not "refuses to regulate". This does not change the severity — a demo board that silently cannot reach its own default setpoint is a Blocker.

---

## CLAIM C — "p.52: powering up without a preload > MFR_IOUT_MIN_WARN_LIMIT (100 mA) makes the part assert a fault after start-up"

### Verdict: **CONFIRMED on substance; two errors found**
Corrected severity: **Should-fix** (unchanged). Confidence: **High**.

I was asked to attack this hardest, on the theory that `MFR_IOUT_MIN_WARN_LIMIT` is foreign vocabulary from another part. **That theory is wrong, and I can show it.**

**C1. Is the LT3074 a PMBus device? Yes, unambiguously.**
- Title, p.1: *"5.5 V, 3 A Ultralow Noise, High PSRR, 45 mV Dropout Linear Regulator **with PMBus**"*.
- p.29: *"The LT3074 supports PMBus compliant serial interface for control, telemetry, and fault reporting…"*, followed by **Table 6, "Supported PMBus Commands"**.
- p.46: *"The LT3074 is compliant with the **PMBus version 1.3, both part I and part II**."*
So the PMBus vocabulary is native to this part, not imported from a sibling or a companion device. The register is real and in Table 6, p.30:

| Command | Code | Description | Type | Format | Default |
|---|---|---|---|---|---|
| `MFR_IOUT_MIN_WARN` | 0xC9 | Minimum output current warning limit | R/W Word | L11 | **0xA19A** |

**C2. Default decoded independently.** Format L11 = Linear_5s_11s (Table 7, p.30): `Value = Y × 2^N`, `N = b[15:11]` signed, `Y = b[10:0]` signed.
`0xA19A = 1010_0001_1001_1010b` → `N = 10100b = −12`, `Y = 000_1100_1101_0b`… re-reading the low 11 bits directly: `0xA19A & 0x7FF = 0x19A = 410`.
**Value = 410 × 2⁻¹² = 410/4096 = 0.100098 A = 100.1 mA.** ✔ Wave 1's figure is exact.

**C3. What is actually on the cited page — and it is not p.52.** `grep -c preload` over pages 48–58 returns a hit on **exactly one page: PDF page 55**. The sentence lives at the end of the `MFR_IOUT_MIN_WARN_LIMIT` command description, verbatim:

> *"If the LT3074 is powered on without a preload greater than the default value set by MFR_MIN_IOUT_WARN_LIMIT register, the LT3074 asserts a fault once it completes the start-up procedure."*

**ERROR 1 — the page citation is wrong: it is p.55, not p.52.** Wave 1's other LT3074 page citations that I spot-checked (p.3 I_SETRES, p.4 I_OUT(MIN), p.14 BIAS, p.30 Table 6 / 0xA19A, p.33 ceramic warning, p.57 Fig. 92) are all **correct**, so this is an isolated slip, not a pattern. Note also that the datasheet spells the register three different ways — `MFR_IOUT_MIN_WARN` (Table 6), `MFR_IOUT_MIN_WARN_LIMIT` (section heading), `MFR_MIN_IOUT_WARN_LIMIT` (the preload sentence itself). Wave 1 used the heading form; that is the datasheet's own inconsistency, not the reviewer's.

**C4. What "asserts a fault" actually means — mild downgrade.** The same page enumerates the response:
> *"Sets the NONE_OF_THE_ABOVE bit in STATUS_BYTE register. Sets the MFRSPECIFIC bit in the STATUS_WORD register. Sets the IOUT_MIN_WARNING bit in the STATUS_MFR_SPECIFIC register. Notifies the host by asserting the ALERT pin."*

It is a **warning**, not a protection event: no shutdown, no latch-off, no output disable. The regulator keeps regulating. Wave 1 never claimed otherwise ("will flag a fault on ALERT_N"), so the finding stands as written, but the word "fault" (the datasheet's own word) reads more alarming than the behaviour is.

**C5. Is there a genuine minimum-load requirement? Yes, separately.** ELECTRICAL CHARACTERISTICS, **p.4**:

| Parameter | Symbol | Conditions | Max | Unit |
|---|---|---|---|---|
| Minimum Load Current | I_OUT(MIN) | V_OUT ≥ 0.8 V | **10** | mA |
| | | V_OUT < 0.8 V | **50** | mA |

Max-column-only, no typ. This is a real regulation requirement independent of the PMBus warning, and Wave 1 cites it correctly.

**C6. Load census re-verified from `nets.tsv`.** `OUT_1` = C4, C5, R15(2 mΩ ballast, series), R28(4k99 Kelvin tap), U1.8/9/10/24. `OUT_2` = C12, C15, R16, R29, U2 pins. `SENSE_1_N` = C9, C13, C17, C18, C19, R15.2, R16.2, R27/R30/R31 (4k99 taps into PAC1944 high-Z sense inputs), R39.1. `SENSE_3_N` = J3.2, R32.2, R39.2. **No resistor to GND anywhere on the output.** Confirmed: zero DC preload.

**ERROR 2 — the suggested fix is undersized by 4×, and self-contradictory.** Each LT3074 runs its own ADC and its own `READ_IOUT`/warning comparison against its own 100.1 mA limit. With two devices sharing current roughly evenly (Fig. 92 claims "better than 20 % accurate output current sharing"), a 100 mA total preload gives each device ~50 mA and **both still warn**. The preload must exceed **~200 mA total** (>100 mA per device, plus margin for the 20 % sharing error → call it 250 mA) to suppress the warning on both. Wave 1's fix text says "sized for ≥ 100 mA" and then offers "10 Ω for 0.5 V → 50 mA" as an example, which fails its own criterion by 2× and the real criterion by 5×. At V_OUT = 0.5 V a 250 mA preload needs 2 Ω / 0.125 W; at V_OUT = 3.3 V the same 2 Ω draws 1.65 A and burns 5.4 W, so a fixed preload cannot span the programmable range — this argues for the jumper-selectable preload Wave 1 mentions in passing, or for simply documenting that the host must write `MFR_IOUT_MIN_WARN_LIMIT` at init.

**C7. Compounding factor Wave 1 missed.** Both devices' ALERT pins sit on one net (`ALERT_N` = U1.3, U2.3, R5.2, P1.3). The host sees one assertion and must poll both PMBus addresses (0x6F, 0x6D) to find out which device warned — and on an unloaded board, both always will.

---

## CLAIM D — "C2/C16 (2u2 0603, BIASAF) and C1/C14 (470n 0402, BIASDF) sit on datasheet minimums; no voltage rating anywhere"

### Verdict: **CONFIRMED**
Corrected severity: **Should-fix**. Confidence: **High** for the omission and the minimums; **Medium** for the derating violation (depends on a part not yet chosen — Wave 1 says this itself, correctly).

**D1. Are BIASAF/BIASDF real LT3074 pin names? Yes.** Table 5, p.14:
> *"16 **BIASAF** — Bias Filter Pin for analog circuity. The LT3074 **requires a minimum 2.2 µF** bypass capacitor on this pin."*
> *"18 **BIASDF** — Bias Filter Pin for digital circuity. The LT3074 **requires a minimum 0.47 µF** bypass capacitor on this pin."*

Restated on **p.37**: *"The LT3074 **requires a minimum 2.2 µF** bypass capacitor on the BIASAF pin and **0.47 µF** bypass capacitor on the BIASDF pin **for stability and proper operation**. … Do not externally load the BIASAF and/or the BIASDF pins."* Both are stated as minimums with requirement language, in two independent sections. ✔ Not recommendations.

**D2. Net connectivity re-verified** (`nets.tsv` lines 20, 21, 27, 28): `Net-(U1-BIASAF)` = C2.1, R3.2, R4.1, U1.16 · `Net-(U1-BIASDF)` = C1.1, U1.18 · `Net-(U2-BIASAF)` = C16.1, R12.2, R13.1, U2.16 · `Net-(U2-BIASDF)` = C14.1, U2.18. Values and packages from `components.tsv`: C1/C14 = `470n` `C_0402_1005Metric`; C2/C16 = `2u2` `C_0603_1608Metric`. ✔ Exactly as claimed.

**D3. Is the DC-bias premise sound?** Yes. p.37: *"The BIASAF and BIASDF pins are **internally tied to the BIAS pin through separate filter resistors**."* With negligible external DC load on those pins, both sit at ≈ V_BIAS = 3.3 V. So the caps really do see ~3.3 V of DC bias. ✔

**D4. Is "no voltage rating appears anywhere" true? Yes — verified directly, not inferred.** Exhaustive enumeration of every `(property "…")` key in `LDO_MON_PMOD_Board_V1.kicad_sch` returns the complete set: `Component Class`, `Datasheet`, `Description`, `Footprint`, `Intersheetrefs`, `ki_fp_filters`, `ki_keywords`, `Netclass`, `Reference`, `Value`. There is **no** `Voltage`, `Dielectric`, `Tolerance` or `MPN` key on any symbol in the file. (Wave 1's list of present properties omitted `Component Class` and `Netclass` — immaterial, neither carries a rating.) The released BOM header is `Reference, Qty, Value, DNP, Exclude from BOM, Exclude from Board, Exclude from Simulation, Exclude from Position Files, Footprint, Datasheet` — same conclusion. `components.tsv` *has* `Manufacturer`, `MPN`, `LCSC` columns but they are **empty for every passive**. Claim D's second half is fully confirmed.

**D5. Evidence Wave 1 under-used.** The LT3074 datasheet goes further than the Y5V warning Wave 1 quoted. p.34, immediately after Figure 86 (*"Capacitor Voltage Coefficient for Different Case Sizes"*):
> *"While capacitance changes due to DC bias for X5R and X7R is better than Y5V and Z5U dielectrics, **it can still be significant enough to drop the capacitance below sufficient levels**. As shown in Figure 86, capacitor DC bias characteristics tend to improve as component case size increases. However, **verification of expected capacitance at the operating voltage is highly recommended**. Due to its good voltage coefficient in small case sizes, **Analog Devices recommends using the Murata GCM series ceramic capacitors.**"*

The datasheet names a specific series for exactly this reason, and the BOM cannot express it. That strengthens the finding.

**D6. The one genuine weakening.** The characterisation conditions printed at the head of every ELECTRICAL CHARACTERISTICS block (pp.3–8) read: *"C_OUT = 22 µF, C_SETCAP = 4.7 µF, **C_BIASAF = 2.2 µF, and C_BIASDF = 0.47 µF**, unless otherwise noted."* So the designer did not pick values that merely scrape a minimum — these are the datasheet's **own reference values**, the ones all the published specs were measured with. The defect is therefore precisely and only the missing dielectric/voltage specification, not the nominal value choice. Wave 1's framing ("sit exactly on datasheet minimums") is accurate but implies poor value selection where none occurred. The remedy is unchanged: specify ≥16 V X7R (or GCM) so the *post-derating* value still clears 2.2 µF / 0.47 µF.

**D7. Not re-derivable from primary evidence:** the "35–50 % loss at 3.3 V for a 2.2 µF/6.3 V X5R 0603" figure is a vendor-typical, not in either supplied datasheet. Figure 86 only plots a 25 V 10 µF part in 0805/1206/1210. So the *magnitude* of the violation remains an estimate — which is exactly how Wave 1 labelled it (Confidence: Medium on the violation). Fair.

---

## Collateral: two Wave 1 claims I checked in passing that do NOT survive

### F-PWR-9 — **REFUTED.** R18 is 1 kΩ, not 10 kΩ.
Severity: **not a defect** (down from Nice-to-have). Confidence: **High**.

`components.tsv` line for R18: `R18 ⟶ 1k ⟶ Resistor_SMD:R_0402_1005Metric`. The schematic agrees. Wave 1 used 10 kΩ in both F-PWR-9 and in its LT3074 compliance checklist ("EN: … R18 = 10 kΩ ✓").

Re-derived with the actual value: V_ENABLE = (4.7 × 3.3 + 1 × 0.7) / (4.7 + 1) = (15.51 + 0.7) / 5.7 = **2.84 V**. Margin over the 1.32 V max EN rising threshold (p.6) = **1.52 V**, not 0.21 V. At 125 °C with V_BE = 0.5 V: (15.51 + 0.5)/5.7 = 2.81 V, margin **1.49 V**. There is no marginality.

This matters beyond the arithmetic: **`DESIGN_INTENT.md` RP-1 states authoritatively that R18 = 1 k and that 10 k would leave ~0.2 V of margin.** Wave 1 independently re-derived the owner's own warning and then mis-attributed the hypothetical 10 k value to the as-built design. The analysis is correct; the premise is not. The correct output here is not a defect report but the **schematic note RP-1 explicitly asks for**, placed beside R18 — which Wave 1's report does not deliver.

### F-PWR-2's AD5272 abs-max argument — **REFUTED at the default setting; real only at high codes.**
Severity of the surviving part: **Should-fix**, and it belongs in F-PWR-11, not F-PWR-2. Confidence: **High**.

Wave 1 asserts that at the 3.33 V default *"the AD5272's A-terminal ESD diode forward-biases into the 3.3 V rail, clamping the SETRES node and injecting the reference current into `3V3_PMOD`, which … is an abs-max violation of U7."* Checking the numbers:
- AD5272 Table 8 absolute maximum: `V_A, V_W to GND = V_SS − 0.3 V to **V_DD + 0.3 V**` = **3.6 V** here.
- V_A at the default = **3.33 V**. That is **270 mV below** the absolute maximum. **No abs-max violation.**
- A silicon ESD diode at 30 mV of forward bias (3.33 V node vs 3.3 V rail) conducts on the order of nanoamps. It does not clamp the node and it does not inject the 200 µA reference into 3V3_PMOD.

What *is* true at the default: the **Table 10 recommended operating condition** `V_SS ≤ V_A ≤ V_DD` is exceeded — by **30 mV**. That is a specification-compliance nit, not a damage mechanism, and the AD5272's rheostat accuracy near the rail is the only thing at risk.

The mechanism Wave 1 describes becomes real further up the code range. Solving for V_A = V_DD + 0.3 = 3.6 V: R_total = 3.6 V / 200 µA = 18.0 kΩ; with R9 = 50 kΩ in parallel, R_WA = 1/(1/18k − 1/50k) = **28.125 kΩ** → **D = 576**. So **codes 576–1023 (44 % of the range) do push the AD5272 A terminal past its absolute maximum**, reaching 5.0 V at full scale. That is a genuine Should-fix and it reinforces F-PWR-11's "pick a smaller R9" remedy — but it is a *high-code* hazard, not a *default-state* one, and stating it as part of the out-of-the-box failure overstates the default case.

---

## Summary table

| Claim | Wave 1 severity | Verdict | Corrected severity | Confidence |
|---|---|---|---|---|
| **A** — 200 µA on shared SETRES; default 3.33 V | Blocker | **CONFIRMED** (reasoning sound; stronger evidence available in Table 8, p.31) | Blocker — but merge with F-PWR-1 as one finding with two branches | High |
| **B** — V_BIAS ≥ V_OUT + 1.2 V caps V_OUT at 2.1 V | Blocker | **CONFIRMED** (p.14 verbatim, restated p.37, encoded in the EC conditions as `Max[2.375, V_OUT+1.2]`) | Blocker | High |
| **C** — no preload → warning on every power-up | Should-fix | **CONFIRMED** on substance; page is **p.55 not p.52**; it is a warning not a shutdown; **suggested fix undersized 4×** (needs >200 mA for the pair) | Should-fix | High |
| **D** — BIASAF/BIASDF caps at minimum, no voltage rating | Should-fix | **CONFIRMED**; the "no rating anywhere" half is verified exhaustively. Weakened only in framing: 2.2 µF/0.47 µF are the datasheet's **own** characterisation values | Should-fix | High (omission) / Medium (violation) |
| *F-PWR-9* — ENABLE margin ~0.2 V | Nice-to-have | **REFUTED** — R18 is **1 k**, not 10 k; real margin **1.52 V**; contradicts `DESIGN_INTENT.md` RP-1 | Not a defect (convert to the RP-1 schematic note) | High |
| *F-PWR-2, AD5272 abs-max half* | part of Blocker | **REFUTED at default** (3.33 V vs 3.6 V abs max, 270 mV of margin); **real for codes ≥ 576** | Should-fix, reassign to F-PWR-11 | High |
| *New* — AD5272 resistance variant absent from BOM/symbol | not raised | **New finding**; default output is 1.67 V / 3.33 V / 5.00 V depending on which "AD5272BCP" is bought | Blocker | High |
