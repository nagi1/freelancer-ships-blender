import json,struct,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pipeline'))
import ini
from build_fx import resolve_effect,effect_requests

class PipelineTests(unittest.TestCase):
    def test_output_groups_follow_factions_instead_of_scope(self):
        from run import ship_group
        for nick,path,expected in [('li_elite','ships/liberty/li_elite/li_elite.cmp','liberty'),
                                   ('co_elite','ships/pirate/pi_elite/pi_elite.cmp','corsairs'),
                                   ('pi_elite','ships/corsair/co_elite/co_elite.cmp','outcasts'),
                                   ('ge_transport','ships/utility/transport_small/transport_small.cmp','utility'),
                                   ('rtcprop_demo','ships/border_world/demo.cmp','cinematic')]:
            self.assertEqual(ship_group({'nickname':nick,'ship':{'entries':[['DA_archetype',[path]]]}}),expected)

    def test_registered_rtc_models_and_inactive_regen_loadouts(self):
        from run import plan
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);old=ini.ROOT
            try:
                for folder in ['EXE','DATA/SHIPS','DATA/ships/utility']:(root/folder).mkdir(parents=True,exist_ok=True)
                (root/'EXE/freelancer.ini').write_text('[Data]\nships = SHIPS/shiparch.ini\nships = SHIPS/rtc_shiparch.ini\nloadouts = SHIPS/loadouts.ini\n')
                (root/'DATA/SHIPS/shiparch.ini').write_text('[Ship]\nnickname = gameplay\nDA_archetype = ships/utility/model.cmp\n')
                (root/'DATA/SHIPS/rtc_shiparch.ini').write_text('[Ship]\nnickname = rtc_alias\nDA_archetype = ships/utility/model.cmp\n[Ship]\nnickname = rtc_unique\nDA_archetype = ships/utility/unique.cmp\n')
                (root/'DATA/SHIPS/loadouts.ini').write_text('[Loadout]\nnickname = active\narchetype = gameplay\n')
                (root/'DATA/SHIPS/loadouts_regen.ini').write_text('[Loadout]\nnickname = aaa_loadout01\narchetype = gameplay\n')
                for name in ['model','unique']:(root/f'DATA/ships/utility/{name}.cmp').write_bytes(b'fixture')
                result=plan({'game':td,'liberty_loadouts':{}},'all')
                self.assertEqual(len(result['ships']),2)
                gameplay=next(s for s in result['ships'] if s['nickname']=='gameplay')
                self.assertEqual(gameplay['aliases'],['gameplay','rtc_alias'])
                self.assertEqual(ini.first(gameplay['loadout'],'nickname'),'active')
            finally:ini.ROOT=old

    def test_mission_loadouts_are_never_candidates(self):
        from run import plan
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);old=ini.ROOT
            try:
                for folder in ['EXE','DATA/SHIPS','DATA/ships/utility','DATA/MISSIONS']:(root/folder).mkdir(parents=True,exist_ok=True)
                (root/'EXE/freelancer.ini').write_text('[Data]\nships = SHIPS/shiparch.ini\nloadouts = SHIPS/loadouts.ini\n')
                (root/'DATA/SHIPS/shiparch.ini').write_text('[Ship]\nnickname = gameplay\nDA_archetype = ships/utility/model.cmp\n')
                (root/'DATA/SHIPS/loadouts.ini').write_text('[Loadout]\nnickname = gameplay\narchetype = gameplay\n')
                (root/'DATA/MISSIONS/loadouts.ini').write_text('[Loadout]\nnickname = MSN99_wrong\narchetype = gameplay\n')
                (root/'DATA/ships/utility/model.cmp').write_bytes(b'fixture')
                ship=plan({'game':td,'liberty_loadouts':{}},'all')['ships'][0]
                self.assertEqual(ini.first(ship['loadout'],'nickname'),'gameplay')
                self.assertNotIn('MSN99_wrong',ship['loadout_choices'])
            finally:ini.ROOT=old

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
