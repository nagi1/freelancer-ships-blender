"""Native bulb/glow textures at loadout hardpoints; docking lights deliberately off."""
import bpy
from pathlib import Path
from ini import first

def wire_light_controls():
    controller=bpy.data.objects.get('Ship_Controls')
    if not controller:
        controller=bpy.data.objects.new('Ship_Controls',None);bpy.context.scene.collection.objects.link(controller)
    if 'headlight_on' not in controller:controller['headlight_on']=True
    if 'headlight_brightness' not in controller:controller['headlight_brightness']=1.0
    controller.id_properties_ui('headlight_on').update(description='Enable the white ship headlight bulb and glow; supports keyframes')
    controller.id_properties_ui('headlight_brightness').update(min=0,max=10,soft_max=3,description='Headlight emission multiplier; supports keyframes')
    count=0
    for obj in bpy.data.objects:
        if not obj.get('navigation_light') or not obj.parent or 'headlight' not in obj.parent.name.lower():continue
        mat=obj.data.materials[0];nodes=mat.node_tree.nodes
        strength=next(n for n in nodes if n.type=='MATH')
        emission=next(n for n in nodes if n.type=='EMISSION')
        for socket,key in [(strength.inputs[1],'headlight_on'),(emission.inputs['Strength'],'headlight_brightness')]:
            driver=socket.driver_add('default_value').driver
            for var in list(driver.variables):driver.variables.remove(var)
            var=driver.variables.new();var.name='value';var.type='SINGLE_PROP';var.targets[0].id=controller;var.targets[0].data_path='["'+key+'"]';driver.expression='value'
        count+=1
    return count

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
    wire_light_controls()
    text=bpy.data.texts.get('Headlight_controls') or bpy.data.texts.new('Headlight_controls')
    text.clear();text.write('HEADLIGHT CONTROL\nSelect Ship_Controls, then Object Properties > Custom Properties.\nToggle headlight_on; adjust headlight_brightness. Right-click either property to insert a keyframe.\nPython or MCP: bpy.data.objects["Ship_Controls"]["headlight_on"] = False\nTurn on with True. This switch controls both the original bulb and glow.\nNo add-on or startup script is required: native Blender drivers are saved in this file.\nOther engines/exporters must map these properties to their own light system.\n')
    return records
