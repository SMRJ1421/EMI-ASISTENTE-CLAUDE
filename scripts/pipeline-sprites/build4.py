from PIL import Image
import numpy as np, json
names=["nueva","pensando","responde","leyendo","escribiendo","necesita","falla","para","terminado","baile","hula","duerme"]
F=np.load("frames_L.npy",allow_pickle=True).item()
GH,GW=F["nueva"][0][1].shape
SIZES={"L":(GW,GH),"S":(20,34),"X":(14,24)}
def resize(rgb,al,w,h):
    r=rgb.astype(float)
    sat=(r.max(axis=2)-r.min(axis=2)>110)&(al>0)
    dark=(r.sum(axis=2)<170)&(al>0)
    pm=r*al[...,None]
    def box(arr): return np.array(Image.fromarray(arr.astype(np.float32),"F").resize((w,h),Image.BOX))
    A=box(al);D=box(dark.astype(float));S=box(sat.astype(float))
    ch=[box(pm[...,i]) for i in range(3)]
    sch=[box((r[...,i]*sat)) for i in range(3)]
    out=np.zeros((h,w,3));mask=A>=0.40
    for i in range(3):
        out[...,i]=np.where(mask,ch[i]/np.maximum(A,1e-6),0)
        sat_col=sch[i]/np.maximum(S,1e-6)
        out[...,i]=np.where(mask&(S>=0.3),sat_col,out[...,i])
    out[mask&(D>=0.45)&(S<0.3)]=(30,22,38)
    return out.clip(0,255).astype(np.uint8),mask.astype(float)
frames={}
allc=[];w8=[]
for n in names:
    for sz,(w,h) in SIZES.items():
        res=[]
        for rgb,al in F[n]:
            res.append((rgb,al) if sz=="L" else resize(rgb,al,w,h))
        frames[(n,sz)]=res
        for rgb,al in res:
            px=rgb[al>0]
            allc.append(px)
            sat=(px.max(axis=1).astype(int)-px.min(axis=1).astype(int)>110)
            if sat.any(): allc.extend([px[sat]]*6)
cols=np.concatenate(allc)
strip=Image.fromarray(cols.reshape(1,-1,3).astype(np.uint8),"RGB")
q=strip.quantize(colors=60,method=Image.MEDIANCUT,dither=Image.NONE)
pal=np.array(q.getpalette()[:60*3]).reshape(-1,3)
print("palette",len(pal))
def idx(rgb):
    d=((rgb[...,None,:].astype(int)-pal[None,None,:,:])**2).sum(-1)
    return d.argmin(-1)
CH_="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
out={"paleta":["#%02x%02x%02x"%tuple(int(v) for v in c) for c in pal],"sprites":{},"sizes":SIZES}
for n in names:
    out["sprites"][n]={}
    for sz in SIZES:
        fl=[]
        for rgb,al in frames[(n,sz)]:
            ix=idx(rgb)
            fl.append(["".join(CH_[ix[y,x]] if al[y,x]>0 else "." for x in range(al.shape[1])) for y in range(al.shape[0])])
        out["sprites"][n][sz]=fl
json.dump(out,open("sprites3.json","w"))
print("json bytes",len(json.dumps(out)),SIZES)
def render(sz,scale,fn):
    w,h=SIZES[sz]
    sheet=Image.new("RGB",(w*scale*8,h*scale*6),(245,230,253))
    for k,n in enumerate(names):
        for f,rows in enumerate(out["sprites"][n][sz]):
            arr=np.zeros((h,w,4),np.uint8)
            for y,r in enumerate(rows):
                for x,c in enumerate(r):
                    if c!=".": arr[y,x,:3]=pal[CH_.index(c)];arr[y,x,3]=255
            im=Image.fromarray(arr,"RGBA").resize((w*scale,h*scale),Image.NEAREST)
            sheet.paste(im,((((k%2)*4)+f)*w*scale,(k//2)*h*scale),im)
    sheet.save(fn)
render("S",6,"prev4_S.png");render("X",8,"prev4_X.png");render("L",5,"prev4_L.png")
