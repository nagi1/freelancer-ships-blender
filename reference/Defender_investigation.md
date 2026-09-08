# Defender reconstruction investigation

Inspected 8 September 2026 through the connected Blender MCP server. This is the investigation checkpoint requested before scene changes. No Blender scene modifications, animation playback, save/reload, or LancerEdit operations were performed. Local reports and read-only parsers were created outside the game installation.


**Selected reconstruction: `li_elite`, loadout `li_n_li_elite_loadout02`**, chosen by the user. The NPC definitions `li_n_li_elite_d6`, `li_n_li_elite_d7`, and `li_n_li_elite_d8` in `DATA/MISSIONS/npcships.ini` refer to this loadout. The scene identifies the hull, not which runtime loadout originally accompanied it.


Source installation: `C:\Program Files (x86)\Microsoft Games\Freelancer`. Open Blender file: `C:\Users\igfi\Downloads\elet.blend`; saved file exists, but Blender reports unsaved changes. Back up the current in-memory scene before reconstruction; copying only the disk file would omit those changes.


## Scene inventory

| Item | Observed state |
|---|---|
| Main hull | `Root` plus 8 child meshes: two engines, two wings, spoiler, glass and two bay doors |
| Objects | 108: 71 meshes and 37 empties; no armature, light or camera objects |
| Geometry breakdown | 9 main meshes, 16 additional LOD meshes, 9 VMeshWire meshes, 37 hardpoint gizmos |
| Collections | `Hardpoints`, `Hulls`, `LODs`, `Wireframes`; all excluded in the active view layer |
| Hardpoints | 37 empties: 32 Hp attachment/helper points and 5 Dp damage points, with original parent parts and fix/rev properties |
| Collision | `Hulls` is empty; the original `li_elite.sur` exists (23,512 bytes), but is not imported |
| Materials | 12 node materials, including material color variants and one `material_0x00000000` |
| Textures | 7 packed images; none depends on an external image filepath |
| Actions | `<Default>`, `Sc_end anim`, `Sc_open baydoor` |
| Animation use | Bay-door opening has quaternion keys at frames 0 and 12; current 24 fps corresponds to 0.5 seconds. All imported NLA tracks are muted; `<Default>` is active |
| Constraints/modifiers | None |
| Scene units | Metric, scale 1; Root world transform is identity |


The native CMP has matching component names, 37 hardpoints and `Animation/Script/Sc_open baydoor` and `Sc_end anim`. The ship INI explicitly names `bay_door_anim = Sc_open baydoor`. The two bay doors retain revolute construct metadata with approximately 115° and 110° limits. There is no basis for inventing moving wings: their constructs are fixed. The imported endpoints are present; interpolation, pivot fidelity and timing against native channel data still need a dedicated comparison before claiming exact animation reproduction.


**Texture provenance mismatch:** Blender’s packed `elite_256.TGA` is 1024×1024. The original DDS payload named `elite_256.TGA` in this installation’s `li_playerships.mat` is 256×256. Thus the current packed image cannot be described as a byte-exact extraction of that installed texture. Its origin is not established. Preserve it in the original backup; use extracted installation textures on the reconstruction copy when enforcing this installation as the source of truth. Other textures and the environment-map shader still need pixel/material comparisons. Principled BSDF conversion is not proof of exact Freelancer shading.


**Hardpoint evaluation:** excluded objects returned identity cached world matrices. Their local transforms are nonzero and intact. We composed parent/local transforms without editing. Native HpWeapon01 position `(0.931965, -0.426164, -3.351111)` maps to Blender `(0.931965, 3.351111, -0.426164)`, consistent with `(x,y,z) → (x,-z,y)` and no scale change for this checked point. Validate all orientation matrices after enabling only the working collection. See `hardpoint_transforms.json`.


## Selected dependency tree

```text
li_elite — Defender
├── Model
│   ├── ships/liberty/li_elite/li_elite.cmp
│   ├── ships/liberty/li_playerships.mat
│   ├── fx/envmapbasic.mat (envmapbasic)
│   └── ships/liberty/li_elite/li_elite.sur [not imported]
├── Hardpoints: 37, retained in Blender
├── Animations: Sc_open baydoor; Sc_end anim; imported default pose
├── Loadout: li_n_li_elite_loadout02
│   ├── HpWeapon01–05 → li_gun01_mark05 ×5
│   │   └── equipment/models/weapons/li_heavy_ion_blaster.cmp
│   ├── HpTurret01 → li_turret01_mark01
│   │   └── equipment/models/weapons/li_smlturret.cmp
│   ├── HpTorpedo01 → cruise_disruptor01_mark01
│   │   └── equipment/models/weapons/li_rad_launcher.cmp
│   ├── HpMine01 → mine01_mark01
│   ├── HpCM01 → ge_s_cm_01
│   │   └── both use equipment/models/weapons/li_cm_dropper01.cmp
│   ├── Internal engine → ge_le_engine_01
│   │   └── exhaust effects at HpEngine01 and HpEngine02
│   ├── HpThruster01 → ge_s_thruster_01
│   │   └── equipment/models/st/ku_thruster.3db; child HpThrust emits fire
│   └── Internal/reference equipment: npc_shield01_mark04 (HpShield01),
│       infinite_power, ge_s_scanner_02, ge_s_tractor_01, armor_scale_5
├── Lights
│   ├── HpHeadlight → LargeWhiteSpecial
│   ├── HpRunningLight01–04 → SlowSmallBlue
│   └── HpDocklight01–02 → DockingLightRedSmall
├── Contrails: HpContrail01–02 → contrail01 → li_contrail
├── Pilot: generic_pilot → equipment/models/pilot/ship_pilot.3db (not in scene)
├── Shield reference: l_elite_shield01; HpMount ↔ HpShield01
├── Collision groups: starboard wing, port wing, spoiler
│   └── separate damage-cap 3DBs at DpStarboardwing, DpPortwing, DpSpoiler
├── Damage fuses: intermed_damage_smallship01/02/03 at 400/200/133 HP
└── FX
    ├── engine fire → gf_li_smallengine02_fire
    ├── NPC engine trail → gf_li_smallengine02_trail
    ├── player alternative → gf_li_smallengine02_playtrail [not selected]
    ├── thruster → gf_ge_s_thruster_01
    ├── wing contrail → li_contrail
    ├── gun flash → li_laser_03_flash
    ├── turret flash → li_laser_01_flash
    └── destruction → explosion_li_elite → gf_explosion_li_ship02
```


Paths in the tree are relative to DATA. Actual registered files come from EXE/freelancer.ini: light/select/misc/engine/ST/weapon/prop equipment, both shiparch files, the goods files, four loadout files, effects.ini plus beam/effect-type and regional ALE definitions, effects_explosion.ini, and fuse files. The exact registration list is included in the JSON. `npcships.ini` is present and contains the cited references but is not an explicit `[Data]` line in freelancer.ini; this report does not invent such a registration. All 70,306 sections across the installation’s INI files were indexed without parse errors, including binary BINI files, to find mission references beyond the registered core files.


**NPC exception:** this loadout mounts class-5 guns, although the player shiparch permits only class 4 on HpWeapon01/02 and class 3 on HpWeapon03–05. These are the actual NPC loadout entries. Do not replace them with player-legal weapons; the chosen reconstruction is an NPC configuration.


## Component assembly and accuracy

Equipment mount rule: attach the equipment model’s `HP_child` (here `HpConnect`) to the specified ship hardpoint. In Blender column-vector convention, after consistent coordinate conversion, `weapon_world = ship_hardpoint_world @ inverse(equipment_connect_in_asset_space)`. Parenting only the weapon origin to the mount is insufficient when the connector has an offset. Preserve the weapon’s internal hierarchy, revolute aiming construct and prismatic firing construct. The reviewed [Librelancer attachment implementation](https://github.com/Librelancer/Librelancer/blob/2025.11/src/LibreLancer/World/EquipmentObjectManager.cs) explicitly applies the child connector inverse; its [weapon implementation](https://github.com/Librelancer/Librelancer/blob/2025.11/src/LibreLancer/World/Components/WeaponComponent.cs) separates hardpoint revolution from internal aiming. This is supporting reverse-engineered evidence, not an assertion that every detail of Librelancer perfectly matches the original engine.


| Component | Nickname | Source INI | Native asset / resource | Ship hardpoint | Blender object / status |
|---|---|---|---|---|---|

| Engine | ge_le_engine_01 | DATA\EQUIPMENT\engine_equip.ini | INI-defined; no model specified | internal | Not added; dependency resolved |

| ShieldGenerator | npc_shield01_mark04 | DATA\EQUIPMENT\st_equip.ini | equipment\models\st\li_refractor_shield.3db | HpShield01 | Not added; dependency resolved |

| Power | infinite_power | DATA\EQUIPMENT\misc_equip.ini | equipment\models\hardware\li_fusion_reactor.3db | internal | Not added; dependency resolved |

| Scanner | ge_s_scanner_02 | DATA\EQUIPMENT\misc_equip.ini | INI-defined; no model specified | internal | Not added; dependency resolved |

| Tractor | ge_s_tractor_01 | DATA\EQUIPMENT\misc_equip.ini | INI-defined; no model specified | internal | Not added; dependency resolved |

| Thruster | ge_s_thruster_01 | DATA\EQUIPMENT\st_equip.ini | equipment\models\st\ku_thruster.3db | HpThruster01 | Not added; dependency resolved |

| Armor | armor_scale_5 | DATA\EQUIPMENT\select_equip.ini | INI-defined; no model specified | internal | Not added; dependency resolved |

| Gun | li_gun01_mark05 | DATA\EQUIPMENT\weapon_equip.ini | equipment\models\weapons\li_heavy_ion_blaster.cmp | HpWeapon01 | Not added; dependency resolved |

| Gun | li_gun01_mark05 | DATA\EQUIPMENT\weapon_equip.ini | equipment\models\weapons\li_heavy_ion_blaster.cmp | HpWeapon02 | Not added; dependency resolved |

| Gun | li_gun01_mark05 | DATA\EQUIPMENT\weapon_equip.ini | equipment\models\weapons\li_heavy_ion_blaster.cmp | HpWeapon03 | Not added; dependency resolved |

| Gun | li_gun01_mark05 | DATA\EQUIPMENT\weapon_equip.ini | equipment\models\weapons\li_heavy_ion_blaster.cmp | HpWeapon04 | Not added; dependency resolved |

| Gun | li_gun01_mark05 | DATA\EQUIPMENT\weapon_equip.ini | equipment\models\weapons\li_heavy_ion_blaster.cmp | HpWeapon05 | Not added; dependency resolved |

| Gun | li_turret01_mark01 | DATA\EQUIPMENT\weapon_equip.ini | equipment\models\weapons\li_smlturret.cmp | HpTurret01 | Not added; dependency resolved |

| Gun | cruise_disruptor01_mark01 | DATA\EQUIPMENT\weapon_equip.ini | equipment\models\weapons\li_rad_launcher.cmp | HpTorpedo01 | Not added; dependency resolved |

| MineDropper | mine01_mark01 | DATA\EQUIPMENT\weapon_equip.ini | equipment\models\weapons\li_cm_dropper01.cmp | HpMine01 | Not added; dependency resolved |

| CounterMeasureDropper | ge_s_cm_01 | DATA\EQUIPMENT\misc_equip.ini | equipment\models\weapons\li_cm_dropper01.cmp | HpCM01 | Not added; dependency resolved |

| Light | LargeWhiteSpecial | DATA\EQUIPMENT\light_equip.ini | INI-defined; no model specified | HpHeadlight | Not added; dependency resolved |

| Light | SlowSmallBlue | DATA\EQUIPMENT\light_equip.ini | INI-defined; no model specified | HpRunningLight01 | Not added; dependency resolved |

| Light | SlowSmallBlue | DATA\EQUIPMENT\light_equip.ini | INI-defined; no model specified | HpRunningLight02 | Not added; dependency resolved |

| Light | SlowSmallBlue | DATA\EQUIPMENT\light_equip.ini | INI-defined; no model specified | HpRunningLight03 | Not added; dependency resolved |

| Light | SlowSmallBlue | DATA\EQUIPMENT\light_equip.ini | INI-defined; no model specified | HpRunningLight04 | Not added; dependency resolved |

| AttachedFX | contrail01 | DATA\EQUIPMENT\select_equip.ini | li_contrail | HpContrail01 | Not added; dependency resolved |

| AttachedFX | contrail01 | DATA\EQUIPMENT\select_equip.ini | li_contrail | HpContrail02 | Not added; dependency resolved |

| Light | DockingLightRedSmall | DATA\EQUIPMENT\light_equip.ini | INI-defined; no model specified | HpDockLight01 | Not added; dependency resolved |

| Light | DockingLightRedSmall | DATA\EQUIPMENT\light_equip.ini | INI-defined; no model specified | HpDockLight02 | Not added; dependency resolved |


For modeled equipment, the intended method is programmatic conversion of original CMP/3DB geometry, embedded and external materials, hardpoints, and constructs. Accuracy target: original asset and exact connector placement; not yet imported or validated. The two inspected weapon CMPs contain embedded `weapon_1.tga` and material variants in addition to `li_equip.mat` references. Their native `Sc_fire` and `Sc_end anim` scripts exist. The mine/countermeasure model also has scripts, but the two equipment definitions do not explicitly specify `use_animation`; do not assume they play merely because they exist. The disruptor has HpFire01 and no animation script was found in the inspected node tree.


The engine is internal equipment with no separate engine mesh in its INI. The two visible engine bodies already belong to the hull. The [engine component source](https://github.com/Librelancer/Librelancer/blob/2025.11/src/LibreLancer/Client/Components/CEngineComponent.cs) creates trail/flame renderers on HpEngine points, excluding HpEngineGlow, and passes a speed parameter. The [thruster component](https://github.com/Librelancer/Librelancer/blob/2025.11/src/LibreLancer/Client/Components/CThrusterComponent.cs) attaches its effect to the equipment’s configured `hp_particles = hpthrust`, enabled during thrust. Both positions can be exact; the eventual Blender particle rendering must be labelled as a recreation unless directly proven equivalent.


## Effect references

| Effect | Native ALE | Texture libraries | Status |
|---|---|---|---|

| gf_li_smallengine02_fire | fx\engines\gf_li_smallengine02_fire.ale | fx\planetflare.txm; fx\kioncannon.txm | File reference resolved; parameters not yet decoded |

| gf_li_smallengine02_trail | fx\engines\gf_li_smallengine02_trail.ale | fx\beam.txm; fx\sarma.txm; fx\planetflare.txm | File reference resolved; parameters not yet decoded |

| gf_li_smallengine02_playtrail | fx\engines\gf_li_smallengine02_playtrail.ale | fx\sarma.txm; fx\planetflare.txm | File reference resolved; parameters not yet decoded |

| gf_ge_s_thruster_01 | fx\equipment\gf_ge_s_thruster_01.ale | fx\planetflare.txm; fx\smoke.txm | File reference resolved; parameters not yet decoded |

| li_contrail | fx\misc\li_contrail.ale | fx\beam.txm | File reference resolved; parameters not yet decoded |

| li_laser_03_flash | fx\weapons\li_laser_03.ale | fx\sarma.txm | File reference resolved; parameters not yet decoded |

| li_laser_01_flash | fx\weapons\li_laser_01.ale | fx\sarma.txm | File reference resolved; parameters not yet decoded |

| gf_explosion_li_ship02 | fx\explosions\gf_explosion_li_ship02.ale | fx\standardeffects.txm; fx\sarma.txm; fx\kioncannon.txm; fx\lightbeam.txm | File reference resolved; parameters not yet decoded |


`contrail01` is `[AttachedFX]` in select_equip.ini with `particles = li_contrail` and `use_throttle = true`. The effect resolves to `EFT_ENGINE_CONTRAIL` and an ALE, rather than a static trailing mesh. Engine trail and wing contrail are separate systems. ALE colors, emitter dimensions, lifetime/velocity curves, texture selection within TXM libraries and throttle response still require node decoding before a faithful recreation. Static guessed cones or invented flame textures would not satisfy this task. Any eventual approximation belongs under `RECREATED_FROM_FREELANCER_ALE`. Weapon projectiles/hit effects and their definitions are preserved in the dependency data; do not display all combat effects permanently.


## Lights, damage and secondary geometry

`SlowSmallBlue → SmallBlue → Blue` inheritance resolves to color `(100,100,255)`, minimum `(0,0,64)`, bulb size 0.1, glow size 0.75, flare cone `(110,40)`, average delay 2 and blink duration 3. `LargeWhiteSpecial` has white glow, bulb color `(155,155,155)`, sizes 0.7/4 and cone `(30,0)`. Docking lights have `always_on=false`, `docking_light=true`, color `(255,64,64)`, minimum `(128,32,32)`, sizes 2/3, delay/duration 0.5/0.5 and cone `(120,90)`. These are appearance parameters, not physical watts. Recreate original bulb/shine sprites with additive emission, directional behavior and blinking; do not substitute arbitrary point-light power. Librelancer’s [light renderer](https://github.com/Librelancer/Librelancer/blob/2025.11/src/LibreLancer/Render/LightEquipRenderer.cs) supports the billboard interpretation and randomized delay, but is not a complete proof of original docking activation or flare-cone behavior. Those remain validation items.


Three ship damage fuses are non-death fuses: 400 HP starts sparks at candidate weapon/shield/thruster points; 200 HP starts fire and smoke at listed candidates; 133 HP starts continuous damage at HpWeapon01/02. Repeated hardpoint lines must retain their source semantics; exact selection/randomization should be verified before animating them. Lifetime is 1 and start time 0 in all three. The full per-fuse action blocks are kept in the JSON. No destruction effect was played.


The two wings have 267 HP each and the spoiler 400, with `root_health_proxy=true`, separability, parent/child impulses 240/7, and `explosion_small_ship_breakoff`. Each maps a damage-cap Simple nickname to a native 3DB and the corresponding Dp point. Keep those in `Damage_References`, inactive in the intact ship. `DpEngine01/02` existing in the model does not by itself establish detachable engines; the standard li_elite entry has only the three collision groups above. Keep SUR reference geometry under `Ship_Collision`, excluded from renders. The pilot, shield-link geometry, cockpit definition and tractor effects are additional references; the pilot model is absent from the current scene. Their runtime placement/visibility still needs verification before addition.


## Loadout alternatives found

The shop package `le_package → le_hull → li_elite` supplies engine, power, scanner, tractor, shield, lights and contrails, with no guns or thruster. A player save would determine actual purchased/transferred equipment; no player save was selected or inferred. Three regular Navy configurations, secret/wreck configurations, mission configurations and one burning variant were found:


| Loadout | Archetype | Source |
|---|---|---|

| li_n_li_elite_loadout01 | li_elite | DATA\SHIPS\loadouts.ini |

| li_n_li_elite_loadout02 | li_elite | DATA\SHIPS\loadouts.ini |

| li_n_li_elite_loadout03 | li_elite | DATA\SHIPS\loadouts.ini |

| SECRET_li_n_li_elite_li01a | li_elite | DATA\SHIPS\loadouts.ini |

| SECRET_li_n_li_elite_li01b | li_elite | DATA\SHIPS\loadouts.ini |

| SETSCENE_M03_Navy_Fighter | li_elite | DATA\SHIPS\loadouts.ini |

| MSN01a_Liberty_Cruiser_Escort | li_elite | DATA\SHIPS\loadouts.ini |

| MSN01b_Liberty_Heavy | li_elite | DATA\SHIPS\loadouts.ini |

| MSN01b_Liberty_Bomber | li_elite | DATA\SHIPS\loadouts.ini |

| MSN03_Liberty_Cruiser_Escort | li_elite | DATA\SHIPS\loadouts.ini |

| MSN04_King | li_elite | DATA\SHIPS\loadouts.ini |

| MSN04_Kings_Escort | li_elite | DATA\SHIPS\loadouts.ini |

| MSN04_Nomad_Liberty_Heavy_Fighter_Aggressor | li_elite | DATA\SHIPS\loadouts.ini |

| MSN04_Nomad_Liberty_Heavy_Fighter_Pursuer | li_elite | DATA\SHIPS\loadouts.ini |

| MSN04_Nomad_Liberty_Heavy_Fighter_Station_Attacker | li_elite | DATA\SHIPS\loadouts.ini |

| MSN04_Liberty_Navy_Heavy_Fighter_Easy | li_elite | DATA\SHIPS\loadouts.ini |

| MSN04_Liberty_Navy_Heavy_Fighter_Medium | li_elite | DATA\SHIPS\loadouts.ini |

| MSN04_Liberty_Navy_Heavy_Fighter_Difficult | li_elite | DATA\SHIPS\loadouts.ini |

| MSN11_Liberty_Heavy_Fighter | li_elite | DATA\SHIPS\loadouts.ini |

| MSN11_Nomad_Liberty_Heavy_Fighter | li_elite | DATA\SHIPS\loadouts.ini |

| MSN11_Nomad_Liberty_Heavy_Fighter_Ace | li_elite | DATA\SHIPS\loadouts.ini |

| MSN11_Nomad_Liberty_Heavy_Fighter_Leader | li_elite | DATA\SHIPS\loadouts.ini |

| MSN11_Nomad_Liberty_Heavy_Fighter_Prototype | li_elite | DATA\SHIPS\loadouts.ini |

| MSN02_Burning_Heavy_Fighter | li_elite | DATA\SHIPS\loadouts_special.ini |


`rtcprop_l_elite` is a third shiparch using the same CMP for cinematics, with reduced configuration. It is not evidence to mix cinematic equipment into the selected Navy loadout.


## Research and conversion route

The investigation searched Reddit, archived Lancers Reactor material, DiscoveryGC, SWAT, ModDB, and Librelancer sources. Sources were treated as evidence rather than instructions. Useful modder references:


- [Drizzt4.0’s ship-creation tutorial archive](https://lancersreactor.com/viewtopic.php_f%3D44_t%3D27904.html) and [SWAT-hosted complete guide](https://swat-portal.com/forum/filebase/download/569/) document ship packages and named equipment mounts.
- [Custom weapons: fix/rev/pris](https://lancersreactor.com/viewtopic.php_f%3D18_t%3D21579) investigates multi-component weapon transforms; [CMP/SUR and destructible components](https://lancersreactor.com/viewtopic.php_f%3D29_t%3D46479.html) explains damage-cap references.
- [Advanced fuses](https://lancersreactor.com/viewtopic.php_f%3D29_t%3D44560) and [ALE cloning](https://lancersreactor.com/viewtopic.php_f%3D29_t%3D46002.html) provide historical background on fuse sequences and ALE effect CRC/texture dependencies.
- [Discovery weapon-editing guide](https://discoverygc.com/forums/showthread.php?tid=161299) was available through indexed excerpts; direct page retrieval failed. Treat it as corroboration, not the sole basis for a decision.
- [SWAT dynamic weapons guide](https://swat-portal.com/forum/thread/12479-creating-new-dynamic-weapons/) traces muzzle/projectile effects across INIs. [Engine colours](https://swat-portal.com/forum/thread/12465-engine-colours/) discusses flame/trail fields. Its blanket suggestion that player and NPC trail names must match conflicts with this installation, where they differ; actual INIs take precedence.
- [Reddit discussion of exported models](https://www.reddit.com/r/freelancer/comments/4a42jj/all_freelancer_ships_weapons_and_turret_models/) identifies material color multiplication as the source of Liberty color variants; local nodes show those variants are present.
- [ModDB Leuchtfeuer](https://www.moddb.com/mods/leuchtfeuer) credits ALE modding work, but provides no verified Blender conversion procedure. No verified Blender 5.2-native CMP/ALE importer was established by this search.


The practical automated candidate is a standalone script using Librelancer’s model/UTF/content libraries, run with its separate [`lleditscript` command-line host](https://github.com/Librelancer/Librelancer/blob/2025.11/src/Editor/lleditscript/Program.cs), or a focused Python reader. No LancerEdit UI is needed. The host source exposes scripting support, but a CMP-to-Blender export script still needs implementation and validation; it is not an already-tested command. Our read-only UTF parser successfully inspected native weapon and thruster hardpoints and animation nodes. ALE source exposes effect libraries, typed parameters and curves; that provides a decoding route, not an existing exact Blender ALE importer.


## Next concrete Blender operation

First save a uniquely named backup of the **current in-memory** scene and preserve an independent original hierarchy with its mesh/material/action data. Then create the reconstruction hierarchy and enable hardpoints only in the working copy. Convert **one** `li_heavy_ion_blaster.cmp` with its connector, textures, revolute/prismatic constructs and Sc_fire action; align HpConnect to HpWeapon01 and verify its world transform against the native CMP. Only after that check, instance the other four guns and add the selected turret/launchers/thruster. Keep all original parts, LODs and helpers. This report is the requested checkpoint; those scene operations have not yet run.


The current investigation resolves the selected assembly and file dependencies. Remaining work: actual equipment import, full material/provenance comparison, animation fidelity tests, ALE curve extraction/recreation, original light-shape resources and runtime gating, SUR import, pilot/shield/cockpit details, and final render verification. No reconstructed component is marked complete prematurely.