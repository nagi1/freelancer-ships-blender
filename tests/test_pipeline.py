import json,struct,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pipeline'))
import ini
from build_fx import resolve_effect,effect_requests

class PipelineTests(unittest.TestCase):
    def test_text_and_bini_preserve_repeated_equipment(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);old=ini.ROOT;ini.ROOT=root
            try:
                p=root/'plain.ini';p.write_text('[Loadout]\nnickname = demo\nequip = gun, HpWeapon01\nequip = gun, HpWeapon02\n')
                self.assertEqual(len(ini.values(ini.ini(p)[0],'equip')),2)
                strings=b'Loadout\0nickname\0demo\0';record=struct.pack('<hh',0,1)+struct.pack('<hB',8,1)+b'\x03'+struct.pack('<i',17)
                p=root/'binary.ini';p.write_bytes(b'BINI'+struct.pack('<II',1,12+len(record))+record+strings)
                self.assertEqual(ini.first(ini.ini(p)[0],'nickname'),'demo')
            finally:ini.ROOT=old
    def test_effect_and_visual_can_share_nickname(self):
        entries=lambda **kw:[[k,[v]] for k,v in kw.items()]
        ship={'dependencies':[{'section':'Effect','entries':entries(nickname='fire',vis_effect='fire')},{'section':'VisEffect','entries':entries(nickname='fire',alchemy='engine.ale')}]}
        self.assertEqual(ini.first(resolve_effect(ship,'fire'),'alchemy'),'engine.ale')
    def test_native_flash_parameter_name(self):
        ship={'mounts':[{'definition':{'section':'Gun','entries':[['flash_particle_name',['flash']]]}}]}
        self.assertEqual(effect_requests(ship)[0]['nickname'],'flash')
    def test_cruiser_main_gun_projectile_reference(self):
        ship={'mounts':[{'definition':{'section':'Gun','entries':[['projectile_archetype',['main_ammo']],['muzzle_velocity',[500]],['refire_delay',[.5]]]}}],
              'dependencies':[{'section':'Munition','entries':[['nickname',['main_ammo']],['const_effect',['li_cruiser_maingun']],['lifetime',[2]]]}]}
        request=effect_requests(ship)[0]
        self.assertEqual((request['nickname'],request['speed'],request['refire'],request['lifetime']),('li_cruiser_maingun',500,.5,2))

if __name__=='__main__':unittest.main()
