"""Native bulb/glow textures at loadout hardpoints; docking lights deliberately off."""
import bpy
from pathlib import Path
from ini import first

def build_lights(job,hardpoints):
    ship=job['ship'];textures=Path(job['base'])/'cache/textures'
    definitions={str(first(d,'nickname')).lower():d for d in ship['dependencies'] if d['section'].lower()=='light'}
    collection=bpy.data.collections['Lights'];records=[]
    # Replace the earlier bulb-only preview without touching hull or equipment.
    for o in list(bpy.data.objects):
        if o.name.startswith(('Light::','Navigation::')):bpy.data.objects.remove(o,do_unlink=True)
    for mount in ship['mounts']:
        if mount['definition']['section'].lower()!='light':continue
        hp=hardpoints.get(str(mount['hardpoint']).lower())
        if not hp:continue
        if 'docklight' in hp.name.lower():
            records.append({'hardpoint':hp.name,'enabled':False});continue
        props={};seen=set();definition=mount['definition']
        while definition and str(first(definition,'nickname')).lower() not in seen:
            seen.add(str(first(definition,'nickname')).lower())
            for k,val in definition['entries']:props.setdefault(k.lower(),val)
            definition=definitions.get(str(first(definition,'inherit')).lower())
        for texture,sizekey,colorkey in [('bulb','bulb_size','color'),('shine','glow_size','glow_color')]:
            size=float(props.get(sizekey,[.1])[0]);color=tuple(float(x)/255 for x in props.get(colorkey,props.get('color',[255,255,255])))
            name='Navigation::'+hp.name+'::'+texture
            path=next(p for p in textures.iterdir() if p.stem.lower()==texture)
            image=bpy.data.images.get('NavTexture::'+texture)
            if not image:image=bpy.data.images.load(str(path));image.name='NavTexture::'+texture;image.pack()
            mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.surface_render_method='BLENDED'
            nodes=mat.node_tree.nodes;links=mat.node_tree.links;nodes.clear()
            out=nodes.new('ShaderNodeOutputMaterial');mix=nodes.new('ShaderNodeMixShader');transparent=nodes.new('ShaderNodeBsdfTransparent');emission=nodes.new('ShaderNodeEmission');tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.extension='CLIP'
            tint=nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[2].default_value=(*color,1)
            links.new(tex.outputs['Color'],tint.inputs[1]);links.new(tint.outputs[0],emission.inputs['Color'])
            strength=nodes.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.use_clamp=True;strength.inputs[1].default_value=1;links.new(tex.outputs['Color'],strength.inputs[0])
            if 'avg_delay' in props and 'blink_duration' in props:
                delay=float(props['avg_delay'][0])*24;duration=float(props['blink_duration'][0])*24
                driver=strength.inputs[1].driver_add('default_value').driver;driver.expression=f'1 if frame%{max(.1,delay+duration):.9g}<{duration:.9g} else .25'
            links.new(strength.outputs[0],mix.inputs[0]);links.new(transparent.outputs[0],mix.inputs[1]);links.new(emission.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])
            mesh=bpy.data.meshes.new(name);mesh.from_pydata([(-size,-size,0),(size,-size,0),(size,size,0),(-size,size,0)],[],[(0,1,2,3)])
            uv=mesh.uv_layers.new()
            for i,co in enumerate([(0,0),(1,0),(1,1),(0,1)]):uv.data[i].uv=co
            obj=bpy.data.objects.new(name,mesh);collection.objects.link(obj);obj.parent=hp;mesh.materials.append(mat);obj.visible_shadow=False
            obj['navigation_light']=True;obj['equipment_nickname']=mount['nickname'];obj['source_properties']=str(props)
            obj['accuracy']='Original bulb/glow textures and INI properties; camera-facing preview, flare-cone behavior approximated'
            if bpy.context.scene.camera:
                con=obj.constraints.new('TRACK_TO');con.target=bpy.context.scene.camera;con.track_axis='TRACK_Z';con.up_axis='UP_Y'
        records.append({'hardpoint':hp.name,'enabled':True,'nickname':mount['nickname']})
    return records
