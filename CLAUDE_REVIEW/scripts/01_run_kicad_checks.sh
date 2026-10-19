#!/usr/bin/env bash
# Wave 0: authoritative tool-driven checks via kicad-cli.
# Produces ERC, DRC (with schematic parity), netlist and BOM into CLAUDE_REVIEW/raw/.
# Re-runnable: overwrites previous output. Exit code is always 0; violations are
# reported in the artefacts, not via exit status.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJ="$ROOT/LDO_MON_PMOD_Board_V1"
SCH="$PROJ/LDO_MON_PMOD_Board_V1.kicad_sch"
PCB="$PROJ/LDO_MON_PMOD_Board_V1.kicad_pcb"
RAW="$ROOT/CLAUDE_REVIEW/raw"
mkdir -p "$RAW"

run() { echo "=== $* ==="; "$@"; echo "  -> exit $?"; }

run kicad-cli sch erc --severity-all --units mm --format json   -o "$RAW/erc.json"    "$SCH"
run kicad-cli sch erc --severity-all --units mm --format report -o "$RAW/erc.rpt"     "$SCH"
run kicad-cli sch export netlist --format kicadsexpr            -o "$RAW/netlist.net" "$SCH"
run kicad-cli sch export bom                                    -o "$RAW/bom.csv"     "$SCH"
run kicad-cli pcb drc --severity-all --units mm --schematic-parity --format json   -o "$RAW/drc.json" "$PCB"
run kicad-cli pcb drc --severity-all --units mm --schematic-parity --format report -o "$RAW/drc.rpt"  "$PCB"

echo "=== artefacts ==="
ls -la "$RAW"
