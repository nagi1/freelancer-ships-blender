"""Native single-texture TXM atlas rectangles driven by particle age."""
import json

def configure_atlas(material,texture_node,name,age,life,path):
    if not path.exists():return
    animation=json.loads(path.read_text()).get(name.lower())
    if not animation:return
    frames=animation['frames'];indices={int(f[0]) for f in frames}
    if len(indices)!=1:raise ValueError('Unsupported multi-image TXM animation: '+name)
    n=material.node_tree.nodes;l=material.node_tree.links
    def math(op,a,b):
        node=n.new('ShaderNodeMath');node.operation=op
        for i,value in enumerate((a,b)):
            if isinstance(value,(int,float)):node.inputs[i].default_value=value
            else:l.new(value,node.inputs[i])
        return node.outputs[0]
    frame=math('FLOOR',math('MULTIPLY',age,life*animation['fps']),0)
    frame=math('MODULO',frame,len(frames))
    coord=n.new('ShaderNodeTexCoord');uv=coord.outputs['UV']
    # One constant ramp is a compact rectangle lookup, including irregular UVs.
    if len(frames)>32:raise ValueError('TXM atlas exceeds compact lookup limit: '+name)
    lookup=n.new('ShaderNodeValToRGB');ramp=lookup.color_ramp;ramp.interpolation='CONSTANT'
    ramp.elements.remove(ramp.elements[1]);ramp.elements[0].color=frames[0][1:]
    for i,f in enumerate(frames[1:],1):ramp.elements.new(i/len(frames)).color=f[1:]
    l.new(math('DIVIDE',math('ADD',frame,.5),len(frames)),lookup.inputs[0])
    split=n.new('ShaderNodeSeparateColor');l.new(lookup.outputs['Color'],split.inputs[0])
    u1,v1,u2=split.outputs[:3];v2=lookup.outputs['Alpha']
    scale=n.new('ShaderNodeCombineXYZ');offset=n.new('ShaderNodeCombineXYZ')
    l.new(math('SUBTRACT',u2,u1),scale.inputs[0]);l.new(math('SUBTRACT',v2,v1),scale.inputs[1])
    l.new(u1,offset.inputs[0]);l.new(v1,offset.inputs[1])
    mul=n.new('ShaderNodeVectorMath');mul.operation='MULTIPLY';l.new(uv,mul.inputs[0]);l.new(scale.outputs[0],mul.inputs[1])
    add=n.new('ShaderNodeVectorMath');add.operation='ADD';l.new(mul.outputs[0],add.inputs[0]);l.new(offset.outputs[0],add.inputs[1]);l.new(add.outputs[0],texture_node.inputs['Vector'])
    material['TXM_animation']=name;material['TXM_fps']=animation['fps'];material['TXM_frame_count']=len(frames)
