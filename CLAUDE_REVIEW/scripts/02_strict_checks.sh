#!/usr/bin/env bash
# Wave 0b: re-run ERC/DRC with ALL suppressed rules re-enabled and all
# exclusions cleared, to reveal what the project's relaxed severities hide.
# Works on a throwaway copy of the project -- the real design is never touched.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RAW="$ROOT/CLAUDE_REVIEW/raw"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cp "$ROOT/LDO_MON_PMOD_Board_V1/"*.kicad_{pro,sch,pcb} "$TMP/"

python3 - "$TMP/LDO_MON_PMOD_Board_V1.kicad_pro" <<'PY'
import json,sys
p=sys.argv[1]; d=json.load(open(p))
# promote every ignored/warning rule to at least warning, and clear exclusions
for sev in (d.setdefault('erc',{}).setdefault('rule_severities',{}),
            d.setdefault('board',{}).setdefault('design_settings',{}).setdefault('rule_severities',{})):
    for k,v in list(sev.items()):
        if v == 'ignore': sev[k] = 'warning'
d['erc']['erc_exclusions']=[]
d['board']['design_settings']['drc_exclusions']=[]
json.dump(d,open(p,'w'),indent=2)
PY

kicad-cli sch erc --severity-all --units mm --format report -o "$RAW/erc_strict.rpt" "$TMP/LDO_MON_PMOD_Board_V1.kicad_sch"
kicad-cli sch erc --severity-all --units mm --format json   -o "$RAW/erc_strict.json" "$TMP/LDO_MON_PMOD_Board_V1.kicad_sch"
kicad-cli pcb drc --severity-all --units mm --schematic-parity --format report -o "$RAW/drc_strict.rpt" "$TMP/LDO_MON_PMOD_Board_V1.kicad_pcb"
kicad-cli pcb drc --severity-all --units mm --schematic-parity --format json   -o "$RAW/drc_strict.json" "$TMP/LDO_MON_PMOD_Board_V1.kicad_pcb"
