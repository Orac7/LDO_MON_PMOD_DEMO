#!/usr/bin/env python3
"""Wave 0c: build the ground-truth tables every later stage reads.
Writes components.tsv, nets.tsv and net_summary.md into CLAUDE_REVIEW/raw/."""
import os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicad_parse import load, find_all, get, val

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RAW  = os.path.join(ROOT, 'CLAUDE_REVIEW', 'raw')
nl   = load(os.path.join(RAW, 'netlist.net'))[0]

# ---- components -------------------------------------------------------
comps = {}
for c in find_all(get(nl, 'components') or [], 'comp'):
    ref = val(c, 'ref')
    if not ref: continue
    fields = {}
    for f in find_all(c, 'field'):
        name = val(f, 'name')
        if name and len(f) > 2: fields[name] = f[-1]
    comps[ref] = dict(
        ref=ref, value=val(c, 'value', default=''),
        footprint=val(c, 'footprint', default=''),
        lib=(val(get(c,'libsource') or [], 'part', default='') if get(c,'libsource') else ''),
        desc=val(c, 'description', default=''), **fields)

# ---- nets -------------------------------------------------------------
nets = {}
for n in find_all(get(nl, 'nets') or [], 'net'):
    name = val(n, 'name')
    if name is None: continue
    nodes = []
    for nd in find_all(n, 'node'):
        nodes.append(dict(ref=val(nd,'ref'), pin=val(nd,'pin'),
                          fn=val(nd,'pinfunction',default=''),
                          ptype=val(nd,'pintype',default='')))
    nets[name] = nodes

# ---- write ------------------------------------------------------------
keys = ['ref','value','footprint','lib','desc','Manufacturer','MPN','LCSC','Datasheet','DNP']
with open(os.path.join(RAW,'components.tsv'),'w') as f:
    f.write('\t'.join(keys)+'\n')
    for ref in sorted(comps, key=lambda r:(r.rstrip('0123456789'), int(''.join(filter(str.isdigit,r)) or 0))):
        f.write('\t'.join(str(comps[ref].get(k,'')).replace('\t',' ') for k in keys)+'\n')

with open(os.path.join(RAW,'nets.tsv'),'w') as f:
    f.write('net\tn_nodes\tnodes\n')
    for name in sorted(nets):
        nd = nets[name]
        f.write(f"{name}\t{len(nd)}\t" +
                ' '.join(f"{x['ref']}.{x['pin']}({x['fn']}:{x['ptype']})" for x in nd) + '\n')

# ---- quick structural flags ------------------------------------------
out = []
out.append(f"Components: {len(comps)}   Nets: {len(nets)}\n")
single = {k:v for k,v in nets.items() if len(v)==1}
out.append(f"## Single-node nets ({len(single)})\n")
for k,v in sorted(single.items()):
    out.append(f"- `{k}` -> {v[0]['ref']}.{v[0]['pin']} ({v[0]['fn']}, {v[0]['ptype']})")
drv = collections.defaultdict(list)
for k,v in nets.items():
    outs = [x for x in v if x['ptype'] in ('output','power_out')]
    if len(outs) > 1: drv[k] = outs
out.append(f"\n## Nets with >1 driver ({len(drv)})\n")
for k,v in sorted(drv.items()):
    out.append(f"- `{k}` <- " + ', '.join(f"{x['ref']}.{x['pin']}({x['ptype']})" for x in v))
pt = collections.Counter(x['ptype'] for v in nets.values() for x in v)
out.append("\n## Pin-type census\n" + '\n'.join(f"- {k}: {n}" for k,n in pt.most_common()))
open(os.path.join(RAW,'net_summary.md'),'w').write('\n'.join(out)+'\n')
print('\n'.join(out))
