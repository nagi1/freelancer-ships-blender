"""Shared post-build/live repair: match the reference timeline without heavy rendering."""
import bpy
from mathutils import Vector

def configure_rendered_view():
    scene=bpy.context.scene
    studio=bpy.data.collections.get('Preview_Studio')
    if not studio:studio=bpy.data.collections.new('Preview_Studio');scene.collection.children.link(studio)
    for name,energy,rotation in [('Preview_Key',4.5,(.45,-.5,-.5)),('Preview_Fill',2.5,(.8,.4,2.2)),('Preview_Rim',3.0,(2.2,.2,.5))]:
        o=bpy.data.objects.get(name)
        if not o:
            light=bpy.data.lights.new(name,'SUN');o=bpy.data.objects.new(name,light);studio.objects.link(o)
        o.data.energy=energy;o.data.angle=.2;o.data.use_shadow=name=='Preview_Key';o.rotation_euler=rotation
    world=bpy.data.worlds.get('Preview_World') or bpy.data.worlds.new('Preview_World')
    world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.025,.035,.055,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.world=world
    objects=[o for c in ['Ship_Main','Weapons','Turrets','Thruster'] for o in bpy.data.collections[c].objects if o.type=='MESH']
    bpy.context.view_layer.update()
    points=[o.matrix_world@Vector(p) for o in objects for p in o.bound_box]
    center=sum(points,Vector())/len(points) if points else Vector();radius=max(((p-center).length for p in points),default=10)
    cam=bpy.data.objects.get('Preview_Camera')
    if not cam:cam=bpy.data.objects.new('Preview_Camera',bpy.data.cameras.new('Preview_Camera'));studio.objects.link(cam)
    cam.location=center+Vector((1.2,1.6,.9)).normalized()*radius*3.8
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=45;cam.data.clip_end=max(10000,radius*30);scene.camera=cam
    for obj in bpy.data.objects:
        if obj.get('navigation_light'):
            con=next((c for c in obj.constraints if c.type=='TRACK_TO'),None) or obj.constraints.new('TRACK_TO')
            con.target=cam;con.track_axis='TRACK_Z';con.up_axis='UP_Y'
    scene.render.engine='BLENDER_EEVEE';scene.eevee.taa_samples=8;scene.eevee.taa_render_samples=32;scene.eevee.use_raytracing=False
    scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.shading.type='RENDERED';space.shading.use_scene_world_render=True;space.shading.use_scene_lights_render=True
                space.region_3d.view_location=center;space.region_3d.view_rotation=cam.rotation_euler.to_quaternion();space.region_3d.view_distance=radius*3

def configure_preview():
    scene=bpy.context.scene
    bursts=0
    for o in bpy.data.objects:
        ad=o.animation_data
        if not ad:continue
        for track in ad.nla_tracks:
            if track.name!='Fire burst':continue
            first=track.strips[0]
            if len(track.strips)==1:
                second=track.strips.new('Second firing burst',168,first.action)
                second.action_slot=first.action_slot
                second.action_frame_start=first.action_frame_start
                second.action_frame_end=first.action_frame_end
                second.repeat=first.repeat
                second.scale=first.scale
                second.extrapolation='NOTHING'
            bursts+=1
    for m in bpy.data.materials:
        if not m.use_nodes or not m.node_tree.animation_data:continue
        for fc in m.node_tree.animation_data.drivers:
            expr=fc.driver.expression
            if '72<=frame<120 and' in expr:
                fc.driver.expression=expr.replace('72<=frame<120 and','((72<=frame<120) or (168<=frame<216)) and').replace('(frame-72)%','((frame-72) if frame<120 else (frame-168))%')
    layer=bpy.context.view_layer.layer_collection.children.get('Freelancer_Ship')
    for category in ['FX','Contrails','Lights']:
        if layer and layer.children.get(category):layer.children[category].exclude=False
    scene.render.engine='BLENDER_EEVEE';scene.eevee.use_raytracing=False;scene.eevee.taa_samples=8
    scene.render.fps=24;scene.frame_start=1;scene.frame_end=max(240,int(max((o.get('projectile_end',0) for o in scene.objects),default=0)))
    for name,frame in [('Second firing burst',168),('Cease fire',216)]:
        if name not in scene.timeline_markers:scene.timeline_markers.new(name,frame=frame)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.shading.type='MATERIAL'
                area.spaces.active.shading.use_scene_world=False
                area.spaces.active.shading.use_scene_lights=False
                area.spaces.active.overlay.show_overlays=False
    scene.frame_set(1)
    configure_rendered_view()
    return bursts

if __name__=='__main__':result={'firing_components':configure_preview()}

