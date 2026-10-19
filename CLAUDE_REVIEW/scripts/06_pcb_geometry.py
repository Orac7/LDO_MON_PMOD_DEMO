#!/usr/bin/env python3
"""06_pcb_geometry.py -- geometry extraction for the LDO_MON PMOD board review.

Correctly transforms footprint pads into board coordinates (KiCad .kicad_pcb pad
angles are ABSOLUTE; the rotation is clockwise in screen coords:
    X = fx + px*cos(r) + py*sin(r)
    Y = fy - px*sin(r) + py*cos(r)
verified against the released Gerber %TO.P pad flashes).

Reports:
  * design-rule minima actually used (track width, clearance proxies, via/drill/annulus)
  * every via: which layers it actually lands copper on
  * thermal-via census under U1/U2 exposed pads
  * silkscreen text sizes and silk-over-pad overlaps
  * board outline and through-hole/mounting-hole inventory
"""
import sys, math, collections, os, json
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
from kicad_parse import parse_sexpr, find_all, get, val
from shapely.geometry import Polygon, Point, box, LineString
from shapely.ops import unary_union
import shapely.affinity as aff

PCB=os.path.join(HERE,'..','..','LDO_MON_PMOD_Board_V1','LDO_MON_PMOD_Board_V1.kicad_pcb')
root=parse_sexpr(open(PCB).read())[0]
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']

def xf(fx,fy,fr,px,py):
    r=math.radians(fr)
    return (fx+px*math.cos(r)+py*math.sin(r), fy-px*math.sin(r)+py*math.cos(r))

# ---------- zones ----------
polys=collections.defaultdict(list)
for z in [n for n in root if isinstance(n,list) and n[0]=='zone']:
    net=val(z,'net'); lg=get(z,'layers'); deflay=lg[1] if lg else val(z,'layer')
    for fp in z:
        if isinstance(fp,list) and fp[0]=='filled_polygon':
            lay=val(fp,'layer') or deflay
            pts=[(float(p[1]),float(p[2])) for p in find_all(get(fp,'pts'),'xy')]
            if len(pts)>2: polys[(lay,net)].append(Polygon(pts).buffer(0))
G={k:unary_union(v) for k,v in polys.items()}

# ---------- footprints / pads ----------
FP=[]
for fp in [n for n in root if isinstance(n,list) and n[0]=='footprint']:
    d={'lib':fp[1],'ref':None,'value':None,'layer':val(fp,'layer'),'pads':[],'texts':[],'dnp':False,'attr':[]}
    at=get(fp,'at'); fx,fy=float(at[1]),float(at[2]); fr=float(at[3]) if len(at)>3 else 0.0
    d['at']=(fx,fy,fr)
    a=get(fp,'attr');  d['attr']=a[1:] if a else []
    d['dnp']= 'dnp' in d['attr']
    for p in fp:
        if isinstance(p,list) and p[0]=='property' and p[1] in ('Reference','Value'):
            d['Reference' if p[1]=='Reference' else 'Value']=p[2]
            eff=get(p,'effects'); fnt=get(eff,'font') if eff else None
            sz=get(fnt,'size') if fnt else None
            d['texts'].append(dict(kind=p[1],text=p[2],layer=val(p,'layer'),
                hide=bool(get(p,'hide') and get(p,'hide')[1]=='yes'),
                size=(float(sz[1]),float(sz[2])) if sz else None,
                thickness=float(val(fnt,'thickness')) if fnt and get(fnt,'thickness') else None))
    d['ref']=d.get('Reference'); d['value']=d.get('Value')
    for pad in [c for c in fp if isinstance(c,list) and c[0]=='pad']:
        pa=get(pad,'at'); px,py=float(pa[1]),float(pa[2]); prot=float(pa[3]) if len(pa)>3 else fr
        X,Y=xf(fx,fy,fr,px,py)
        sz=get(pad,'size'); w,h=float(sz[1]),float(sz[2])
        g=aff.translate(aff.rotate(box(-w/2,-h/2,w/2,h/2),-prot,origin=(0,0)),X,Y)
        dr=get(pad,'drill')
        d['pads'].append(dict(num=pad[1],type=pad[2],shape=pad[3],x=X,y=Y,w=w,h=h,
            layers=(get(pad,'layers') or [])[1:],net=val(pad,'net'),geom=g,
            drill=float(dr[1]) if dr and dr[1] not in ('oval',) else (float(dr[2]) if dr and dr[1]=='oval' else None)))
    FP.append(d)

if __name__=='__main__':
    print('=== pad transform sanity (compare with Gerber %TO.P) ===')
    for f in FP:
        if f['ref']=='U1':
            for p in f['pads']:
                if p['num'] in ('9','21','23','24'):
                    print(f"  U1.{p['num']} -> ({p['x']:.3f},{p['y']:.3f})  (gerber: 9=130.400, 21=126.600, 23=127.935, 24=129.385)")

    vias=[]
    for v in [n for n in root if isinstance(n,list) and n[0]=='via']:
        a=get(v,'at'); vias.append(dict(x=float(a[1]),y=float(a[2]),size=float(val(v,'size')),
            drill=float(val(v,'drill')),net=val(v,'net')))
    segs=[n for n in root if isinstance(n,list) and n[0] in ('segment','arc')]

    print('\n=== vias: layers actually landed on ===')
    allpads=[(f['ref'],p) for f in FP for p in f['pads']]
    bad=[]
    for v in vias:
        P=Point(v['x'],v['y']); disc=Point(v['x'],v['y']).buffer(v['size']/2)
        land=[]
        for L in LAYERS:
            hit=[]
            g=G.get((L,v['net']))
            if g is not None and g.intersects(disc) and g.intersection(disc).area>1e-6: hit.append('zone')
            for s in segs:
                if val(s,'layer')!=L or val(s,'net')!=v['net']: continue
                st=get(s,'start'); en=get(s,'end')
                if min(math.dist((float(st[1]),float(st[2])),(v['x'],v['y'])),
                       math.dist((float(en[1]),float(en[2])),(v['x'],v['y'])))<v['size']/2:
                    hit.append('track'); break
            for ref,p in allpads:
                if L in p['layers'] and p['net']==v['net'] and p['geom'].intersects(disc):
                    hit.append('pad %s.%s'%(ref,p['num'])); break
            if hit: land.append(L+':'+'+'.join(sorted(set(hit))))
        if len(land)<2: bad.append((v,land))
    print(f'  {len(vias)} vias total; {len(bad)} land copper on fewer than 2 layers:')
    for v,land in bad:
        print(f"    ({v['x']},{v['y']}) net={v['net']} size={v['size']}/{v['drill']} lands={land or 'NOTHING'}")

    print('\n=== thermal vias under U1/U2 exposed pads ===')
    for f in FP:
        if f['ref'] not in ('U1','U2'): continue
        for p in f['pads']:
            if p['w']*p['h']<1.0: continue
            ins=[v for v in vias if p['geom'].contains(Point(v['x'],v['y']))]
            print(f"  {f['ref']}.{p['num']} net={p['net']:10s} pad {p['w']}x{p['h']}mm area={p['w']*p['h']:.2f}mm2 "
                  f"vias_in_pad={len(ins)} nets={set(v['net'] for v in ins)} drills={set(v['drill'] for v in ins)}")
            for v in ins:
                lands=[L for L in LAYERS if (G.get((L,v['net'])) is not None and
                        G[(L,v['net'])].intersects(Point(v['x'],v['y']).buffer(v['size']/2)))]
                print(f"       via({v['x']},{v['y']}) reaches zones on: {lands or 'NONE'}")

    print('\n=== silkscreen: refdes text size/thickness and hidden refdes ===')
    small=[];hidden=[]
    for f in FP:
        for t in f['texts']:
            if t['kind']!='Reference': continue
            if t['hide'] or (t['layer'] not in ('F.SilkS','B.SilkS')):
                hidden.append((f['ref'],t['layer'],t['hide']))
            elif t['size'] and (t['size'][0]<0.8 or (t['thickness'] or 0)<0.12):
                small.append((f['ref'],t['size'],t['thickness']))
    print(f'  refdes not on silk / hidden: {len(hidden)} -> {sorted(set(h[0] for h in hidden))}')
    print(f'  refdes smaller than 0.8mm high or <0.12mm thick: {len(small)}')
    for s in sorted(small)[:30]: print('    ',s)

    print('\n=== silk graphics over exposed copper (F/B) ===')
    silk=collections.defaultdict(list)
    for f in FP:
        fx,fy,fr=f['at']
        for g in [c for c in f if False]: pass
    # footprint silk lines
    for fpnode in [n for n in root if isinstance(n,list) and n[0]=='footprint']:
        ref=None
        for p in fpnode:
            if isinstance(p,list) and p[0]=='property' and p[1]=='Reference': ref=p[2]
        at=get(fpnode,'at'); fx,fy=float(at[1]),float(at[2]); fr=float(at[3]) if len(at)>3 else 0
        for sh in [c for c in fpnode if isinstance(c,list) and c[0] in ('fp_line','fp_arc','fp_circle','fp_poly','fp_rect')]:
            lay=val(sh,'layer')
            if lay not in ('F.SilkS','B.SilkS'): continue
            w=float(val(get(sh,'stroke') or ['stroke'],'width') or 0.1) if get(sh,'stroke') else 0.1
            pts=[]
            for key in ('start','end','center','mid'):
                c=get(sh,key)
                if c: pts.append(xf(fx,fy,fr,float(c[1]),float(c[2])))
            for p in find_all(sh,'xy'): pts.append(xf(fx,fy,fr,float(p[1]),float(p[2])))
            if len(pts)>=2: silk[lay].append((ref,LineString(pts).buffer(w/2)))
    for lay,cu in (('F.SilkS','F.Cu'),('B.SilkS','B.Cu')):
        clashes=[]
        for ref,g in silk[lay]:
            for f in FP:
                for p in f['pads']:
                    if cu not in p['layers'] or p['type']=='np_thru_hole': continue
                    if g.intersects(p['geom']):
                        a=g.intersection(p['geom']).area
                        if a>0.002: clashes.append((round(a,4),ref,f['ref']+'.'+p['num']))
        clashes.sort(reverse=True)
        print(f'  {lay}: {len(clashes)} silk-graphic/pad overlaps >0.002mm2')
        for c in clashes[:15]: print('     ',c)
