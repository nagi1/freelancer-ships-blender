# Freelancer to Blender

Local, deterministic extraction. No AI, API keys, network calls, or token use at runtime.
Uses the installed LibreLancer 2025.11 CPU model exporter and background Blender.
Source: https://github.com/Librelancer/Librelancer/tree/2025.11

Run from PowerShell:

```powershell
./run.ps1 plan
./run.ps1 build
./run.ps1 verify
```

Default scope is Liberty: six distinct hulls (Patriot, Defender, Juni's Defender,
Rhino, cruiser, dreadnought). Story/cinematic aliases sharing these models are
recorded in the manifest instead of producing duplicate hull files.
Loadouts are explicit in config.json. Juni uses MSN03_Juni, a story configuration;
there is no universal canonical loadout for every hull.

Generated files: ships/liberty/*.blend. Existing hand-assembled elet.blend is in
ships/elet.blend and is never overwritten by the batch pipeline.

Budget: one worker, at most two logical CPUs via Windows process affinity,
below-normal priority, two Blender threads, per-process timeout. No rendering,
GPU conversion, texture upscaling, or simulation baking. Files open in solid
texture-color mode; switch to material preview when needed. FX are optional and
excluded from the view layer by default; this avoids expensive transparent overdraw.
No promise of a particular Task Manager percentage: other programs and GPU clocks
affect that number.

Native models, textures, hardpoints, LODs, SUR and animation actions are retained.
Equipment uses ship hardpoints and inverse equipment HpConnect, never eyeballed
coordinates. Effects and fuses are traced and embedded as data. Unsupported FX
are reported, never silently claimed to be exact imports.

Inputs and tool/script hashes control caching; unchanged builds skip work. JSON
manifests/validation are stable and sorted. Blender files are semantically
deterministic, not guaranteed byte-identical (Blender stores internal IDs).
Game assets and generated binaries are ignored by Git; code and config are tracked.

Future full-game run: `./run.ps1 plan -Scope all`, review the selected loadouts,
then `./run.ps1 build -Scope all`. Only Liberty is built for this experiment.
