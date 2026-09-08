import struct,json,pathlib
ROOT=pathlib.Path(r'C:\Program Files (x86)\Microsoft Games\Freelancer')
OUT=pathlib.Path(__file__).parent
def ini(path):
 b=path.read_bytes(); sections=[]
 if b[:4]==b'BINI':
  version,off=struct.unpack_from('<II',b,4); assert version==1
  def string(n):
   start=off+n; return b[start:b.index(b'\0',start)].decode('cp1252')
  p=12
  while p<off:
   name,count=struct.unpack_from('<hh',b,p);p+=4
   s={'section':string(name),'entries':[]};sections.append(s)
   for _ in range(count):
    name,n=struct.unpack_from('<hB',b,p);p+=3; vals=[]
    for _ in range(n):
     t=b[p];p+=1
     if t==0: v=bool(b[p]);p+=1
     elif t in (1,2,3):
      v=struct.unpack_from('<f' if t==2 else '<i',b,p)[0];p+=4
      if t==3:v=string(v)
     else: raise ValueError((path,p,t))
     vals.append(v)
    s['entries'].append([string(name),vals])
  assert p==off
 else:
  for line in b.decode('cp1252').splitlines():
   line=line.split(';',1)[0].strip()
   if line.startswith('[') and ']' in line:
    s={'section':line[1:line.index(']')],'entries':[]};sections.append(s)
   elif '=' in line and sections:
    k,v=line.split('=',1);s['entries'].append([k.strip(),[x.strip() for x in v.split(',')]])
 for s in sections:s['file']=str(path.relative_to(ROOT))
 return sections
def values(s,k):return [v for key,v in s['entries'] if key.lower()==k.lower()]
def first(s,k):
 v=values(s,k);return v[0][0] if v and v[0] else None
def text(s):return '['+s['section']+'] '+s['file']+'\n'+'\n'.join(k+' = '+', '.join(map(str,v)) for k,v in s['entries'])
if __name__=='__main__':
 config=ini(ROOT/'EXE/freelancer.ini')
 loaded=[(k,v[0]) for s in config if s['section'].lower()=='data' for k,v in s['entries'] if v]
 allsecs=[];errors=[]
 for p in (ROOT/'DATA').rglob('*.ini'):
  try:allsecs.extend(ini(p))
  except Exception as e:errors.append([str(p),str(e)])
 (OUT/'ini_index.json').write_text(json.dumps(allsecs),encoding='utf8')
 (OUT/'loaded.json').write_text(json.dumps(loaded,indent=2),encoding='utf8')
 ships=[s for s in allsecs if s['section'].lower()=='ship' and any('li_elite.cmp' in str(v).lower() for k,v in s['entries'])]
 print('Matching ships',len(ships),'sections',len(allsecs),'errors',errors)
 for s in ships:print(text(s))
 names={str(first(s,'nickname')).lower() for s in ships}
 loads=[s for s in allsecs if s['section'].lower()=='loadout' and str(first(s,'archetype')).lower() in names]
 (OUT/'ship_matches.json').write_text(json.dumps({'ships':ships,'loadouts':loads},indent=2),encoding='utf8')
 print('LOADOUTS:')
 for s in loads:print(first(s,'nickname'),s['file'])
