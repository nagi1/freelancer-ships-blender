"""Run only in a fresh background Blender worker; never edits the live scene."""
import bpy, json, sys, math
from pathlib import Path
from mathutils import Matrix, Vector
JOB=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text())
BASE=Path(JOB['base']);sys.path.insert(0,str(BASE/'pipeline'))
from ini import first, values
s=bpy.context.scene
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
for c in list(bpy.data.collections):bpy.data.collections.remove(c)
master=bpy.data.collections.new('Freelancer_Ship');s.collection.children.link(master)
names=['Ship_Main','Ship_LODs','Ship_Hardpoints','Ship_Collision','Weapons','Turrets','Engine','Thruster','Lights','Contrails','FX','Animations','Damage_References','Helpers','Internal_Equipment']
cols={}
for name in names:
    c=bpy.data.collections.new(name);master.children.link(c);cols[name]=c
errors=[];warnings=[];mounted=[];native_actions=[]
def comp(o):return comp(o.parent)@o.matrix_parent_inverse@o.matrix_basis if o.parent else o.matrix_basis.copy()
def hpname(o):return str(o.get('source_name',o.name)).split('.')[0]
def import_asset(key,prefix,category,hp=None,connect_required=True):
    before=set(bpy.data.objects);actions=set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=str(BASE/'cache/models'/(key+'.glb')),import_pack_images=True,import_select_created_objects=False)
    objects=sorted(set(bpy.data.objects)-before,key=lambda o:o.name)
    roots=[o for o in objects if o.parent not in objects]
    if len(roots)!=1:raise ValueError('Expected one model root: '+key)
    root=roots[0];connector=next((o for o in objects if o.name.split('.')[0].lower()=='hpconnect'),None)
    if hp:
        if not connector and connect_required:raise ValueError('Missing HpConnect: '+key)
        local=comp(root).inverted()@comp(connector) if connector else Matrix.Identity(4)
        root.parent=hp;root.matrix_parent_inverse=Matrix.Identity(4);root.matrix_basis=local.inverted()
    for o in objects:
        source=o.name;o['source_name']=source;o['source_asset']=JOB['assets'][key]['path']
        o.name=prefix+'::'+source if prefix else source
        dest='Ship_Collision' if o.get('hull') or '$hull' in source else 'Ship_LODs' if '$lod' in source else 'Ship_Hardpoints' if o.get('hardpoint') else category
        for c in list(o.users_collection):c.objects.unlink(o)
        cols[dest].objects.link(o)
        if o.get('hardpoint'):o.hide_set(True);o.hide_render=True
        if o.animation_data:
            for t in o.animation_data.nla_tracks:t.mute=True
    for a in sorted(set(bpy.data.actions)-actions,key=lambda a:a.name):
        a.name=(prefix or 'Ship')+'::'+a.name;a.use_fake_user=True;native_actions.append(a.name)
    if hp and connector:
        delta=comp(connector)-comp(hp);error=max(abs(delta[i][j]) for i in range(4) for j in range(4))
        if error>1e-4:errors.append('Attachment transform error: '+prefix)
        mounted.append({'root':root.name,'hardpoint':hp.name,'max_matrix_error':error})
    return root,objects

ship=JOB['ship'];root,shipobjects=import_asset(ship['asset'],'','Ship_Main')
root['Freelancer_ship']=ship['nickname'];root['Freelancer_loadout']=first(ship['loadout'],'nickname') if ship['loadout'] else ''
hardpoints={hpname(o).lower():o for o in shipobjects if o.get('hardpoint')}
if ship.get('pilot_asset'):
    hp=hardpoints.get('hppilot')
    if hp:import_asset(ship['pilot_asset'],'Pilot','Ship_Main',hp)
    else:warnings.append('Pilot referenced without HpPilot')
equipment=[]
for i,m in enumerate(ship['mounts']):
    hp=hardpoints.get(str(m['hardpoint']).lower());kind=m['definition']['section'].lower()
    prefix=f'{m["hardpoint"] or "Internal"}_{i:02d}_{m["nickname"]}'
    if m['asset'] and hp and kind not in ['power','shieldgenerator']:
        category='Thruster' if kind=='thruster' else 'Turrets' if 'turret' in hp.name.lower() else 'Weapons'
        r,objs=import_asset(m['asset'],prefix,category,hp)
        r['equipment_nickname']=m['nickname'];equipment.append((m,r,objs))
    else:
        r=bpy.data.objects.new(prefix,None);cols['Engine' if kind=='engine' else 'Internal_Equipment'].objects.link(r);r.parent=hp or root;r.hide_set(True)
        r['equipment_definition']=json.dumps(m['definition'],sort_keys=True)
        if m['asset'] and not hp and m['hardpoint']:errors.append('Missing equipment hardpoint '+m['hardpoint'])
        equipment.append((m,r,[]))
for i,cap in enumerate(ship['damage']):
    hp=hardpoints.get(str(cap['hardpoint']).lower())
    if hp:import_asset(cap['asset'],'Damage_'+str(i),'Damage_References',hp,False)
    else:warnings.append('Damage cap reference has no mount: '+str(cap['hardpoint']))

# Keep native action slots and base poses; schedule only native door/recoil clips.
animated=[]
for o in sorted(bpy.data.objects,key=lambda o:o.name):
    ad=o.animation_data
    if not ad:continue
    tracks={t.name:[(st.action,st.action_slot) for st in t.strips] for t in ad.nla_tracks}
    motion=next((n for n in tracks if n.lower().startswith('sc_open')),None)
    equip=next((m for m,r,objs in equipment if o in objs),None)
    if not motion and equip and first(equip['definition'],'use_animation'):
        motion=next((n for n in tracks if n.lower()==str(first(equip['definition'],'use_animation')).lower()),None)
    if not motion:continue
    base=tracks.get('<Default>');act,slot=tracks[motion][0]
    for t in list(ad.nla_tracks):ad.nla_tracks.remove(t)
    ad.action=None
    def strip(trackname,a,slot,start,end=None,repeat=1,reverse=False,ext='NOTHING'):
        t=ad.nla_tracks.new();t.name=trackname;st=t.strips.new(trackname,start,a);st.action_slot=slot
        st.action_frame_start=0;st.action_frame_end=end if end else max(1,a.frame_range[1]);st.frame_start=start;st.repeat=repeat;st.use_reverse=reverse;st.extrapolation=ext
    if base:strip('Base pose',*base[0],1,1,ext='HOLD')
    if motion.lower().startswith('sc_open'):
        duration=max(1,act.frame_range[1]);strip(motion,act,slot,24,ext='HOLD_FORWARD');strip('Close (native clip reversed)',act,slot,int(24+duration+12),reverse=True,ext='HOLD_FORWARD')
    else:
        refire=float(first(equip['definition'],'refire_delay') or .2)*24
        strip('Fire burst',act,slot,72,min(refire,max(1,act.frame_range[1])),max(1,48/min(refire,max(1,act.frame_range[1]))))
    animated.append(o.name)

# All provenance stays inside the blend, not dependent on the extraction directory.
text=bpy.data.texts.new('Freelancer_manifest.json');text.write(json.dumps(ship,indent=2,sort_keys=True))
text=bpy.data.texts.new('READ_ME');text.write('Native Freelancer model and explicitly selected loadout.\nPlay 1–240: native baydoor/recoil clips where present. Other native actions retained with fake users.\nFX, collision, LODs and damage are excluded by default for inexpensive editing. Enable FX collection to inspect approximations.\nExact source references and unsupported items are in Freelancer_manifest.json and Build_report.json.\nNo Cycles, simulations or background renders are required.\n')
s.render.engine='BLENDER_EEVEE';s.render.threads_mode='FIXED';s.render.threads=JOB['threads'];s.eevee.taa_samples=8;s.eevee.use_raytracing=False
s.render.fps=24;s.frame_start=1;s.frame_end=240;s.sync_mode='FRAME_DROP';s.frame_set(1)
for frame,label in [(1,'Idle'),(24,'Native door open'),(72,'Native weapon firing'),(121,'Idle')]:s.timeline_markers.new(label,frame=frame)
for category in ['Ship_LODs','Ship_Collision','Damage_References','Helpers','Internal_Equipment']:
    cols[category].hide_render=True
    bpy.context.view_layer.layer_collection.children[master.name].children[category].exclude=True
# Optional bounded FX generator; unsupported effects are reported explicitly.
from build_fx import build_fx
fx_report=build_fx(JOB,cols,hardpoints,equipment)
for category in ['FX','Contrails','Lights']:
    bpy.context.view_layer.layer_collection.children[master.name].children[category].exclude=True
bpy.context.view_layer.update()
visible=[o for o in bpy.data.objects if o.type=='MESH' and o.visible_get()]
points=[comp(o)@Vector(p) for o in visible for p in o.bound_box]
center=sum(points,Vector())/len(points) if points else Vector();radius=max(((p-center).length for p in points),default=10)
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.shading.type='SOLID';a.spaces.active.shading.color_type='TEXTURE';a.spaces.active.overlay.show_overlays=False
            a.spaces.active.region_3d.view_location=center;a.spaces.active.region_3d.view_distance=radius*2.8;a.spaces.active.clip_end=max(10000,radius*20)
for image in bpy.data.images:
    if image.source=='FILE' and not image.packed_file:image.pack()
from animation_preview import configure_preview
configure_preview()
unpacked=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file]
if unpacked:errors.append('Unpacked images: '+str(unpacked))
report={'valid':not errors,'errors':errors,'warnings':warnings,'nickname':ship['nickname'],'output':JOB['output'],'signature':JOB['signature'],'objects':len(s.objects),'vertices':sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH'),'visible_vertices':sum(len(o.data.vertices) for o in visible),'mounted':mounted,'native_actions':sorted(native_actions),'animated_objects':animated,'packed_images':sum(bool(i.packed_file) for i in bpy.data.images),'fx':fx_report}
text=bpy.data.texts.new('Build_report.json');text.write(json.dumps(report,indent=2,sort_keys=True))
if errors:raise RuntimeError(json.dumps(errors))
bpy.ops.wm.save_as_mainfile(filepath=JOB['output'],check_existing=False)
Path(JOB['report']).write_text(json.dumps(report,indent=2,sort_keys=True))
