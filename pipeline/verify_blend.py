"""Reopen on disk and verify packed assets, mounts, poses and inexpensive defaults."""
import bpy,json,sys
from pathlib import Path
def comp(o):return comp(o.parent)@o.matrix_parent_inverse@o.matrix_basis if o.parent else o.matrix_basis.copy()
s=bpy.context.scene;s.frame_set(1);s.view_layers[0].update()
r=json.loads(bpy.data.texts['Build_report.json'].as_string())
assert s.render.engine=='BLENDER_EEVEE'
assert not s.eevee.use_raytracing
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
        assert distance(samples[1][o.name],samples[36][o.name])>1e-5,('Door does not open',o.name)
        assert distance(samples[1][o.name],samples[60][o.name])<1e-4,('Door does not close',o.name)
assert not bpy.context.view_layer.layer_collection.children['Freelancer_Ship'].children['FX'].exclude
print('VERIFIED',r['nickname'],len(s.objects),'objects',len(r['mounted']),'mounts')
