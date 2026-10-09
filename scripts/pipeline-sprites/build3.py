from PIL import Image
import numpy as np, collections, json
from collections import deque
SRC=r"C:\Users\Admin0011\Downloads\animacion de Emilia pixel de estados.png"
A=np.array(Image.open(SRC).convert("RGB")).astype(int)
names=["nueva","pensando","responde","leyendo","escribiendo","necesita","falla","para","terminado","baile","hula","duerme"]
cols=[(15,473),(490,955),(975,1435)]
rows=[(30,262),(283,515),(538,777),(795,1043)]
K=4
def flood_bg(win,bg,tol=28):
    cand=np.abs(win-bg).sum(axis=2)<=tol
    H,W=cand.shape
    seen=np.zeros((H,W),bool);dq=deque()
    for x in range(W):
        for y in(0,H-1):
            if cand[y,x] and not seen[y,x]: seen[y,x]=True;dq.append((y,x))
    for y in range(H):
        for x in(0,W-1):
            if cand[y,x] and not seen[y,x]: seen[y,x]=True;dq.append((y,x))
    while dq:
        y,x=dq.popleft()
        for dy,dx in((1,0),(-1,0),(0,1),(0,-1)):
            ny,nx=y+dy,x+dx
            if 0<=ny<H and 0<=nx<W and cand[ny,nx] and not seen[ny,nx]:
                seen[ny,nx]=True;dq.append((ny,nx))
    return ~seen   # True = sprite
def phase(win):
    g=np.abs(np.diff(win,axis=1)).sum(axis=(0,2)); h=np.abs(np.diff(win,axis=0)).sum(axis=(1,2))
    px=max(range(K),key=lambda p:g[p::K].sum() if True else 0)
    py=max(range(K),key=lambda p:h[p::K].sum())
    return (px+1)%K,(py+1)%K
def down(win,fg):
    H,W=fg.shape;h=H//K;w=W//K
    rgb=np.zeros((h,w,3),np.uint8);al=np.zeros((h,w))
    for j in range(h):
        for i in range(w):
            m=fg[j*K:(j+1)*K,i*K:(i+1)*K]
            if m.mean()>=0.5:
                al[j,i]=1
                blk=win[j*K:(j+1)*K,i*K:(i+1)*K].reshape(-1,3)[m.reshape(-1)]
                rgb[j,i]=np.median(blk,axis=0)
    return rgb,al
states={}
k=0
for (y0,y1) in rows:
    for (x0,x1) in cols:
        fy1=y1-40; ix0=x0+8; ix1=x1-8; pw=(ix1-ix0)/4
        fig=A[y0+10:fy1,ix0:ix1]
        bg=np.array(collections.Counter(map(tuple,fig.reshape(-1,3)[::7])).most_common(1)[0][0])
        frames=[]
        for i in range(4):
            xs=int(round(ix0+i*pw)); xe=int(round(ix0+(i+1)*pw))
            win=A[y0+10:fy1,xs:xe]
            fg=flood_bg(win,bg)
            for r in range(min(14,fg.shape[0])):
                if fg[r].mean()>0.7: fg[r]=False
            for r in range(max(0,fg.shape[0]-18),fg.shape[0]):
                if fg[r].mean()>0.6: fg[r]=False
            px,py=phase(win)
            win=win[py:,px:];fg=fg[py:,px:]
            frames.append(down(win,fg))
        # common size
        h=min(f[1].shape[0] for f in frames);w=min(f[1].shape[1] for f in frames)
        frames=[(r[:h,:w],a[:h,:w]) for r,a in frames]
        states[names[k]]=frames;k+=1
        print(names[k-1],w,h)
# union bbox per state
out={}
GW=0;GH=0;boxes={}
for n,fr in states.items():
    u=np.zeros(fr[0][1].shape,bool)
    for r,a in fr: u|=a>0
    ys=np.where(u.any(axis=1))[0];xs=np.where(u.any(axis=0))[0]
    boxes[n]=(ys[0],ys[-1]+1,xs[0],xs[-1]+1)
    GW=max(GW,xs[-1]+1-xs[0]);GH=max(GH,ys[-1]+1-ys[0])
GH+=1; GH+=GH%2; GW+=GW%2
print("global canvas",GW,GH)
final={}
for n,fr in states.items():
    y0,y1,x0,x1=boxes[n];bw=x1-x0;bh=y1-y0
    ox=(GW-bw)//2;oy=GH-bh
    lst=[]
    for r,a in fr:
        R=np.zeros((GH,GW,3),np.uint8);Al=np.zeros((GH,GW))
        R[oy:oy+bh,ox:ox+bw]=r[y0:y1,x0:x1];Al[oy:oy+bh,ox:ox+bw]=a[y0:y1,x0:x1]
        lst.append((R,Al))
    final[n]=lst
np.save("frames_L.npy",final,allow_pickle=True)
# preview
sc=5
sheet=Image.new("RGB",(GW*sc*8,GH*sc*6),(245,230,253))
for idx,n in enumerate(names):
    for f,(R,Al) in enumerate(final[n]):
        t=np.dstack([R,(Al*255).astype(np.uint8)])
        im=Image.fromarray(t,"RGBA").resize((GW*sc,GH*sc),Image.NEAREST)
        sheet.paste(im,((((idx%2)*4)+f)*GW*sc,(idx//2)*GH*sc),im)
sheet.save("prev3_L.png");print(sheet.size)
