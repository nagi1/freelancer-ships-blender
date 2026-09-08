# Freelancer HD Edition source audit

The full-game source is `C:/Games/Freelancer HD Edition`. Files are read in place;
the game installation is never modified. Run `python pipeline/audit_sources.py`
with the configured Blender Python to regenerate `reports/source-audit.json`.

| File under DATA/SHIPS | Records | Use |
| --- | ---: | --- |
| loadouts.ini | 359 | Registered normal equipment and inventory choices |
| loadouts_special.ini | 75 | Registered capital and special ship configurations |
| loadouts_utility.ini | 61 | Registered transports, liners, trains and utility configurations |
| loadouts_regen.ini | 359 | Unregistered alternate data; audit only, never overrides active loadouts |
| shiparch.ini | 69 | Gameplay archetypes referencing 61 distinct models |
| rtc_shiparch.ini | 46 | Registered cinematic archetypes; shared hull aliases merge with gameplay hulls |

Comparing `loadouts_regen.ini` with the active `loadouts.ini` finds 223 changed
records, each adding one shield equipment entry. The detailed added/removed
rows are retained in the audit JSON. This alternate gameplay configuration
does not add new hull geometry and is not merged into the active loadouts.

`UTILITY` contains 34 CMP/3DB files, of which 12 are referenced by ship
archetypes. Other files include damage caps, shield/escape-pod parts, train
composition variants, mining debris and a mining variant. Referenced damage
parts remain hidden references in the ship file. Unregistered models do not
receive invented ship loadouts; the audit lists them explicitly. SUR files are
collision data, and MAT libraries supply materials, not additional ships.

## LibreLancer compatibility

The pipeline uses the installed LibreLancer 2025.11 exporter. Its matching
source confirms the following:

- [FreelancerIni](https://github.com/Librelancer/Librelancer/blob/2025.11/src/LibreLancer.Data/FreelancerIni.cs)
  collects multiple `ships` and `loadouts` paths from the game configuration.
- [ShiparchIni](https://github.com/Librelancer/Librelancer/blob/2025.11/src/LibreLancer.Data/Ships/ShiparchIni.cs)
  reads Ship, child CollisionGroup, and Simple records across those files.
- [Loadout](https://github.com/Librelancer/Librelancer/blob/2025.11/src/LibreLancer.Data/Solar/Loadout.cs)
  distinguishes equipment with optional hardpoints from cargo with quantities.
- [GameDataManager.InitLoadouts](https://github.com/Librelancer/Librelancer/blob/2025.11/src/LibreLancer/GameDataManager.cs)
  resolves equipment and cargo separately. Cargo is preserved as metadata;
  it is not mounted as an external weapon or cargo container by guesswork.

RTC ship geometry can be exported with native model actions. This does not
execute cinematic THN scripts, actor choreography, or mission logic.

Each generated file embeds its selected loadout, all matching loadout choices,
source records and model aliases. One file is generated per distinct registered
model, not per NPC nickname or equipment permutation.
