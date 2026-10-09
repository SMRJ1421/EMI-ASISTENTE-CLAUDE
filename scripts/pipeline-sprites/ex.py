import json,glob,os,sys,re
out=[]
for f in glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl')):
    proj=os.path.basename(os.path.dirname(f)).replace('C--Users-Admin0011-','')[-40:]
    sid=os.path.basename(f)[:8]
    for line in open(f,encoding='utf-8',errors='ignore'):
        try: o=json.loads(line)
        except: continue
        if o.get('type')!='user' or o.get('isSidechain') or o.get('isMeta'): continue
        c=o.get('message',{}).get('content')
        if isinstance(c,list):
            c=' '.join(x.get('text','') for x in c if isinstance(x,dict) and x.get('type')=='text')
        if not isinstance(c,str): continue
        c=c.strip()
        if not c or c.startswith('<') and 'command-name' not in c[:40] and 'system-reminder' in c[:30]: continue
        if c.startswith('<local-command') or c.startswith('[Request interrupted') : 
            if c.startswith('[Request interrupted'): out.append((o.get('timestamp',''),proj,sid,'##INTERRUPT'))
            continue
        out.append((o.get('timestamp',''),proj,sid,re.sub(r'\s+',' ',c)[:260]))
out.sort()
with open(sys.argv[1],'w',encoding='utf-8') as w:
    for t,p,s,c in out: w.write(f"{t[:16]}|{p[-14:]}|{s}|{c}\n")
print(len(out))
