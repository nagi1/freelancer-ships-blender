"""Small, optional FX previews; no simulation and no stacked hundreds of sprites."""
import json, math
from pathlib import Path
from ini import first, values

def effect_requests(ship):
    requests=[]
    for i,m in enumerate(ship['mounts']):
        d=m['definition'];kind=d['section'].lower()
        keys=['flame_effect','trail_effect'] if kind=='engine' else ['particles'] if kind in ['thruster','attachedfx'] else ['flash_particle_name','effect']
        for key in keys:
            if first(d,key):requests.append({'nickname':first(d,key),'mount_index':i,'kind':kind,'key':key})
    return requests

def resolve_effect(ship,nick):
    seen=set()
    while str(nick).lower() not in seen:
        seen.add(str(nick).lower())
        matches=[d for d in ship['dependencies'] if str(first(d,'nickname')).lower()==str(nick).lower() and d['section'].lower() in ['effect','viseffect']]
        d=next((d for d in matches if first(d,'alchemy')),matches[0] if matches else None)
        if not d:return None
        if first(d,'alchemy'):return d
        nick=first(d,'vis_effect')
    return None

def prepare(manifest,cfg,base,bounded):
    from run import cs,dump,digest
    from utf import utf
    data=Path(cfg['game'])/'DATA';dest=base/'cache/ale';dest.mkdir(exist_ok=True)
    defs={}
    for ship in manifest['ships']:
        for r in effect_requests(ship):
            d=resolve_effect(ship,r['nickname'])
            if d:defs[str(first(d,'alchemy'))]=d
    files=sorted(defs);resources=set(files)
    for d in defs.values():resources.update(str(v[0]) for v in values(d,'textures'))
    resources.add('fx/efx.txm')
    fingerprints={p:digest(data/p) for p in sorted(resources) if (data/p).exists()}
    stamp=dest/'inputs.json';template=(base/'reference/effects.csx').read_text()
    signature={'inputs':fingerprints,'template':digest(base/'reference/effects.csx')}
    if not stamp.exists() or json.loads(stamp.read_text())!=signature:
        begin=template.index(' using var stream=');body=template[begin:]
        header=template[template.index('using System;'):template.index('var root=')]
        code='#r '+json.dumps((Path(cfg['sdk'])/'lib/System.Text.Json.dll').as_posix())+'\n'+header+'\nvar root='+cs(data)+';var output='+cs(dest)+';\nvar opts=new JsonSerializerOptions{IncludeFields=true,WriteIndented=true};opts.Converters.Add(new JsonStringEnumConverter());\nforeach(var p in new string[]{'+','.join(cs(p) for p in files)+'}){\n'+body
        script=base/'cache/effects.csx';script.write_text(code)
        bounded([str(Path(cfg['sdk'])/'lleditscript.exe'),str(script)],base/'cache/effects.log',cfg)
        textures=base/'cache/textures';textures.mkdir(exist_ok=True)
        for p in sorted(resources):
            if not p.lower().endswith('.txm') or not (data/p).exists():continue
            for n in utf(data/p):
                if n['size'] and n['path'].rsplit('/',1)[-1].lower() in ['mip0','mips']:
                    name=n['path'].split('/')[-2];raw=n['raw'];ext='.dds' if raw[:4]==b'DDS ' else '.tga'
                    (textures/(name+ext)).write_bytes(raw)
        dump(stamp,signature)
    return fingerprints

def build_fx(job,cols,hardpoints,equipment):
    import bpy
    from mathutils import Matrix,Vector,Quaternion
    base=Path(job['base']);ship=job['ship'];report={'created':[],'unsupported':[],'accuracy':'RECREATED_FROM_FREELANCER_ALE; eight crossed cards maximum per emitter; sampled fixed SParam .85; straight-flight trails; approximate alpha blending'}
    C=Matrix(((1,0,0),(0,0,-1),(0,1,0)))
    # Reuse the verified elet.blend ALE node implementation, with an eight-particle
    # budget. Unlike the first batch preview it retains animated size/color/alpha.
    import fx_runtime as runtime
    layer=bpy.context.view_layer.layer_collection.children['Freelancer_Ship']
    layer.children['Helpers'].exclude=False
    textures={p.stem.lower():p for p in (base/'cache/textures').glob('*')}
    def material(name,texture,color,alpha):
        p=textures.get(str(texture).lower())
        if not p:report['unsupported'].append('Missing FX texture '+str(texture));return None
        im=bpy.data.images.get('FX::'+p.stem)
        if not im:im=bpy.data.images.load(str(p));im.name='FX::'+p.stem;im.pack()
        m=bpy.data.materials.new(name);m.use_nodes=True;m.surface_render_method='BLENDED';m['accuracy']='RECREATED_FROM_FREELANCER_ALE'
        n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');mix=n.new('ShaderNodeMixShader');tr=n.new('ShaderNodeBsdfTransparent');em=n.new('ShaderNodeEmission');tex=n.new('ShaderNodeTexImage');tex.image=im;tex.extension='CLIP'
        tint=n.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[2].default_value=(*color,1);l.new(tex.outputs['Color'],tint.inputs[1]);l.new(tint.outputs[0],em.inputs['Color'])
        mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';mask.use_clamp=True;mask.inputs[1].default_value=alpha;l.new(tex.outputs['Color'],mask.inputs[0]);l.new(mask.outputs[0],mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface']);return m
    def card(name,parent,size,mat,position=(0,0,0),trail=0):
        mesh=bpy.data.meshes.new(name)
        if trail:verts=[(-size,0,0),(size,0,0),(size,-trail,0),(-size,-trail,0),(0,0,-size),(0,0,size),(0,-trail,size),(0,-trail,-size)]
        else:verts=[(-size,-size,0),(size,-size,0),(size,size,0),(-size,size,0),(0,-size,-size),(0,size,-size),(0,size,size),(0,-size,size)]
        mesh.from_pydata(verts,[],[(0,1,2,3),(4,5,6,7)]);uv=mesh.uv_layers.new()
        for poly in mesh.polygons:
            for i,li in enumerate(poly.loop_indices):uv.data[li].uv=[(0,0),(1,0),(1,1),(0,1)][i]
        o=bpy.data.objects.new(name,mesh);cols['FX'].objects.link(o);o.parent=parent;o.location=position;mesh.materials.append(mat);o.visible_shadow=False;return o
    for req in effect_requests(ship):
        d=resolve_effect(ship,req['nickname'])
        if not d:report['unsupported'].append('Unresolved effect '+str(req['nickname']));continue
        file=Path(str(first(d,'alchemy')).replace('\\','/')).stem
        p=base/'cache/ale'/(file+'_sampled.json')
        if not p.exists():report['unsupported'].append('ALE not sampled '+file);continue
        data=json.loads(p.read_text());crc=int(first(d,'effect_crc') or 0)&0xffffffff
        effect=next((e for e in data['Effects'] if (int(e['CRC'])&0xffffffff)==crc),None)
        if not effect:report['unsupported'].append('Missing ALE effect CRC '+str(crc));continue
        mount,r,objs=equipment[req['mount_index']]
        if req['kind']=='engine':hps=[o for k,o in hardpoints.items() if k.startswith('hpengine')]
        elif req['kind']=='thruster':hps=[o for o in objs if str(o.get('source_name','')).split('.')[0].lower()==str(first(mount['definition'],'hp_particles')).lower()]
        elif objs:hps=[o for o in objs if str(o.get('source_name','')).lower().startswith('hpfire')]
        else:hps=[hardpoints[str(mount['hardpoint']).lower()]] if str(mount['hardpoint']).lower() in hardpoints else []
        refs={x['Index']:x for x in effect['Fx']};nodes={x['CRC']:x for x in data['Nodes']}
        if not hps:report['unsupported'].append('Effect lacks mount '+str(req['nickname']))
        for hp in hps:
            control='engine_on' if req['kind']=='engine' else 'thruster_on' if req['kind']=='thruster' else 'contrails_on' if req['kind']=='attachedfx' else 'weapon_effects'
            before=len(runtime.fxrecords)
            runtime.make_effect(file,effect['Name'],hp.name,cols['FX'],control,req['key']=='flash_particle_name',5 if req['kind']=='thruster' else 2)
            report['created'].extend(runtime.fxrecords[before:])
    # Inherited INI light properties; compact original texture cards, no scene lights.
    defs={str(first(d,'nickname')).lower():d for d in ship['dependencies'] if d['section'].lower()=='light'}
    for m,r,objs in equipment:
        if m['definition']['section'].lower()!='light':continue
        hp=hardpoints.get(str(m['hardpoint']).lower())
        if not hp:continue
        d=m['definition'];props={};seen=set()
        while d and str(first(d,'nickname')).lower() not in seen:
            seen.add(str(first(d,'nickname')).lower())
            for k,val in d['entries']:props.setdefault(k.lower(),val)
            d=defs.get(str(first(d,'inherit')).lower())
        color=tuple(float(x)/255 for x in props.get('color',[255,255,255]))
        mat=material('Light::'+hp.name,'bulb',color,1)
        if mat:
            card('Light::'+hp.name,hp,float(props.get('bulb_size',[.1])[0]),mat)
            mask=next(n for n in mat.node_tree.nodes if n.type=='MATH')
            if 'docklight' in hp.name.lower():mask.inputs[1].default_value=0
            elif 'avg_delay' in props and 'blink_duration' in props:
                delay=float(props['avg_delay'][0])*24;duration=float(props['blink_duration'][0])*24
                fc=mask.inputs[1].driver_add('default_value');fc.driver.expression=f'1 if frame%{max(.1,delay+duration):.9g}<{duration:.9g} else .25'
    # EEVEE-compatible alpha blending: no stochastic dither, no transparent shadows.
    for m in bpy.data.materials:
        if not m.use_nodes or not m.get('accuracy'):continue
        n=m.node_tree.nodes;l=m.node_tree.links
        add=next((x for x in n if x.type=='ADD_SHADER'),None)
        if not add:continue
        em=next(x for x in n if x.type=='EMISSION');tr=next(x for x in n if x.type=='BSDF_TRANSPARENT');tex=next(x for x in n if x.type=='TEX_IMAGE');out=next(x for x in n if x.type=='OUTPUT_MATERIAL')
        mix=n.new('ShaderNodeMixShader');mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';mask.use_clamp=True
        l.new(tex.outputs['Color'],mask.inputs[0]);l.new(em.inputs['Strength'].links[0].from_socket,mask.inputs[1]);l.new(mask.outputs[0],mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface']);n.remove(add);m.surface_render_method='BLENDED'
    for o in cols['FX'].all_objects:o.visible_shadow=False
    report['accuracy']='RECREATED_FROM_FREELANCER_ALE; reference Geometry Nodes animation with sampled size/color/alpha; eight particles per emitter; engine SParam .85 and thruster 1; straight-flight trails'
    return report


