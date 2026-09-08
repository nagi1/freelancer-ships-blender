import bpy,json
from pathlib import Path
out={}
for path in [r'C:\Games\freelancer-ships\ships\elet.blend',r'C:\Games\freelancer-ships\ships\liberty\li_elite.blend']:
 bpy.ops.wm.open_mainfile(filepath=path)
 objects=[o for o in bpy.data.objects if o.animation_data and not o.name.startswith('ORIGINAL') and ('baydoor' in o.name.lower() or 'heavyionblaster_gun' in o.name.lower())]
 rows=[]
 for o in objects:
  ad=o.animation_data
  rows.append({'name':o.name,'mode':o.rotation_mode,'active':ad.action.name if ad.action else None,'tracks':[{'name':t.name,'mute':t.mute,'strips':[{'action':x.action.name,'slot':x.action_slot.identifier if x.action_slot else None,'start':x.frame_start,'end':x.frame_end,'a_start':x.action_frame_start,'a_end':x.action_frame_end,'repeat':x.repeat,'reverse':x.use_reverse,'scale':x.scale,'extrapolation':x.extrapolation} for x in t.strips]} for t in ad.nla_tracks],'poses':{}})
 for f in [1,24,30,36,48,54,60,72,73,74,121,168,169,217]:
  bpy.context.scene.frame_set(f)
  for o,r in zip(objects,rows):r['poses'][str(f)]=[list(o.location),list(o.rotation_quaternion)]
 out[path]=rows
Path(r'C:\Games\freelancer-ships\reports\animation-comparison.json').write_text(json.dumps(out,indent=2))
