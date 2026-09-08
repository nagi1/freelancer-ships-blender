"""Bounded straight-flight preview of the cruiser forward gun's native ALE."""
import bpy,math
from mathutils import Vector

def add_projectile_preview(runtime,file,effect,hp,collection,request):
    result=[];interval=request['refire']*24;life=request['lifetime']*24;speed=request['speed']
    for burst in [72,168]:
        for i in range(math.ceil(48/interval)):
            spawn=burst+i*interval
            carrier=bpy.data.objects.new(f'MainGun_Projectile_{int(spawn):03d}',None);collection.objects.link(carrier);carrier.parent=hp
            carrier['projectile_spawn']=spawn;carrier['projectile_end']=spawn+life;carrier['speed_m_s']=speed;carrier['effect_nickname']=request['nickname']
            carrier['accuracy']='Native ammunition speed/lifetime/refire; straight flight without collisions; capped ALE trail density'
            carrier.driver_add('location',1).driver.expression=f'{speed:.9g}*(frame-{spawn:.9g})/24'
            before=len(runtime.fxrecords)
            runtime.make_effect(file,effect,carrier.name,collection,'weapon_effects',False,2)
            for name in runtime.fxrecords[before:]:
                obj=bpy.data.objects[name];obj['projectile_spawn']=spawn;obj['projectile_end']=spawn+life
                obj['accuracy']=carrier['accuracy'];obj.visible_shadow=False
                materials=[]
                if obj.modifiers:
                    group=obj.modifiers[0].node_group
                    for node in group.nodes:
                        if node.type=='VECT_MATH' and node.operation=='SCALE':
                            # Subtract projectile motion to leave a trail behind its head.
                            node.inputs[0].default_value=Vector(node.inputs[0].default_value)-Vector((0,speed*obj['particle_lifetime'],0))
                        if node.type=='OBJECT_INFO' and node.inputs.get('Object') and node.inputs['Object'].default_value:
                            materials.extend(node.inputs['Object'].default_value.data.materials)
                else:
                    for vert in obj.data.vertices:vert.co.y*=speed/80
                    materials.extend(obj.data.materials)
                for mat in materials:
                    gain=next(n for n in mat.node_tree.nodes if n.type=='VALUE')
                    driver=gain.outputs[0].driver_add('default_value').driver
                    driver.expression=f'v*(1 if {spawn:.9g}<=frame<{spawn+life:.9g} else 0)'
                    nodes=mat.node_tree.nodes;links=mat.node_tree.links
                    age=next(n for n in nodes if n.type=='ATTRIBUTE')
                    visible=nodes.new('ShaderNodeMath');visible.operation='LESS_THAN'
                    links.new(age.outputs['Fac'],visible.inputs[0])
                    visible.inputs[1].driver_add('default_value').driver.expression=f'(frame-{spawn:.9g})/(24*{obj["particle_lifetime"]:.9g})'
                    emission=next(n for n in nodes if n.type=='EMISSION')
                    gate=nodes.new('ShaderNodeMath');gate.operation='MULTIPLY'
                    links.new(emission.inputs['Strength'].links[0].from_socket,gate.inputs[0]);links.new(visible.outputs[0],gate.inputs[1]);links.new(gate.outputs[0],emission.inputs['Strength'])
                result.append(name)
    return result
