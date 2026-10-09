from PIL import Image
import numpy as np, json

def label(mask):
    lab=np.zeros(mask.shape,int);n=0
    H,W=mask.shape
    for y in range(H):
        for x in range(W):
            if mask[y,x] and not lab[y,x]:
                n+=1;st=[(y,x)];lab[y,x]=n
                while st:
                    cy,cx=st.pop()
                    for dy in(-1,0,1):
                        for dx in(-1,0,1):
                            ny,nx=cy+dy,cx+dx
                            if 0<=ny<H and 0<=nx<W and mask[ny,nx] and not lab[ny,nx]:
                                lab[ny,nx]=n;st.append((ny,nx))
    return lab,n
names=["nueva","pensando","responde","leyendo","escribiendo","necesita","falla","para","terminado","baile","hula","duerme"]
S=np.load("sprites_L.npy",allow_pickle=True).item()
CW,CH=40,46
def canvas(rgb,al):
    h,w=al.shape
    R=np.zeros((CH,CW,3),np.uint8);Al=np.zeros((CH,CW))
    ox=(CW-w)//2; oy=CH-h-1   # 1 row margin at bottom
    R[oy:oy+h,ox:ox+w]=rgb; Al[oy:oy+h,ox:ox+w]=al
    return R,Al
L={n:canvas(*S[n]) for n in names}
def blink(rgb,al):
    r=rgb.astype(int)
    blue=(al>0)&(r[...,2]>150)&(r[...,2]>r[...,0]+35)&(r[...,2]>r[...,1]+10)
    lab,n=label(blue)
    rows=np.where(al.any(axis=1))[0]; top,bot=rows[0],rows[-1]
    comps=[]
    for k in range(1,n+1):
        ys,xs=np.where(lab==k)
        if not(2<=len(ys)<=16): continue
        if ys.max()>31 or ys.min()<24: continue
        comps.append((k,ys,xs))
    keep=[]
    for k,ys,xs in comps:
        for k2,ys2,xs2 in comps:
            if k2!=k and abs(ys.mean()-ys2.mean())<=2.5 and 3<=abs(xs.mean()-xs2.mean())<=16:
                keep.append((k,ys,xs));break
    out=rgb.copy();em=np.zeros(al.shape,bool)
    for k,ys,xs in keep:
        em[ys,xs]=True
        for y,x in zip(ys,xs):
            out[y,x]=(120,88,160) if y==ys.max() else (252,232,228)
    return out,len(keep),em
def flip(rgb,al): return rgb[:,::-1],al[:,::-1]
alts={}
EYE={}
for n in names:
    rgb,al=L[n]
    if n in("terminado","baile"):
        r2,a2=flip(rgb,al); alts[n]=("flip",r2,a2)
    else:
        b,c,em=blink(rgb,al)
        if c>=2: alts[n]=("blink",b,al); EYE[n]=em
print({n:alts[n][0] for n in alts})
def resize(rgb,al,w,h,eye=None):
    a=al[...,None]
    pm=(rgb*a)
    im=Image.fromarray(np.dstack([pm,al*255]).astype(np.float32),"RGBA") if False else None
    # manual box resize via PIL per channel (mode F)
    chans=[np.array(Image.fromarray(pm[...,i].astype(np.float32),"F").resize((w,h),Image.BOX)) for i in range(3)]
    A=np.array(Image.fromarray(al.astype(np.float32),"F").resize((w,h),Image.BOX))
    out=np.zeros((h,w,3));mask=A>=0.45
    for i in range(3): out[...,i]=np.where(mask,chans[i]/np.maximum(A,1e-6),0)
    out=out.clip(0,255).astype(np.uint8)
    if eye is not None and eye.any():
        E=np.array(Image.fromarray(eye.astype(np.float32),"F").resize((w,h),Image.BOX))
        force=(E>0.12)&mask
        out[force]=(70,150,235)
    return out,mask.astype(float)
SIZES={"L":(40,46),"S":(20,24),"X":(14,16)}
frames={} # (n,size)->[base,alt?]
allcols=[]
for n in names:
    fl=[L[n]]
    if n in alts: fl.append((alts[n][1],alts[n][2]))
    for sz,(w,h) in SIZES.items():
        res=[]
        for k,(rgb,al) in enumerate(fl):
            res.append((rgb,al) if sz=="L" else resize(rgb,al,w,h,EYE.get(n) if k==0 else None))
        frames[(n,sz)]=res
        for rgb,al in res: allcols.append(rgb[al>0])
cols=np.concatenate(allcols)
strip=Image.fromarray(cols.reshape(1,-1,3).astype(np.uint8),'RGB')
q=strip.quantize(colors=48,method=Image.MEDIANCUT,dither=Image.NONE)
pal=np.array(q.getpalette()[:48*3]).reshape(-1,3)
# ensure a near-black outline entry exists
pal=np.vstack([pal,[[70,150,235],[165,210,245]]]);print(len(pal))
def idx(rgb):
    d=((rgb[...,None,:].astype(int)-pal[None,None,:,:])**2).sum(-1)
    return d.argmin(-1)
CH_="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
out={"paleta":["#%02x%02x%02x"%tuple(c) for c in pal],"sprites":{}}
for n in names:
    out["sprites"][n]={}
    for sz in SIZES:
        fl=[]
        for rgb,al in frames[(n,sz)]:
            ix=idx(rgb)
            rows=["".join(CH_[ix[y,x]] if al[y,x]>0 else "." for x in range(al.shape[1])) for y in range(al.shape[0])]
            fl.append(rows)
        out["sprites"][n][sz]=fl
json.dump(out,open("sprites.json","w"))
print("json bytes",len(json.dumps(out)))
# previews
def render(sz,scale):
    w,h=SIZES[sz]
    sheet=Image.new("RGB",(w*scale*6,(h*scale)*4),(255,255,255))
    k=0
    for n in names:
        for f,rows in enumerate(out["sprites"][n][sz]):
            arr=np.zeros((h,w,3),np.uint8)+255
            for y,r in enumerate(rows):
                for x,c in enumerate(r):
                    if c!=".": arr[y,x]=pal[CH_.index(c)]
            im=Image.fromarray(arr).resize((w*scale,h*scale),Image.NEAREST)
            sheet.paste(im,((k%6)*w*scale,(k//6)*h*scale)); k+=1
    sheet.save(f"prev_{sz}.png")
render("S",7);render("X",9)
