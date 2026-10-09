from PIL import Image
import numpy as np
SRC=r"C:\Users\Admin0011\Proyectos\mods-claude\emilia-mascota\arte\Emilia Claude pixel de estados y emociones.png"
im=Image.open(SRC).convert("RGB"); A=np.array(im).astype(int)
BG=np.array([245,241,251])
names=["nueva","pensando","responde","leyendo","escribiendo","necesita","falla","para","terminado","baile","hula","duerme"]
boxes={"nueva":(120,112,283,326),"pensando":(474,45,675,330),"responde":(815,51,981,331),"leyendo":(1128,155,1378,324),
"escribiendo":(63,472,343,648),"necesita":(488,400,651,656),"falla":(816,425,1006,657),"para":(1177,446,1366,656),
"terminado":(68,728,335,992),"baile":(452,758,698,990),"hula":(801,758,1027,990),"duerme":(1142,770,1385,987)}
K=7
sprites={}
for n,(x0,y0,x1,y1) in boxes.items():
    crop=A[y0:y1,x0:x1]
    h,w=crop.shape[:2]
    H=(h+K-1)//K; W=(w+K-1)//K
    rgb=np.zeros((H,W,3));al=np.zeros((H,W))
    for j in range(H):
        for i in range(W):
            blk=crop[j*K:(j+1)*K,i*K:(i+1)*K].reshape(-1,3)
            fg=np.abs(blk-BG).sum(axis=1)>40
            if fg.mean()>=0.5:
                al[j,i]=1
                # dominant color: median of fg pixels
                rgb[j,i]=np.median(blk[fg],axis=0)
    sprites[n]=(rgb.astype(np.uint8),al)
    print(n,W,H)
# contact sheet
CW=max(s[1].shape[1] for s in sprites.values());CH=max(s[1].shape[0] for s in sprites.values())
print("canvas",CW,CH)
sheet=Image.new("RGBA",(CW*4*4,CH*3*4),(255,255,255,255))
for idx,n in enumerate(names):
    rgb,al=sprites[n]
    t=np.dstack([rgb,(al*255).astype(np.uint8)])
    im2=Image.fromarray(t,"RGBA").resize((rgb.shape[1]*4,rgb.shape[0]*4),Image.NEAREST)
    sheet.alpha_composite(im2,((idx%4)*CW*4,(idx//4)*CH*4))
sheet.save("contact_L.png")
np.save("sprites_L.npy",{n:(sprites[n][0],sprites[n][1]) for n in names},allow_pickle=True)
