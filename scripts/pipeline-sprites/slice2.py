from PIL import Image
import numpy as np
im=Image.open(r"C:\Users\Admin0011\Proyectos\mods-claude\emilia-mascota\arte\Emilia Claude pixel de estados y emociones.png").convert("RGB")
a=np.array(im).astype(int)
bg=np.array([245,241,251])
mask=np.abs(a-bg).sum(axis=2)>40
rowsb=[(45,331),(400,657),(728,992)]
names=["nueva","pensando","responde","leyendo","escribiendo","necesita","falla","para","terminado","baile","guardia_hula","duerme"]
out=[]
i=0
for (y0,y1) in rowsb:
    cols=mask[y0:y1].sum(axis=0)
    bands=[];inb=False;gap=0
    for x,v in enumerate(cols):
        if v>0:
            if not inb: s=x;inb=True
            gap=0;e=x
        elif inb:
            gap+=1
            if gap>25: bands.append((s,e+1));inb=False
    if inb: bands.append((s,e+1))
    print(y0,bands)
    for (x0,x1) in bands:
        sub=mask[y0:y1,x0:x1]
        ys=np.where(sub.any(axis=1))[0]; xs=np.where(sub.any(axis=0))[0]
        box=(x0+xs[0],y0+ys[0],x0+xs[-1]+1,y0+ys[-1]+1)
        out.append((names[i],box)); i+=1
for n,b in out: print(n,b,b[2]-b[0],b[3]-b[1])
import json;json.dump(out,open("boxes.json","w"))
