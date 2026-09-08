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
for name in ['FX','Ship_LODs','Ship_Collision','Damage_References']:
    assert bpy.context.view_layer.layer_collection.children['Freelancer_Ship'].children[name].exclude
# Read several frames to exercise persisted NLA and simple drivers; no rendering.
for frame in [1,36,73,122,240]:s.frame_set(frame)
print('VERIFIED',r['nickname'],len(s.objects),'objects',len(r['mounted']),'mounts')
