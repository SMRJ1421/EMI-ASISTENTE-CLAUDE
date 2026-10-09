import json, re
TS = r"C:/Users/Admin0011/Proyectos/mods-claude/emilia-mascota/mod/hooks/sprites.ts"
ts = open(TS, encoding="utf-8").read()
def unrle(t):
    o=[];i=0
    while i<len(t):
        if t[i]=="§": o.append(t[i+2]*"0123456789abcdefghijklmnopqrstuvwxyz".index(t[i+1])); i+=3
        else: o.append(t[i]); i+=1
    return "".join(o)
print("tamaño | celdas/fotograma | glifos ▀ (actual: 100%) | glifos ▀ (nuevo) | pares de color máx. actual -> nuevo")
for t in ("S","N","M","L","XL"):
    b=re.search(rf"  {t}: \{{\n    ancho: (\d+),\n    alto: (\d+),\n    paleta: (\[.*?\]),\n    estados: \{{\n(.*?)\n    \}},\n  \}},", ts, re.S)
    w,h=int(b.group(1)),int(b.group(2)); pal=json.loads(b.group(3))
    tot=0; dif=0; mx1=0; mx2=0
    for m in re.finditer(r"      (\w+): (\[.*?\]),(?:\n|$)", b.group(4)):
        for f in json.loads(m.group(2)):
            rows=[unrle(r) for r in f.split("/")]
            p1=set(); p2=set(); d=0
            for r in range(0,h,2):
                for x in range(w):
                    a=rows[r][x]; c=rows[r+1][x]
                    ca=pal[0] if False else a  # comparar por carácter de paleta; '.' = tarjeta
                    same = (a==c)
                    p1.add((a,c))
                    if same: p2.add(("sp",c))
                    else: p2.add((a,c)); d+=1
                    tot+=1
            dif+=d; mx1=max(mx1,len(p1)); mx2=max(mx2,len(p2))
    print(f"{t:>2} {w}x{h} | {w*h//2} | 100% | {dif/tot*100:.1f}% | {mx1} -> {mx2}")
