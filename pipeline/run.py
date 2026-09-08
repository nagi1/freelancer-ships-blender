"""Offline orchestration: deterministic manifests, content cache, bounded workers."""
import argparse, hashlib, json, os, subprocess, sys
from collections import deque
from pathlib import Path
import ini as fl

BASE = Path(__file__).resolve().parents[1]
def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf8')
def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()
def cs(s): return '@"' + str(s).replace('"', '""') + '"'
def v(s,k): return fl.values(s,k)
def f(s,k): return fl.first(s,k)
def low(s): return str(s or '').lower()

def plan(cfg, scope):
    game=Path(cfg['game']); fl.ROOT=game; data=game/'DATA'
    sections=[]; parsed={}
    for p in sorted(data.rglob('*.ini'),key=lambda p:str(p).lower()):
        parsed[str(p.relative_to(game))]=fl.ini(p)
        sections.extend(parsed[str(p.relative_to(game))])
    config=fl.ini(game/'EXE/freelancer.ini')
    registered=[str(row[0]).replace('\\','/') for s in config if low(s['section'])=='data' for _,row in s['entries'] if row]
    dependency_files={'data/'+str(row[0]).replace('\\','/').lower() for s in config if low(s['section'])=='data' for k,row in s['entries'] if low(k) in ('equipment','effects','fuses','explosions','ships') and row}
    def dependency(entry):
        return low(entry['file']).replace('\\','/') in dependency_files and low(entry['section']) not in ('ship','good','loadout','sound')
    # Source files registered by freelancer.ini take priority over mission-local data.
    sections.sort(key=lambda s:(str(s['file']).replace('\\','/')[5:].lower() not in [r.lower() for r in registered],low(s['file'])))
    index={}
    for s in sections:
        name=f(s,'nickname') or (f(s,'name') if low(s['section'])=='fuse' else None)
        if name:index.setdefault(low(name),[]).append(s)
    def resolve(n,kind=None):
        candidates=index.get(low(n),[])
        if kind:candidates=[s for s in candidates if low(s['section'])==low(kind)]
        else:candidates=[s for s in candidates if low(s['section']) not in ['good','loadout','ship','npcshiparch','sound']]
        return candidates[0] if candidates else None
    ship_files={'data/'+str(row[0]).replace('\\','/').lower() for s in config if low(s['section'])=='data' for k,row in s['entries'] if low(k)=='ships' and row}
    loadout_files={'data/'+str(row[0]).replace('\\','/').lower() for s in config if low(s['section'])=='data' for k,row in s['entries'] if low(k)=='loadouts' and row}
    ships=[s for s in sections if low(s['section'])=='ship' and low(s['file']).replace('\\','/') in ship_files]
    ships=[s for s in ships if f(s,'DA_archetype') and (scope=='all' or 'ships\\liberty\\' in low(f(s,'DA_archetype')))]
    groups={}
    for s in ships:groups.setdefault(low(f(s,'DA_archetype')),[]).append(s)
    assets={}; result=[]; hashes={}
    def asset(s):
        path=f(s,'DA_archetype')
        if not path:return None
        libs=[str(x[0]) for x in v(s,'material_library')]+['fx\\envmapbasic.mat']
        libs=sorted(set(x for x in libs if (data/x).exists()),key=str.lower)
        key=hashlib.sha256(json.dumps([low(path),libs]).encode()).hexdigest()[:16]
        if key in assets:return key
        files=[data/path,*[data/x for x in libs]]
        sur=(data/path).with_suffix('.sur')
        if sur.exists():files.append(sur)
        for p in files:
            if not p.exists():raise FileNotFoundError(p)
        for p in files:
            if p not in hashes:hashes[p]=digest(p)
        assets[key]={'id':key,'path':path,'libraries':libs,'sha256':{str(p.relative_to(data)):hashes[p] for p in files}}
        return key
    for model,aliases in sorted(groups.items()):
        aliases.sort(key=lambda s:(low(s['file']).replace('\\','/')!='data/ships/shiparch.ini',low(f(s,'nickname'))))
        s=next((s for s in aliases if low(f(s,'nickname'))==Path(model.replace('\\','/')).stem),aliases[0]);nick=f(s,'nickname')
        choices=[x for x in sections if low(x['section'])=='loadout' and low(f(x,'archetype'))==low(nick) and (low(x['file']).replace('\\','/') in loadout_files or 'missions' in low(x['file']))]
        selected=cfg['liberty_loadouts'].get(nick)
        if selected:
            load=next((x for x in choices if low(f(x,'nickname'))==low(selected)),None)
            if not load:raise ValueError('Configured loadout missing: '+selected)
        else:
            choices.sort(key=lambda x:(not low(f(x,'nickname')).endswith('loadout01'),low(f(x,'nickname')),low(x['file'])))
            load=choices[0] if choices else None
        mounts=[];dependencies=[];seen=set();queue=deque([s]+([load] if load else []))
        while queue:
            entry=queue.popleft();key=id(entry)
            if key in seen:continue
            seen.add(key);dependencies.append(entry)
            if low(entry['section'])=='fuse':
                raw=parsed[entry['file']];at=next(i for i,x in enumerate(raw) if x is entry)
                for x in raw[at+1:]:
                    if low(x['section'])=='fuse':break
                    queue.append(x)
            for k,vals in entry['entries']:
                for value in vals:
                    if isinstance(value,str):
                        # Effect and VisEffect may deliberately share a nickname.
                        # Follow both records instead of stopping at the first one.
                        queue.extend(ref for ref in index.get(low(value),[]) if dependency(ref))
        for row in v(load,'equip') if load else []:
            entry=resolve(row[0]);hp=str(row[1]) if len(row)>1 else None
            if not entry:raise ValueError('Unresolved equipment '+str(row[0]))
            mounts.append({'nickname':row[0],'hardpoint':hp,'asset':asset(entry),'definition':entry})
        caps=[]
        # Collision groups immediately follow their Ship section.
        raw=fl.ini(game/s['file']);at=next(i for i,x in enumerate(raw) if low(f(x,'nickname'))==low(nick))
        for x in raw[at+1:]:
            if low(x['section'])=='ship':break
            if low(x['section'])=='collisiongroup':
                dependencies.append(x)
                if f(x,'dmg_obj'):
                    cap=resolve(f(x,'dmg_obj'),'Simple')
                    if cap:caps.append({'asset':asset(cap),'hardpoint':f(x,'dmg_hp'),'definition':x})
        pilot=resolve(f(s,'pilot_mesh'),'Simple') if f(s,'pilot_mesh') else None
        result.append({'nickname':nick,'asset':asset(s),'pilot_asset':asset(pilot) if pilot else None,'aliases':sorted(f(x,'nickname') for x in aliases),'ship':s,'loadout':load,'loadout_choices':sorted(set(f(x,'nickname') for x in choices)),'mounts':mounts,'damage':caps,'dependencies':dependencies})
    return {'schema':1,'scope':scope,'game':str(game),'registered_files':registered,'ships':result,'assets':assets}

def bounded(args, log, cfg):
    env=os.environ.copy();env.update(OMP_NUM_THREADS=str(cfg['threads']),OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    flags=0x4000 if os.name=='nt' else 0  # BELOW_NORMAL_PRIORITY_CLASS
    with log.open('w',encoding='utf8') as out:
        p=subprocess.Popen(args,stdout=out,stderr=subprocess.STDOUT,env=env,creationflags=flags,cwd=BASE)
        if os.name=='nt':
            import ctypes
            kernel=ctypes.WinDLL('kernel32',use_last_error=True)
            kernel.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
            kernel.GetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)]
            available=ctypes.c_size_t();system=ctypes.c_size_t()
            if not kernel.GetProcessAffinityMask(int(p._handle),ctypes.byref(available),ctypes.byref(system)):
                p.kill();raise OSError('Cannot obtain worker CPU affinity')
            bits=[1<<i for i in range(64) if available.value&(1<<i)]
            if not kernel.SetProcessAffinityMask(int(p._handle),sum(bits[-cfg['threads']:])):
                p.kill();raise OSError('Cannot enforce worker CPU limit')
        try:code=p.wait(timeout=cfg['timeout_seconds'])
        except subprocess.TimeoutExpired:p.kill();p.wait();raise RuntimeError('Worker timeout: '+str(log))
    if code:raise RuntimeError('Worker failed; see '+str(log))

def convert(manifest,cfg,force):
    cache=BASE/'cache';cache.mkdir(exist_ok=True);out=cache/'models';out.mkdir(exist_ok=True)
    template=(BASE/'reference/convert.csx').read_text()
    header=template[:template.index('var data=')]
    exporter=template[template.index(' var r=new CpuResources(fs);'):]
    exporter=exporter[:exporter.rfind('}')]
    start=exporter.index(' foreach(var lib in new[]{');end=exporter.index('r.LoadResourceFile(lib);',start)+len('r.LoadResourceFile(lib);')
    exporter=exporter[:start]+' foreach(var lib in libs)r.LoadResourceFile(lib);'+exporter[end:]
    exporter=exporter.replace('Path.Combine(output,Path.GetFileNameWithoutExtension(path)+".glb")','destination')
    # Some legitimate equipment files (Nomad thruster) contain only hardpoints.
    at=exporter.index(' var result=')
    empty='''
 if(drawable is ModelFile emptyModel && emptyModel.Levels.Length == 0) {
   var root = new ModelNode {Name="Root"};
   foreach(var hp in emptyModel.Hardpoints) {
     var child = new ModelNode {Name=hp.Name, Transform=hp.Transform.Matrix()};
     child.Properties["hardpoint"] = true;
     child.Properties["hptype"] = hp is RevoluteHardpointDefinition ? "rev" : "fix";
     if(hp is RevoluteHardpointDefinition rev) {
       child.Properties["min"] = MathHelper.RadiansToDegrees(rev.Min);
       child.Properties["max"] = MathHelper.RadiansToDegrees(rev.Max);
       child.Properties["axis"] = rev.Axis;
     }
     root.Children.Add(child);
   }
   var model = new SimpleMesh.Model {Roots=new[]{root}, Geometries=Array.Empty<Geometry>(), Materials=new Dictionary<string,SimpleMesh.Material>()};
   using var file=File.Create(destination);model.SaveTo(file,ModelSaveFormat.GLB);
   Console.WriteLine("Converted hardpoint-only "+path);
 } else {
'''
    exporter=exporter[:at]+empty+exporter[at:]+'\n}\n'
    sdk=Path(cfg['sdk']);tool=sdk/'lleditscript.exe'
    todo=[]
    for key,a in sorted(manifest['assets'].items()):
        signature=hashlib.sha256((json.dumps(a,sort_keys=True)+template+digest(sdk/'lib/LibreLancer.ContentEdit.dll')).encode()).hexdigest()
        stamp=out/(key+'.sha256');dest=out/(key+'.glb')
        if not force and dest.exists() and stamp.exists() and stamp.read_text()==signature:continue
        todo.append((a,dest,stamp,signature))
    if not todo:return
    # Small restartable batches keep memory and the worker timeout bounded.
    for offset in range(0,len(todo),12):
        batch=todo[offset:offset+12]
        code=header+'\nvar data='+cs(Path(cfg['game'])/'DATA')+';\nvar map=new MaterialMap(); map.AddMap("EcEtOcOt","DcDtOcOt");map.AddMap("DcDtEcEt","DcDtEt");var fs=FileSystem.FromPath(data);\n'
        for a,dest,stamp,signature in batch:
            code+='\n{ var path='+cs(a['path'])+'; var destination='+cs(dest)+';var libs=new string[]{'+','.join(cs(x) for x in a['libraries'])+'};\n'+exporter+'\n}\n'
            code+='File.WriteAllText('+cs(stamp)+','+cs(signature)+');\n'
        script=cache/'convert.csx';script.write_text(code,encoding='utf8')
        bounded([str(tool),str(script)],cache/'convert.log',cfg)
        for a,dest,stamp,signature in batch:
            if not dest.exists() or not stamp.exists():raise RuntimeError('Missing conversion '+a['path'])
        print('Converted assets:',min(offset+12,len(todo)),'/',len(todo),flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['plan','build','verify']);ap.add_argument('--scope',choices=['liberty','all'],default='liberty');ap.add_argument('--ship',action='append',help='Limit work to an exact manifest nickname; repeatable');ap.add_argument('--force',action='store_true');args=ap.parse_args()
    cfg=json.loads((BASE/'config.json').read_text());cfg['threads']=max(1,min(2,int(cfg['threads'])))
    if args.command=='verify':
        reports=sorted((BASE/'reports'/args.scope).glob('*.json'))
        if args.ship:reports=[p for p in reports if p.stem in args.ship]
        if not reports:raise RuntimeError('No build reports')
        failures=[]
        for p in reports:
            r=json.loads(p.read_text());assert r['valid'],r;assert Path(r['output']).exists()
            try:
                bounded([cfg['blender'],'--background',r['output'],'--threads',str(cfg['threads']),'--python-exit-code','1','--python',str(BASE/'pipeline/verify_blend.py')],BASE/'cache'/('verify-'+p.stem+'.log'),cfg)
            except RuntimeError as error:
                failures.append({'ship':p.stem,'error':str(error)});print(p.stem,'FAILED',flush=True);continue
            print(p.stem,'PASS (reopened from disk)',flush=True)
        dump(BASE/'reports'/('verification-'+args.scope+'.json'),{'checked':len(reports),'failures':failures})
        if failures:raise RuntimeError('Verification failures: '+', '.join(f['ship'] for f in failures))
        return
    manifest=plan(cfg,args.scope);dump(BASE/'reports'/('manifest-'+args.scope+'.json'),manifest)
    if args.ship:
        unknown=set(args.ship)-{s['nickname'] for s in manifest['ships']}
        if unknown:raise ValueError('Unknown ships: '+', '.join(sorted(unknown)))
        manifest['ships']=[s for s in manifest['ships'] if s['nickname'] in args.ship]
    print('Ships:',', '.join(s['nickname'] for s in manifest['ships']),'| Unique assets:',len(manifest['assets']),flush=True)
    if args.command=='plan':return
    convert(manifest,cfg,args.force)
    from build_fx import prepare
    fx_inputs=prepare(manifest,cfg,BASE,bounded)
    for ship in manifest['ships']:
        nick=ship['nickname'];output=BASE/'ships'/args.scope/(nick+'.blend');output.parent.mkdir(parents=True,exist_ok=True)
        report=BASE/'reports'/args.scope/(nick+'.json');report.parent.mkdir(parents=True,exist_ok=True)
        sig=hashlib.sha256(json.dumps({'ship':ship,'assets':manifest['assets'],'fx':fx_inputs,'scripts':{p.name:digest(p) for p in sorted((BASE/'pipeline').glob('*.py'))},'blender':digest(Path(cfg['blender']))},sort_keys=True).encode()).hexdigest()
        if not args.force and output.exists() and report.exists() and json.loads(report.read_text()).get('signature')==sig:
            print(nick,'cached',flush=True);continue
        job={'ship':ship,'assets':manifest['assets'],'base':str(BASE),'output':str(output),'report':str(report),'signature':sig,'threads':cfg['threads']}
        path=BASE/'cache'/('job-'+nick+'.json');dump(path,job)
        bounded([cfg['blender'],'--background','--factory-startup','--threads',str(cfg['threads']),'--python-exit-code','1','--python',str(BASE/'pipeline/build_blend.py'),'--',str(path)],BASE/'cache'/(nick+'.log'),cfg)
        r=json.loads(report.read_text());assert r['valid'],r
        print(nick,'built:',r['objects'],'objects;',r['vertices'],'vertices',flush=True)

if __name__=='__main__':main()
