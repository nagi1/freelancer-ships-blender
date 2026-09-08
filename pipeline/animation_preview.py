"""Shared post-build/live repair: match the reference timeline without heavy rendering."""
import bpy

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
    scene.render.fps=24;scene.frame_start=1;scene.frame_end=240
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
    return bursts

if __name__=='__main__':result={'firing_components':configure_preview()}
