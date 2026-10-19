# Wave 1 — Supervisor and Logic Review (watchdog / enable / control path)

Scope: U3 (MAX6373), U4 (74LVC1G175), U6 (74LVC1G08), Q1 (MMBT3904), JP1/JP2/JP3, J2, R17–R21, R40, R43, R44, C28, and the path to U1.22/U2.22 (LT3074 EN) and to P1 (PMOD).

## 1. Reconstructed watchdog subsystem

Derived entirely from `CLAUDE_REVIEW/raw/nets.tsv` (every node listed below is a literal entry in that file), cross-checked against the KiCad netlist regenerated from commit `125b2fa^` for the "before" state.

```
                    3V3_PMOD (PMOD P1.6 / P1.12 — host-supplied)
                       |        |        |        |            |
                       |       JP1.3    JP2.3    JP3.3        R17 (10k)
                       |        |        |        |            |
                    U3.8      JP1.2    JP2.2    JP3.2          |
                    VCC      (common)  (common) (common)       |
                       |        |        |        |            |
   +-------------------+--------+--------+--------+            |
   |  U3  MAX6373  (SOT-23-8, open-drain WDO)                  |
   |   pin1 WDI   <--- net WDI                                 |
   |   pin2 GND                                                |
   |   pin3 N.C.  (no-connect flag, nothing attached)          |
   |   pin4 SET0  <--- Net-(JP1-C)   [JP1.1 = GND, JP1.3 = 3V3]|
   |   pin5 SET1  <--- Net-(JP2-C)   [JP2.1 = GND, JP2.3 = 3V3]|
   |   pin6 SET2  <--- Net-(JP3-C)   [JP3.1 = GND, JP3.3 = 3V3]|
   |   pin7 /WDO  ---> Net-(U3-~{WDO})  (open_collector) -------+
   |   pin8 VCC                                                |
   +-----------------------------------------------------------+
                                     |
                       Net-(U3-~{WDO}) = U3.7 + R17.2 + C28.1 + U4.6
                                     |         (C28 = 100n to GND)
                                     v
   WDI  (P1.10 ---- R19 1k ---- GND) |
     |                               |
     +-----------------+             |
     |                 |             |
   U3.1 (WDI)        U4.1 (CLK)    U4.6 (/CLR)
                       |
   3V3_PMOD --------> U4.3 (D)   [hard-tied high]
   +------------------------------------+
   |  U4  74LVC1G175  single D-FF, async clear (SOT-23-6)
   |  1=CLK 2=GND 3=D 4=Q 5=VCC 6=/CLR   (VERIFIED, DS p.3)
   +------------------------------------+
                       |
             Net-(U4-Q) = U4.4 + R21.1(10k to GND) + U6.1
                       |
                     U6.1 (A)
   CNTRL (P1.4 --- R20 10k --- GND) --> U6.2 (B)
   +------------------------------------+
   |  U6  74LVC1G08  2-input AND (DRL-5)
   |  1=A 2=B 3=GND 4=Y 5=VCC            (VERIFIED, DS p.3)
   +------------------------------------+
                       |
                   U6.4 (Y)
                       |
            Net-(J2-Pin_2) = U6.4 + J2.2
                       |
                   [ J2 ]  2-pin 2.54 header, shunt NOT fitted as shipped
                       |
            ENABLE = J2.1 + R18.2 + R40.1 + R43.1 + U1.22(EN)
                       |        |        |        |
                       |     R18 1k   R40 100R  R43 4k7
                       |     to 3V3      |        |
                       |              U2.22(EN)  Q1.1 (B)
                       |                          |
                       |                 Q1.2 E = GND, Q1.3 C -- R44 1k -- D2(K)
                       |                                    D2(A) = 3V3  (enable LED)
```

Boolean behaviour: `EN(LT3074) = J2_fitted ? (Q_ff AND CNTRL) : 1`, where `Q_ff` is set by a rising edge on WDI (D tied high) and asynchronously cleared by a MAX6373 timeout pulse on `/WDO`.

## 2. Checks performed

| Check | Method | Result | Notes |
|---|---|---|---|
| Identify what `125b2fa` actually changed | `git show 125b2fa --stat` + schematic diff; regenerated the pre-fix netlist with `kicad-cli sch export netlist` from `125b2fa^` | Change isolated to R18 and J2 placement/wiring | Only two symbols moved: R18 220.98→241.3, J2 (245.11,179.07)→(238.76,198.12), plus the y=187.96 ENABLE wire broken either side of J2 |
| Verify the pre-fix bug | Old netlist node lists | **Confirmed real and severe** — see F-LOGIC-2 | OLD: `J2.1` was a member of `3V3_PMOD`; `J2.2` sat on the net containing `U6.4` |
| Verify the fix works in BOTH jumper states | Netlist + DC analysis | **Correct and complete** | J2 open → ENABLE = 2.84 V via R18; J2 fitted → U6 drives ENABLE. No node floats into a CMOS input in either state |
| U4 pinout + every input pin driven | 74LVC1G175 DS p.3 (Pin Functions) vs nets.tsv | **Clean** | CLK=WDI, D=3V3_PMOD, /CLR=WDO net, Q=output, VCC/GND correct. No floating input |
| U6 pinout + every input pin driven | 74LVC1G08 DS p.3 (Pin Functions, DRL column) vs nets.tsv | **Clean** | A=U4.Q, B=CNTRL(R20 pulldown), Y=output, VCC/GND correct. No floating input |
| MAX6373 SET0/1/2 strapping legality | MAX6373 DS p.3 (EC conditions "SET_ = V_CC or GND"), p.6 (Pin Description), p.7 Table 1, p.9 "Selecting Device Timing" | **FAILS** — see F-LOGIC-1 | No floating/tri-state option exists anywhere in this datasheet family |
| MAX6373 timeout actually selected | Table 1 p.7 | **Undefined** as shipped | Depends entirely on which JPs the user bridges |
| WDI driven correctly | MAX6373 DS p.6 pin 1: "Connect WDI to ground with a 100k (max) resistor if not driven externally" | **Clean** | R19 = 1k to GND, well inside the 100k limit; also driven by host P1.10 |
| Watchdog disable available | Table 1 p.7, row SET2=0/SET1=1/SET0=1 | **Available and intentional** | Reachable by bridging JP3→GND, JP2→3V3, JP1→3V3. Plus the J2 bypass |
| Open-drain net has a pullup | nets.tsv pin-type `open_collector` census (1 pin) + MAX6373 DS p.9 "A 10kΩ pullup is sufficient in most applications" | **Clean, value endorsed by datasheet** | Only open-collector pin in the design is U3.7; R17 = 10k to 3V3_PMOD |
| Power-up defined states on all reset/enable nets | nets.tsv | **Clean except SET0/1/2** | CNTRL→R20 10k pulldown; WDI→R19 1k pulldown; U4.Q→R21 10k pulldown; ENABLE→R18 1k pullup; DP_RST_N→R37 10k pullup; PAC_EN→R23 10k pullup; SLOW→R24 10k pullup; GPIO→R25 10k pullup; U8 EN→R22 200k to BIAS |
| Edge rate into U4 /CLR | R17×C28 = 10k × 100n; 74LVC1G175 DS p.5 Δt/Δv ≤ 10 ns/V at 3.3 V | **Violated by ~5×10⁴** — see F-LOGIC-4 | 0.8 V→2.0 V takes 0.65 ms ⇒ ≈545 µs/V |
| ENABLE high level vs LT3074 EN threshold | LT3074 DS EC table: ENVTHR 1.20/1.26/1.32 V, hysteresis 80 mV, IEN ≤ 5 µA; abs-max EN = −0.3 to 6 V | **Clean, good margin** | J2 open: 2.84 V (R18 1k loaded by Q1's R43 4k7 + Vbe). J2 fitted + U6 high: ≈3.2 V. Both ≫ 1.32 V |
| ENABLE low level vs LT3074 EN falling threshold | 74LVC1G08 VOL table; falling threshold = 1.26 − 0.08 = 1.18 V | **Clean, huge margin** | U6 sinks 3.3 mA through R18; VOL ≪ 0.1 V (spec is 0.4 V max at 16 mA) |
| Watchdog-kicks-itself lockout | Trace of power domains | **Clean — no lockout** | WDI is driven by the PMOD host on P1.10, powered from 3V3_PMOD. U1/U2 outputs (OUT_1/OUT_2) feed only external loads via J3; they do not power the host, U3, U4 or U6 |
| U3 bypass cap placement | MAX6373 DS p.9: 0.1 µF within 0.2 in (5.08 mm) of VCC/GND; PCB footprint coordinates | **Clean** | C29 (100n) at 2.36 mm from U3, same layer. Also U4↔C30 (100n) at 0.0 mm (directly under, B.Cu); U6↔C31 (100n) at 2.39 mm |
| U3 pin 3 N.C. handling | MAX6373 DS p.6: "Do not make any connection to this pin" | **Clean** | `unconnected-(U3-NC-Pad3)` is a 1-node net with a no-connect flag; no copper attached |
| Q1 LED driver bias | DC calc | Works, but dim | Ib ≈ 0.46 mA, Ic limited to ≈1.1 mA by R44 1k + D2 Vf. Saturated, LED visible but faint |
| ERC/DRC hits in this subsystem | grep of `erc_strict.rpt` for U3/U4/U6/JP*/J2/Q1/ENABLE/WDI/WDO/CNTRL | None | Only hit is the already-known `power_pin_not_driven` on U3.8 |
| Could NOT check | — | — | Whether the assembly/user documentation specifies a JP1/JP2/JP3 setting — no README or assembly note exists in the repo for this board |

## 3. Findings

### F-LOGIC-1: MAX6373 SET0/SET1/SET2 float on an unmodified board — watchdog timeout is undefined
- **Severity:** Blocker
- **Confidence:** High
- **Where:** U3.4/U3.5/U3.6; nets `Net-(JP1-C)`, `Net-(JP2-C)`, `Net-(JP3-C)`; JP1/JP2/JP3 = `SolderJumper_3_Open`
- **Evidence:**
  - `nets.tsv`: `Net-(JP1-C)  2  JP1.2(C_2:passive) U3.4(SET0_4:input)` — and identically for JP2/SET1 and JP3/SET2. Each of these three nets contains **exactly two nodes**: the floating common pad of an open solder jumper, and a CMOS logic input. There is no resistor, no default strap, nothing else.
  - MAX6373 datasheet p.3, Electrical Characteristics header: *"(V_CC = +2.5V to +5.5V, **SET_ = V_CC or GND**, …)"* — every parameter in the table is only specified for the SET pins at a rail.
  - MAX6373 datasheet p.6, Pin Description for pins 4/5/6: *"**Logic input** for selecting startup delay and watchdog timeout periods."* — a plain logic input, not a tri-level input.
  - MAX6373 datasheet p.7, Table 1 "Minimum Timeout Settings": the SET2/SET1/SET0 columns contain only `0` and `1`. There is no third state.
  - MAX6373 datasheet p.9, "Selecting Device Timing": *"Timeout settings can be hard wired, or they can be controlled with logic gates"* — both options drive the pins.
  - `components.tsv`: all three are `SolderJumper_3_Open` / `Jumper:SolderJumper-3_P1.3mm_Open_RoundedPad1.0x1.5mm`, i.e. **no copper bridge in the default artwork**; the common pad is isolated until a user adds solder.
- **Why it matters:** This is not a cosmetic ERC complaint — the MAX6373 has no internal pull on these pins and no defined floating state. On a board as manufactured, the selected timeout is whatever the three floating pins happen to settle at, decided by leakage, flux residue, humidity and capacitive coupling from the GND pad (JPx.1) and 3V3 pad (JPx.3) sitting 1.3 mm either side. Concretely:
  - If the pins drift to `SET2=1, SET1=0, SET0=0`, Table 1 gives **t_WD = 30 µs** for the MAX6373. The host would have to strobe WDI faster than 30 µs or the watchdog fires continuously, clearing U4 and holding both LT3074s off forever (whenever J2 is fitted). The board looks dead.
  - If they drift to `0,1,1` the watchdog is silently **Disabled**, so the supervisor appears to work but provides no protection — the worst outcome for a supervisor.
  - If they drift to `0,0,1` the timeout is 3 s; if `1,1,1` it is 10 s. The behaviour can differ board-to-board and change after a wash or over time.
  - Additionally, a CMOS input parked mid-rail holds both stages of the input inverter partly on. The 74LVC parts spec this as ΔI_CC 500 µA per input; the MAX6373 does not spec it at all because the condition is outside its data sheet.
- **Suggested fix:** Give every SET pin a defined default. Either (a) change JP1/JP2/JP3 to `SolderJumper_3_Bridged12` (or `..._Bridged23`) so the artwork ships with a known strap and the user cuts/moves it, or (b) keep the open jumpers and add three 100 kΩ resistors from each SET pin to the intended default rail, so an un-bridged board still has a legal state and bridging a jumper simply overrides the weak pull. For this application the most useful default is `SET2=1, SET1=0, SET0=1` → MAX6373 **t_DELAY = "First Edge", t_WD = 1 s** (Table 1 p.7, with Note 3 p.5: *"In this setting the watchdog timer is inactive and startup delay ends when WDI sees its first level transition"*). That removes any chance of a spurious timeout before the host has booted, which is exactly the behaviour this board wants.

### F-LOGIC-2: The `125b2fa` fix is CORRECT — the original bug was a hard short of the 74LVC1G08 output to 3V3
- **Severity:** (resolved — recorded for the record; no action)
- **Confidence:** High
- **Where:** J2, R18, U6.4; `git show 125b2fa -- '*.kicad_sch'`
- **Evidence:** Netlist regenerated from `125b2fa^` gives:
  - `3V3_PMOD -> … J2.1 JP1.3 JP2.3 JP3.3 …`  ← **J2 pin 1 was on the 3.3 V rail**
  - ENABLE-equivalent net `-> J2.2 R18.2 R40.1 R43.1 U1.22 U6.4` ← **J2 pin 2 was on the same net as the AND gate's push-pull output**

  Current netlist (`nets.tsv`):
  - `Net-(J2-Pin_2)  2  J2.2 U6.4(:output)`
  - `ENABLE  5  J2.1 R18.2 R40.1 R43.1 U1.22(EN_22)`

  Schematic diff confirms the mechanism: the wire run at y = 187.96 was cut either side of J2 (new wires `227.33,187.96 → 215.9,187.96` and `229.87,187.96 → 241.3,187.96`, with no wire between 227.33 and 229.87), and R18 was relocated from x = 220.98 to x = 241.3 so it now pulls up the ENABLE side only.
- **Why it mattered:** In the old design, fitting the J2 "bypass" shunt connected 3V3_PMOD directly to pin 4 (Y) of U6. Whenever the AND gate was outputting low — which is its **power-up default**, because CNTRL is pulled low by R20 10k and Q is cleared by C28 — the shunt would have put the 3.3 V rail across the gate's low-side FET. The 74LVC1G08 absolute-maximum continuous output current is ±50 mA (DS §5.1); with an on-resistance in the tens of ohms the fault current would be an order of magnitude above that. The part would be destroyed, probably on the first power-up after fitting the jumper, and the "bypass" feature would have appeared to work for a few seconds before failing. Fixing this before fab was the right call.
- **Verification of completeness (both jumper states):**
  - **J2 open (as shipped):** ENABLE is pulled to 3V3 through R18 1k. Loads are Q1's base path (R43 4k7 + V_BE) plus 2 × ≤5 µA of LT3074 EN current, so I ≈ (3.3 − 0.7)/(1k + 4k7) = 0.456 mA and V_ENABLE = 3.3 − 0.456 V = **2.84 V**, comfortably above the LT3074's 1.32 V max rising threshold. U6.4 is left driving a 2-node net with no load — an unloaded push-pull output, which is harmless. **Nothing floats.**
  - **J2 fitted:** U6 drives ENABLE against the 1k pullup. Low = ≪0.1 V (3.3 mA sink), high = ≈3.2 V. **Nothing floats.**
  - Note the 1k value of R18 is not arbitrary and should not be "optimised" upward: with Q1's 4k7 base path loading the node, R18 = 10k would give only 1.53 V at ENABLE, leaving ~0.2 V margin to the 1.32 V max threshold. If R18 is ever changed, move Q1's base to the U6 output side of J2 or raise R43 at the same time.

### F-LOGIC-3: With J2 un-fitted (the as-shipped default) the host has no way to switch the LDOs off at all
- **Severity:** Should-fix
- **Confidence:** High
- **Where:** J2, nets `ENABLE` and `CNTRL`
- **Evidence:** `nets.tsv`: `CNTRL 3 P1.4 R20.2 U6.2(:input)` and `Net-(J2-Pin_2) 2 J2.2 U6.4(:output)`. With no shunt on J2, U6's output reaches nothing; `ENABLE` is held at 2.84 V by R18 alone.
- **Why it matters:** The "bypass" is all-or-nothing. It does not merely bypass the *watchdog* — it bypasses the entire AND gate, so the host's `CNTRL` line on PMOD pin 4 is also disconnected. On a board straight from assembly, P1.4 does nothing and the two LT3074s are unconditionally enabled from the moment 3V3_PMOD appears. Anyone evaluating the enable/sequencing behaviour will conclude the CNTRL pin is broken. It also means the default board ships with its supervisor functionally absent, which partly masks F-LOGIC-1 but makes it much harder to notice.
- **Suggested fix:** No change to the topology is needed — the circuit is correct. Document it: add silkscreen next to J2 (see F-LOGIC-5) along the lines of `J2 OPEN = EN ALWAYS ON`, and make the as-shipped state an explicit decision. If the intended out-of-box behaviour is "watchdog active", ship with the shunt fitted and the JPs bridged.

### F-LOGIC-4: C28 (100 nF) on the open-drain /WDO net violates the 74LVC1G175 input slew-rate limit on /CLR by ~5×10⁴
- **Severity:** Should-fix
- **Confidence:** Medium
- **Where:** `Net-(U3-~{WDO})` = `C28.1 R17.2 U3.7(open_collector) U4.6(~{CLR}_6:input)`
- **Evidence:** R17 = 10k, C28 = 100n ⇒ τ = 1 ms. Rising from V_IL max (0.8 V) to V_IH min (2.0 V) at V_CC = 3.3 V takes τ·ln((3.3−0.8)/(3.3−2.0)) = **0.65 ms**, i.e. ≈545 µs/V. SN74LVC1G175 datasheet p.5, Recommended Operating Conditions: **Δt/Δv input transition rise or fall rate, V_CC = 3.3 V ± 0.3 V, max 10 ns/V** — and footnote (1) on p.4 points at TI SCBA004, *Implications of Slow or Floating CMOS Inputs*. The spec is in the Recommended Operating Conditions table and applies to all inputs, /CLR included.
- **Why it matters:** The MAX6373 asserts /WDO low for 100–300 ms (DS p.5, t_WDO for MAX6369/71/73). When it releases, U4's /CLR spends ~0.65 ms traversing the forbidden input band. During exactly that window the host is, by design, resuming its WDI strobing — and WDI is U4's **clock**. A clock edge arriving while /CLR is in the indeterminate band means the "/CLR inactive setup time" (spec'd at 0.5 ns, DS p.6 §6.6) is not met in any meaningful sense, so Q is indeterminate. Since Q directly gates the LT3074 enable, the observable symptom is a glitchy or non-repeatable recovery from a watchdog timeout — the hardest class of bug to chase on a demo board. SCBA004 also warns of input-stage crossover current (spec'd here at ΔI_CC 500 µA, DS p.5) and output oscillation during such a transition.
  Worth noting that C28's apparent secondary purpose — giving U4 a power-on reset so Q starts at 0 — is **already redundant**: R20 holds CNTRL low at power-up, so U6's output is low regardless of Q. The cap is not earning its slew-rate penalty.
- **Suggested fix:** Reduce C28 to 1 nF (τ = 10 µs, ~5.5 µs/V — still 3 orders over spec but the exposure window shrinks 100×), or better, delete C28 entirely and rely on R20's pulldown for the power-up state. If the slow clear is genuinely wanted, buffer the WDO net through a Schmitt-trigger inverter/buffer (e.g. 74LVC1G14 ×2 or 74LVC1G17) before U4.6 so U4 sees a fast edge.

### F-LOGIC-5: JP1/JP2/JP3 reference designators are hidden and the board carries zero free silkscreen text
- **Severity:** Should-fix
- **Confidence:** High
- **Where:** `LDO_MON_PMOD_Board_V1.kicad_pcb`, footprints JP1 (106.5, 107.7), JP2 (109.0, 107.7), JP3 (111.5, 107.7)
- **Evidence:** Parsing the PCB file: JP1, JP2 and JP3 all have `(property "Reference" …)` on `F.SilkS` with **`(hide yes)`**. J2's reference is visible. Separately, `grep -c 'gr_text' LDO_MON_PMOD_Board_V1.kicad_pcb` returns **0** — there is not a single free-text silkscreen string anywhere on the board.
- **Why it matters:** The MAX6373 cannot work until a human correctly solder-bridges all three jumpers (F-LOGIC-1). What that human will find on the board is three identical, unlabelled 3-pad patterns on 2.5 mm centres, with no refdes, no `0`/`1` or `GND`/`3V3` marking, and no indication of which end is which. Getting SET2 and SET0 swapped is a single mirrored mistake and silently selects a completely different timeout (e.g. `1,0,0` = 30 µs vs `0,0,1` = 3 s). There is also nothing on the board explaining J2's polarity of meaning. For a demo/evaluation board — which this is — the configuration straps being unmarked is a usability defect with a direct functional consequence.
- **Suggested fix:** Un-hide the JP1/JP2/JP3 references, and add `F.SilkS` text marking which pad is GND and which is 3V3 on each jumper (and ideally `SET0`/`SET1`/`SET2`), plus a short `WD BYPASS` / `EN` legend at J2. If there is no room, at minimum un-hide the refdes and put a polarity tick at the GND pad.

### F-LOGIC-6: A watchdog timeout is not latched — the LDOs re-enable on the next WDI edge
- **Severity:** Nice-to-have
- **Confidence:** High
- **Where:** U4 (74LVC1G175), `Net-(U3-~{WDO})` → U4.6, `WDI` → U4.1
- **Evidence:** U4.3 (D) is tied to `3V3_PMOD` (`nets.tsv`, 3V3_PMOD node list includes `U4.3(D_3:input)`), so every rising CLK edge loads a 1. /CLR is a 100–300 ms pulse, not a level (MAX6373 DS p.5 t_WDO).
- **Why it matters:** The design turns the LDOs off on a timeout, but the very next WDI rising edge after /WDO deasserts turns them straight back on. A host stuck in a loop that produces one WDI edge every few seconds would cycle the rails rather than keep them off. Whether that is wanted depends on intent: auto-recovery is often desirable for a demo, but it should be a deliberate choice, not an accident of the topology. Note the MAX6373's own "First Edge" startup modes (Table 1 rows `1,0,1` and `1,1,0`) interact with this — after each /WDO pulse the startup delay re-runs, so there is a grace period before the next possible timeout.
- **Suggested fix:** None required if auto-recovery is intended — but say so in the documentation. If a latching shutdown is wanted instead, drive U4.3 (D) from `CNTRL` rather than 3V3 so the host must explicitly re-arm, which costs nothing and makes the behaviour explicit.

### F-LOGIC-7: R19 = 1 kΩ is a heavy static load on the host's WDI pin
- **Severity:** Nice-to-have
- **Confidence:** High
- **Where:** `WDI` = `P1.10 R19.1 U3.1(WDI_1:input) U4.1(C_1:input)`; R19 = 1k to GND
- **Evidence:** MAX6373 DS p.6, pin 1: *"Connect WDI to ground with a **100kΩ (max)** resistor if not driven externally."* R19 at 1k is legal (it is well under the 100k ceiling) and correctly guarantees a defined level when nothing is plugged in.
- **Why it matters:** When the PMOD host drives WDI high it sinks a continuous 3.3 mA into R19, on every strobe, for the whole high time. That is a large fraction of what a conservatively-configured FPGA/MCU PMOD pin is budgeted for, and it is 100× more than this pin needs. The same observation applies to R18's 3.3 mA when U6 is holding ENABLE low with J2 fitted (see F-LOGIC-2 for why R18 cannot simply be raised on its own).
- **Suggested fix:** Change R19 to 10 kΩ (330 µA) or 100 kΩ. Both remain within the datasheet limit and keep the "undriven = low" guarantee. No other node depends on R19's value.

## 4. Explicitly clean results

These were checked against datasheets and came back correct; recording them so they are not re-reviewed:

- **The `125b2fa` fix itself is correct and complete.** The bypass works in both jumper states, and no node floats into a CMOS input in either state (F-LOGIC-2).
- **U4 (74LVC1G175): every pin accounted for, no floating input.** Pinout verified against DS p.3: 1 = CLK (← WDI), 2 = GND, 3 = D (← 3V3_PMOD, legal per the "unused inputs held at V_CC or GND" note on DS p.4), 4 = Q, 5 = V_CC, 6 = /CLR (← WDO net). The part has no OE pin.
- **U6 (74LVC1G08): every pin accounted for, no floating input.** Pinout verified against DS p.3 (DRL column): 1 = A (← U4.Q), 2 = B (← CNTRL, held low by R20 10k), 3 = GND, 4 = Y, 5 = V_CC.
- **The only open-collector pin in the design (U3.7 /WDO) has a correctly-valued pullup.** R17 = 10 kΩ to 3V3_PMOD; the MAX6373 datasheet p.9 states verbatim that "A 10kΩ pullup is sufficient in most applications". The MAX6373 (as opposed to the MAX6374) is correctly identified as the open-drain variant.
- **U3 pin 3 (N.C.) is correctly left with nothing attached**, as the datasheet demands ("Do not make any connection to this pin", p.6).
- **WDI is driven correctly** and has a legal undriven default (F-LOGIC-7 is about the resistor value, not correctness).
- **Every reset and enable net in the design has a defined state at power-up before anything is configured, except the three SET pins.** Audited from `nets.tsv`: CNTRL (R20 10k ↓), WDI (R19 1k ↓), U4.Q (R21 10k ↓), ENABLE (R18 1k ↑), DP_RST_N (R37 10k ↑, so the AD5272 comes out of reset), PAC_EN/U5 /PWRDN (R23 10k ↑, not powered down), SLOW (R24 10k ↑), GPIO (R25 10k ↑), U8 EN (R22 200k to BIAS with C51). R21 is strictly redundant — it is a pulldown on a push-pull output — but it is harmless and does give a defined level if U4 is left unpopulated.
- **No power-up lockout exists.** The watchdog cannot reset the thing that kicks it: WDI comes from the PMOD host on P1.10, powered from the host's own 3V3_PMOD rail, which also powers U3/U4/U6. The LT3074 outputs (OUT_1, OUT_2) go only to the sense network and the external load connector J3 — they power nothing in the control path. At power-on with J2 fitted, CNTRL is low (R20), so the rails start disabled and stay disabled until the host asserts CNTRL *and* has clocked a 1 into U4 with a WDI edge. That is the correct, safe order.
- **ENABLE levels have large margin at both ends** against the LT3074's 1.20/1.26/1.32 V rising threshold and 80 mV hysteresis, and 3.3 V is far inside the EN pin's −0.3 V to 6 V absolute maximum.
- **Decoupling placement for all three logic/supervisor parts meets the datasheet requirement.** MAX6373 p.9 asks for 0.1 µF within 0.2 in (5.08 mm): C29 (100n) is 2.36 mm from U3 on the same layer. U4 has C30 (100n) directly beneath it on B.Cu (0.0 mm offset); U6 has C31 (100n) at 2.39 mm.
- **No ERC or DRC item in the strict reports touches this subsystem** beyond the already-known `power_pin_not_driven` warning on U3.8.
