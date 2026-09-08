"""Reopen on disk and verify packed assets, mounts, poses and inexpensive defaults."""
import bpy,json,sys
from pathlib import Path
def comp(o):return comp(o.parent)@o.matrix_parent_inverse@o.matrix_basis if o.parent else o.matrix_basis.copy()
s=bpy.context.scene;s.frame_set(1);s.view_layers[0].update()
r=json.loads(bpy.data.texts['Build_report.json'].as_string())
assert s.render.engine=='BLENDER_EEVEE'
assert not s.eevee.use_raytracing
assert s.camera is not None and s.world is not None
assert any(o.type=='LIGHT' for o in s.objects)
assert s.render.threads<=2
assert all(i.packed_file for i in bpy.data.images if i.source=='FILE')
assert len(s.objects)==r['objects']
for mount in r['mounted']:
    root=bpy.data.objects[mount['root']];hp=bpy.data.objects[mount['hardpoint']]
    connector=next(o for o in root.children_recursive if str(o.get('source_name','')).split('.')[0].lower()=='hpconnect')
    delta=comp(connector)-comp(hp)
    assert max(abs(delta[i][j]) for i in range(4) for j in range(4))<1e-4,mount
assert all(bpy.data.actions.get(a) is not None for a in r['native_actions'])
for name in ['Ship_LODs','Ship_Collision','Damage_References']:
    assert bpy.context.view_layer.layer_collection.children['Freelancer_Ship'].children[name].exclude
# Read several frames to exercise persisted NLA and simple drivers; no rendering.
from mathutils import Matrix
moving=[bpy.data.objects[n] for n in r['animated_objects']]
samples={}
for frame in [1,36,60,73,122,169,217]:
    s.frame_set(frame)
    samples[frame]={o.name:o.matrix_basis.copy() for o in moving}
def distance(a,b):return max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4))
for o in moving:
    is_gun=any(t.name=='Fire burst' for t in o.animation_data.nla_tracks)
    if is_gun:
        assert distance(samples[1][o.name],samples[73][o.name])>1e-5,('No first recoil',o.name)
        assert distance(samples[73][o.name],samples[169][o.name])<1e-4,('Second burst mismatch',o.name)
        assert distance(samples[1][o.name],samples[217][o.name])<1e-4,('Rest pose not restored',o.name)
    else:
        strips=[st for t in o.animation_data.nla_tracks for st in t.strips]
        opened=next(st for st in strips if not st.use_reverse and st.frame_start==24)
        closed=next(st for st in strips if st.use_reverse)
        s.frame_set(int(opened.frame_end))
        assert distance(samples[1][o.name],o.matrix_basis)>1e-5,('Door does not open',o.name)
        s.frame_set(int(closed.frame_end)+1)
        assert distance(samples[1][o.name],o.matrix_basis)<1e-4,('Door does not close',o.name)
assert not bpy.context.view_layer.layer_collection.children['Freelancer_Ship'].children['FX'].exclude
particles=[o for o in s.objects if any(m.type=='NODES' for m in o.modifiers)]
if particles:
    o=particles[0];positions=[]
    for frame in [1,2]:
        s.frame_set(frame);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
        assert len(ev.data.vertices)>0,('Missing evaluated particles',o.name)
        positions.append(ev.data.vertices[0].co.copy())
    assert (positions[1]-positions[0]).length>1e-7,('Static particle system',o.name)
if r['nickname']=='li_elite':
    fixture=json.loads((Path(__file__).resolve().parents[1]/'tests/defender_reference_motion.json').read_text())
    for name,poses in fixture.items():
        if name.startswith('Gun_'):
            hp=name.split('::')[0][4:];component=name.split('::')[1]
            o=next(o for o in s.objects if o.name.startswith(hp+'_') and o.name.endswith('::'+component))
        else:o=bpy.data.objects[name]
        for frame,expected in poses.items():
            s.frame_set(int(frame));actual=[list(o.location),list(o.rotation_quaternion)]
            assert max(abs(a-b) for av,bv in zip(actual,expected) for a,b in zip(av,bv))<1e-4,('Reference animation mismatch',name,frame)
print('VERIFIED',r['nickname'],len(s.objects),'objects',len(r['mounted']),'mounts')
