#!/usr/bin/env python3
"""05_plane_return_path.py -- reference-plane integrity check for the LDO_MON PMOD board.

Reads LDO_MON_PMOD_Board_V1.kicad_pcb, reconstructs every zone's *filled* polygon
set per copper layer, then for each routed track segment on a signal layer tests
whether the segment's footprint is continuously backed by the adjacent reference
plane. A segment whose centreline leaves the reference copper is a return-path
discontinuity (classic plane-split crossing).

Also reports: per-layer copper coverage, which nets own each inner plane, and the
number of disjoint islands each plane is broken into.

Requires: shapely.  Usage: python3 05_plane_return_path.py
"""
import sys, collections, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kicad_parse import parse_sexpr, find_all, get, val
from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.ops import unary_union

PCB = os.path.join(HERE, '..', '..', 'LDO_MON_PMOD_Board_V1', 'LDO_MON_PMOD_Board_V1.kicad_pcb')
root = parse_sexpr(open(PCB).read())[0]

# ---- board outline area
edge = []
for g in root:
    if isinstance(g, list) and g[0] in ('gr_line','gr_rect','gr_arc'):
        if val(g,'layer') == 'Edge.Cuts':
            edge.append(g)

# ---- filled polygons per (layer, net)
polys = collections.defaultdict(list)
for z in [n for n in root if isinstance(n,list) and n[0]=='zone']:
    net = val(z,'net')
    lg = get(z,'layers')
    deflay = lg[1] if lg else val(z,'layer')
    for fp in z:
        if isinstance(fp,list) and fp[0]=='filled_polygon':
            lay = val(fp,'layer') or deflay
            pts = [(float(p[1]),float(p[2])) for p in find_all(get(fp,'pts'),'xy')]
            if len(pts) > 2:
                polys[(lay,net)].append(pts)

layer_net_geom = {}
for (lay,net), ps in polys.items():
    gs = []
    for p in ps:
        g = Polygon(p)
        if not g.is_valid: g = g.buffer(0)
        gs.append(g)
    layer_net_geom[(lay,net)] = unary_union(gs)

print('=== Plane / zone copper per layer ===')
per_layer = collections.defaultdict(list)
for (lay,net), g in sorted(layer_net_geom.items()):
    n_islands = len(g.geoms) if isinstance(g, MultiPolygon) else 1
    per_layer[lay].append((net, g.area, n_islands))
for lay in ['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']:
    tot = sum(a for _,a,_ in per_layer.get(lay,[]))
    print(f'{lay:8s} zone copper {tot:8.1f} mm2  ' +
          ', '.join(f'{n}={a:.1f}mm2/{i}island(s)' for n,a,i in sorted(per_layer.get(lay,[]), key=lambda x:-x[1])))

# ---- tracks
segs = [n for n in root if isinstance(n,list) and n[0] in ('segment','arc')]
REF = {'F.Cu':'In1.Cu', 'B.Cu':'In4.Cu'}      # adjacent reference layer per signal layer
GNDREF = {}
for sig, ref in REF.items():
    GNDREF[sig] = layer_net_geom.get((ref,'GND'))

print('\n=== Return-path check: signal tracks vs adjacent GND plane ===')
bad = collections.defaultdict(lambda: [0,0.0,[]])
for s in segs:
    lay = val(s,'layer'); net = val(s,'net')
    if lay not in REF or net in ('GND',):
        continue
    ref = GNDREF[lay]
    if ref is None: continue
    st = get(s,'start'); en = get(s,'end')
    a = (float(st[1]),float(st[2])); b = (float(en[1]),float(en[2]))
    if a == b: continue
    line = LineString([a,b])
    outside = line.difference(ref)
    if outside.length > 0.05:          # ignore sliver/numerical
        k = (lay, net)
        bad[k][0] += 1
        bad[k][1] += outside.length
        bad[k][2].append((round(a[0],2),round(a[1],2),round(b[0],2),round(b[1],2),round(outside.length,2)))

for k in sorted(bad, key=lambda k:-bad[k][1]):
    n, L, ex = bad[k]
    print(f'{k[0]:6s} net {k[1]:22s} {n:3d} segment(s), {L:7.2f} mm not over {REF[k[0]]} GND')
    for e in sorted(ex, key=lambda e:-e[4])[:4]:
        print(f'          ({e[0]},{e[1]})->({e[2]},{e[3]})  {e[4]} mm unbacked')
if not bad:
    print('  none -- every signal segment is fully backed by its adjacent GND plane')

# ---- inner-layer routing carved into planes
print('\n=== Tracks routed ON plane layers (these cut the plane) ===')
cut = collections.defaultdict(lambda:[0,0.0])
for s in segs:
    lay = val(s,'layer')
    if not lay.startswith('In'): continue
    st=get(s,'start'); en=get(s,'end')
    L = math.dist((float(st[1]),float(st[2])),(float(en[1]),float(en[2])))
    cut[(lay,val(s,'net'),val(s,'width'))][0]+=1
    cut[(lay,val(s,'net'),val(s,'width'))][1]+=L
for k in sorted(cut):
    print(f'  {k[0]} net {k[1]:18s} w={k[2]}mm  n={cut[k][0]:3d}  len={cut[k][1]:6.2f}mm')
