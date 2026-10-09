from PIL import Image
import numpy as np, sys, json
im=Image.open(r"C:\Users\Admin0011\Proyectos\mods-claude\emilia-mascota\arte\Emilia Claude pixel de estados y emociones.png").convert("RGB")
a=np.array(im).astype(int)
print(im.size)
bg=a[5,5]; print("bg",bg, a[1080,1440])
# non-background mask
d=np.abs(a-bg).sum(axis=2)
mask=d>40
H,W=mask.shape
# label text is dark gray/black thin text; sprites have black outline too. find row bands via projection
rows=mask.sum(axis=1)
bands=[];inb=False
for y,v in enumerate(rows):
    if v>0 and not inb: s=y;inb=True
    if v==0 and inb:
        if y-s>3: bands.append((s,y))
        inb=False
print("row bands",bands)
