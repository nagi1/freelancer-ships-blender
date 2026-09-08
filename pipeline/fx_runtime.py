import bpy,math,json,random
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
W=Path(__file__).resolve().parents[1]/'cache'
scene=bpy.context.scene;master=bpy.data.collections['Freelancer_Ship'];ship=bpy.data.objects['Root']
def collection(name,parent=master):
 c=bpy.data.collections.get(name)
 if not c:c=bpy.data.collections.new(name);parent.children.link(c)
 return c
fx=collection('FX');enginecol=collection('FX_Engine',fx);thrustcol=collection('FX_Thruster',fx);weaponcol=collection('FX_Weapons',fx)
helpers=collection('Helpers');helpers.hide_viewport=False;helpers.hide_render=True
# Keeping helper empties evaluated prevents stale attachment matrices; hide their display individually.
for o in helpers.objects:o.hide_set(True);o.hide_render=True
ctrl=bpy.data.objects.new('Ship_Controls',None);collection('Animations').objects.link(ctrl);ctrl.empty_display_type='CIRCLE';ctrl.empty_display_size=2
ctrl['engine_on']=1.;ctrl['thruster_on']=1.;ctrl['contrails_on']=1.;ctrl['running_lights']=1.;ctrl['docking_lights']=0.;ctrl['weapon_effects']=1.
ctrl['ALE_sparam']=0.85;ctrl['preview_speed_m_s']=80.;ctrl['notes']='Native animations on timeline; FX use sampled original ALE parameters. Trails preview straight flight. Original hierarchy is preserved.'
for k in ['engine_on','thruster_on','contrails_on','running_lights','docking_lights','weapon_effects']:
 ctrl.id_properties_ui(k).update(min=0,max=1,description='0 off; 1 on')
def composed(o):return composed(o.parent)@o.matrix_parent_inverse@o.matrix_basis if o.parent else o.matrix_basis.copy()
def image_named(name):
 im=bpy.data.images.get('FreelancerFX::'+name)
 if im:return im
 p=next((p for p in (W/'textures').iterdir() if p.stem.lower()==name.lower()),None)
 if not p:
  animations=json.loads((W/'textures/animations.json').read_text())
  animation=animations.get(name.lower())
  if animation:
   index=int(animation['frames'][0][0]);p=next((p for p in (W/'textures').iterdir() if p.stem.lower()==(name+'_'+str(index)).lower()),None)
 if not p:raise ValueError('Missing original texture '+name)
 im=bpy.data.images.load(str(p),check_existing=False);im.name='FreelancerFX::'+name;im.pack();return im
def driver(socket,prop,expr='v'):
 fc=socket.driver_add('default_value');d=fc.driver;d.type='SCRIPTED';v=d.variables.new();v.name='v';v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["'+prop+'"]';d.expression=expr
def material(name,texture,colors,alphas,control,flash=False,life=1):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.surface_render_method='DITHERED';m.diffuse_color=(*colors[0],1)
 n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');add=n.new('ShaderNodeAddShader');trans=n.new('ShaderNodeBsdfTransparent');em=n.new('ShaderNodeEmission');l.new(trans.outputs[0],add.inputs[0]);l.new(em.outputs[0],add.inputs[1]);l.new(add.outputs[0],out.inputs['Surface'])
 tex=n.new('ShaderNodeTexImage');tex.image=image_named(texture);tex.extension='CLIP'
 att=n.new('ShaderNodeAttribute');att.attribute_name='ale_age'
 from texture_animation import configure_atlas
 configure_atlas(m,tex,texture,att.outputs['Fac'],life,W/'textures/animations.json')
 ramp=n.new('ShaderNodeValToRGB');ar=n.new('ShaderNodeValToRGB')
 for node,vs in [(ramp,[(*c,1) for c in colors]),(ar,[(a,a,a,1) for a in alphas])]:
  cr=node.color_ramp;cr.interpolation='LINEAR';cr.elements.remove(cr.elements[1]);cr.elements[0].color=vs[0]
  for i in sorted(set(list(range(1,len(vs),2))+[len(vs)-1])):cr.elements.new(i/(len(vs)-1)).color=vs[i]
  l.new(att.outputs['Fac'],node.inputs[0])
 mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;l.new(tex.outputs['Color'],mix.inputs[1]);l.new(ramp.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],em.inputs['Color'])
 mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(ar.outputs['Color'],mul.inputs[0]);l.new(tex.outputs['Alpha'],mul.inputs[1])
 gain=n.new('ShaderNodeValue');gain.label=control;driver(gain.outputs[0],control,'v*(1 if ((72<=frame<120) or (168<=frame<216)) and ((frame-72)%2.88<1.1) else 0)' if flash else 'v')
 strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';l.new(mul.outputs[0],strength.inputs[0]);l.new(gain.outputs[0],strength.inputs[1]);l.new(strength.outputs[0],em.inputs['Strength'])
 m['accuracy']='RECREATED_FROM_FREELANCER_ALE';return m
def meshobject(name,verts,faces,col,parent=None):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);col.objects.link(o)
 if parent:o.parent=parent;o.matrix_parent_inverse=Matrix.Identity(4)
 return o
def uv_default(mesh):
 uv=mesh.uv_layers.new(name='UVMap')
 for p in mesh.polygons:
  for j,li in enumerate(p.loop_indices):uv.data[li].uv=[(0,0),(1,0),(1,1),(0,1)][j%4]
def val(d,k,default=0):
 v=d.get(k,default);return v[0] if isinstance(v,list) else v
def curve(d,k,default):return d.get(k,[default]*33)
def colors(d):
 values=[tuple(float(v[k]) for k in ('R','G','B')) for v in d.get('BasicApp_Color',[{'R':1,'G':1,'B':1}]*33)]
 # A zero-width ALE key interval can evaluate to NaN exactly at birth.
 # Use the nearest finite sampled color, retaining all other source samples.
 valid=[i for i,c in enumerate(values) if all(math.isfinite(x) for x in c)]
 if not valid:raise ValueError('ALE color curve has no finite samples')
 return [c if all(math.isfinite(x) for x in c) else values[min(valid,key=lambda j:abs(j-i))] for i,c in enumerate(values)]
C=Matrix(((1,0,0),(0,0,-1),(0,1,0)))
fxrecords=[]
def make_effect(file,effectname,hp,col,control,flash=False,sample=2):
 data=json.loads((W/'ale'/(file+'_sampled.json')).read_text());nodes={n['CRC']:n for n in data['Nodes']}
 effect=next(e for e in data['Effects'] if e['Name'].lower()==effectname.lower());refs={r['Index']:r for r in effect['Fx']}
 mount=bpy.data.objects[hp]
 for pair in effect['Pairs']:
  er=refs[pair['Item1']];ap=refs[pair['Item2']]
  en=nodes.get(er['CRC']);an=nodes.get(ap['CRC'])
  if not en or not an:continue
  ed=en['Samples'][sample]['Parameters'];ad=an['Samples'][sample]['Parameters']
  frequency=val(ed,'Emitter_Frequency');life=max(.001,val(ed,'Emitter_InitLifeSpan',.2));pressure=val(ed,'Emitter_Pressure')
  if frequency<=0:continue
  tr=ed.get('Node_Transform',{});pos=tr.get('Translation',{'X':0,'Y':0,'Z':0});rot=tr.get('Rotation',{'W':1,'X':0,'Y':0,'Z':0})
  origin=C@Vector((pos['X'],pos['Y'],pos['Z']));direction=C@(Quaternion((rot['W'],rot['X'],rot['Y'],rot['Z']))@Vector((0,1,0)))
  label=f'{effectname}::{hp}::{an["Name"]}::{pair["Item1"]}'
  mat=material(label,ad.get('BasicApp_TexName','planetflare'),colors(ad),curve(ad,'BasicApp_Alpha',1),control,flash,life)
  if an['Name']=='FLBeamAppearance':
   # World-space trail represented by a straight-flight preview at the configured speed.
   count=max(3,min(64,round(frequency*life)));width=curve(ad,'RectApp_Width',1);length=80*life
   verts=[];faces=[];ages=[]
   for plane in range(2):
    start=len(verts);side=Vector((1,0,0)) if plane==0 else Vector((0,0,1))
    for i in range(count+1):
     age=i/count;w=width[min(32,round(age*32))]/2;p=origin+Vector((0,-length*age,0));verts.extend([p-side*w,p+side*w]);ages.extend([age,age])
    for i in range(count):j=start+i*2;faces.append((j,j+1,j+3,j+2))
   o=meshobject(label,verts,faces,col,mount);uv_default(o.data)
   a=o.data.attributes.new('ale_age','FLOAT','POINT')
   for i,v in enumerate(ages):a.data[i].value=v
   o.data.materials.append(mat);o['preview_assumption']='Straight flight at 80 m/s; not an exact motion-history simulation'
  else:
   count=max(1,min(8,math.ceil(frequency*life)))
   o=meshobject(label,[origin]*count,[],col,mount)
   # Original texture on crossed quads. Perp rings use one plane perpendicular to exhaust.
   if an['Name']=='FxPerpAppearance':vs=[(-1,0,-1),(1,0,-1),(1,0,1),(-1,0,1)];fs=[(0,1,2,3)]
   else:vs=[(-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0),(0,-1,-1),(0,1,-1),(0,1,1),(0,-1,1)];fs=[(0,1,2,3),(4,5,6,7)]
   card=meshobject('SpriteSource::'+label,vs,fs,helpers);uv_default(card.data);card.data.materials.append(mat);card.hide_set(True);card.hide_render=True
   ng=bpy.data.node_groups.new('ALE_Particles::'+label,'GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
   n=ng.nodes;l=ng.links
   inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');idx=n.new('GeometryNodeInputIndex');time=n.new('GeometryNodeInputSceneTime')
   def mathnode(op):x=n.new('ShaderNodeMath');x.operation=op;return x
   div=mathnode('DIVIDE');l.new(idx.outputs[0],div.inputs[0]);div.inputs[1].default_value=count
   speed=mathnode('DIVIDE');l.new(time.outputs['Seconds'],speed.inputs[0]);speed.inputs[1].default_value=life
   add=mathnode('ADD');l.new(div.outputs[0],add.inputs[0]);l.new(speed.outputs[0],add.inputs[1]);fract=mathnode('FRACT');l.new(add.outputs[0],fract.inputs[0])
   store=n.new('GeometryNodeStoreNamedAttribute');store.data_type='FLOAT';store.domain='POINT';store.inputs['Name'].default_value='ale_age';l.new(inp.outputs['Geometry'],store.inputs['Geometry']);l.new(fract.outputs[0],store.inputs['Value'])
   vm=n.new('ShaderNodeVectorMath');vm.operation='SCALE';vm.inputs[0].default_value=direction*pressure*life;l.new(fract.outputs[0],vm.inputs['Scale'])
   setpos=n.new('GeometryNodeSetPosition');l.new(store.outputs['Geometry'],setpos.inputs['Geometry']);l.new(vm.outputs['Vector'],setpos.inputs['Offset'])
   fc=n.new('ShaderNodeFloatCurve');fc.mapping.initialize();c=fc.mapping.curves[0];sizes=curve(ad,'BasicApp_Size',.5);c.points[0].location=(0,sizes[0]);c.points[-1].location=(1,sizes[-1]);fc.mapping.use_clip=False
   for i in range(1,32):c.points.new(i/32,sizes[i])
   for p in c.points:p.handle_type='VECTOR'
   fc.mapping.update();l.new(fract.outputs[0],fc.inputs['Value'])
   info=n.new('GeometryNodeObjectInfo');info.inputs['Object'].default_value=card;info.transform_space='ORIGINAL';info.inputs['As Instance'].default_value=False
   inst=n.new('GeometryNodeInstanceOnPoints');l.new(setpos.outputs['Geometry'],inst.inputs['Points']);l.new(info.outputs['Geometry'],inst.inputs['Instance']);l.new(fc.outputs['Value'],inst.inputs['Scale'])
   real=n.new('GeometryNodeRealizeInstances');l.new(inst.outputs['Instances'],real.inputs['Geometry']);l.new(real.outputs['Geometry'],out.inputs['Geometry'])
   mod=o.modifiers.new('Original ALE parameters • animated particles','NODES');mod.node_group=ng
   o['preview_assumption']='Deterministic continuous emission; crossed texture cards replace view-facing ALE sprites; sampled curves at fixed SParam'
  o['accuracy']='RECREATED_FROM_FREELANCER_ALE';o['effect_nickname']=effectname;o['ALE_source']=file+'.ale';o['emitter_frequency']=frequency;o['particle_lifetime']=life;o['emitter_pressure']=pressure;o['SParam']=en['Samples'][sample]['SParam']
  fxrecords.append(o.name)

