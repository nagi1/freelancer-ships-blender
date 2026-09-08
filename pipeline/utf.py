from ini import *
def utf(path):
 b=path.read_bytes();assert b[:4]==b'UTF '
 ver,no,ns,pad,esize,so,sa,ss,do=struct.unpack_from('<9I',b,4);assert ver==257
 nodes=[];seen=set()
 def visit(offset,parent):
  assert offset not in seen;seen.add(offset)
  peer,name,flags,pad,child,alloc,size=struct.unpack_from('<7I',b,no+offset)
  start=so+name;n=b[start:b.index(b'\0',start)].decode('cp1252');p=parent+'/'+n
  if flags&16:
   nodes.append({'path':p,'size':None});c=child
   while c:c=visit(c,p)
  else:
   raw=b[do+child:do+child+size];assert len(raw)==size
   nodes.append({'path':p,'size':size,'raw':raw})
  return peer
 visit(0,'');return nodes
if __name__=='__main__':
 files=['ships/liberty/li_elite/li_elite.cmp','equipment/models/weapons/li_heavy_ion_blaster.cmp','equipment/models/weapons/li_smlturret.cmp','equipment/models/st/ku_thruster.3db']
 report={}
 for f in files:
  ns=utf(ROOT/'DATA'/f);report[f]=[{k:v for k,v in n.items() if k!='raw'} for n in ns]
  print('\nASSET',f)
  for n in ns:
   if n['size'] is None and ('hardpoints' in n['path'].lower() or 'animation' in n['path'].lower() or n['path'].count('/')<4):print(n['path'])
 (OUT/'native_nodes.json').write_text(json.dumps(report,indent=2),encoding='utf8')
