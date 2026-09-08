# Freelancer to Blender

## Freelancer Liberty Elite Ship Blender Demo

<p align="center">
  <a href="https://github.com/nagi1/freelancer-ships-blender/raw/refs/heads/master/docs/media/freelancer-liberty-elite-ship-blender-demo.mp4">
    <img src="https://raw.githubusercontent.com/nagi1/freelancer-ships-blender/master/docs/media/freelancer-liberty-elite-ship-blender-demo.png" alt="Freelancer Liberty Elite ship shown in Blender" width="720">
  </a><br>
  <a href="https://github.com/nagi1/freelancer-ships-blender/raw/refs/heads/master/docs/media/freelancer-liberty-elite-ship-blender-demo.mp4">▶ Watch the Freelancer Liberty Elite Ship Blender demo video</a>
</p>

A local, deterministic pipeline that builds self-contained Blender ships from original Freelancer assets: hulls, mounted equipment, packed textures, native animations, animated effects and working light controls.

**No AI, API keys, network calls or token usage at runtime.** Blender MCP is useful for development but is not required to build or use the files.

**Validated scope:** 64 registered Freelancer HD Edition models across 13 faction/family folders. All 64 passed saved-file verification. See [CATALOG.md](CATALOG.md) for files and loadouts, and [SOURCE_AUDIT.md](SOURCE_AUDIT.md) for source selection.

## Quick start

### Requirements

- Windows and PowerShell.
- A local Freelancer installation with `DATA/` and `EXE/`.
- [LibreLancer SDK 2025.11](https://github.com/Librelancer/Librelancer/tree/2025.11), including `lleditscript.exe` and its `lib/` directory.
- Blender 5.2 with bundled Python; tested with Blender 5.2.1.
- Git for development. No additional Python packages are required.

Edit [config.json](config.json) for your machine before running. The checked-in paths describe the current workstation; nothing is downloaded automatically.

| Setting | Description |
| --- | --- |
| `game` | Freelancer installation root, not its `DATA` directory |
| `sdk` | Directory containing `lleditscript.exe` |
| `blender` | Full path to `blender.exe` |
| `threads` | Worker allowance, clamped to 1–2 logical CPUs |
| `timeout_seconds` | Per-worker timeout; default 600 seconds |
| `liberty_loadouts` | Explicit ship nickname → loadout nickname selections |

The launcher currently expects Python at `5.2/python/bin/python.exe` beside `blender.exe`. Other Blender versions require a launcher update and validation. Only `config.json` is loaded; the Git-ignored `config.local.json` is not an implemented override.

```powershell
Set-Location C:\Games\freelancer-ships
.\run.ps1 plan     # Inspect selection and dependencies.
.\run.ps1 build    # Build changed inputs; reuse unchanged outputs.
.\run.ps1 verify   # Reopen saved files and test their behavior.
```

Commands return a nonzero exit code on failure. Run `verify` after `build`: assembly checks and reopened-file verification are separate steps.

## Liberty outputs

Open files from `ships/liberty/`:

| File | Ship | Selected loadout |
| --- | --- | --- |
| `li_fighter.blend` | Patriot | `li_p_li_fighter_loadout01` |
| `li_elite.blend` | Defender | `li_n_li_elite_loadout02` |
| `li_elite2.blend` | Juni's Defender variant | `li_n_li_elite_loadout02` |
| `li_freighter.blend` | Rhino | `co_li_freighter_loadout01` |
| `li_cruiser.blend` | Liberty cruiser | `li_n_li_cruiser` |
| `li_dreadnought.blend` | Liberty dreadnought | `li_n_li_dreadnought` |

Aliases sharing a hull are recorded in the manifest instead of producing duplicate files. Batch exports only select normal registered ship loadouts; campaign, secret, set-scene, and `rm_` records are excluded. Juni's variant uses the normal Defender loadout because it has no ordinary loadout record of its own.

`ships/elet.blend` is the original hand-built Defender reference and is not overwritten by batch builds. Save manual edits to generated ships under a different filename before rebuilding.

## Using the ships in Blender

### View and animate

Files open in **EEVEE Rendered** shading with scene lighting, a world, a fitted camera and visible animated effects. Cycles is not required.

Press **Space** over the viewport to play frames 1–240 at 24 fps:

| Timeline | Behavior |
| --- | --- |
| Frame 24 onward | Native door opening, when present |
| After opening and a short hold | Native clip reversed to close doors |
| Frames 72–120 | First weapon recoil/muzzle-effect burst |
| Frames 168–216 | Second firing burst |
| Outside firing bursts | Weapon resting pose |

Door duration comes from each asset; capital ships take longer than the Defender. Only available native clips and equipment-requested recoil are scheduled.

The Liberty cruiser's forward main gun also has its original `li_cruiser_maingun`
ring/projectile effect, fired from `HpFire01` at 500 m/s every 0.5 seconds during
the two bursts. Its 2-second projectile lifetime extends the cruiser timeline to
frame 252. This is a bounded straight-flight ALE preview, without collision or
damage simulation; other ammunition is not yet given projectile previews.

### Headlight controls

1. Find **Ship_Controls** in the Outliner and select it.
2. Open **Object Properties → Custom Properties**.
3. Toggle **headlight_on** or adjust **headlight_brightness**.

Right-click either property to insert keyframes. Both the bulb and glow follow the switch. Running lights are enabled; red docking/entry lights stay off.

The same controls work through Blender Python or MCP:

```python
import bpy
controls = bpy.data.objects["Ship_Controls"]
controls["headlight_on"] = False  # True restores the headlight.
controls["headlight_brightness"] = 1.0
controls.keyframe_insert(data_path='["headlight_on"]')  # Optional.
```

The saved drivers need no add-on or startup script. Other engines/exporters must map these properties to their own lighting system.

### Scene organization

- `Freelancer_Ship` contains the hull, equipment, hardpoints, lights and effects.
- `Ship_LODs`, `Ship_Collision` and `Damage_References` preserve reference geometry separately and start excluded.
- `FX` contains animated engine, thruster, contrail and muzzle previews.
- `Lights` contains navigation bulbs/glows. `Preview_Studio` holds presentation lights and the camera separately from the ship.
- Blender Text Editor datablocks `READ_ME`, `Freelancer_manifest.json`, `Build_report.json` and `Headlight_controls` describe provenance and usage.

## Performance

Batch workers run sequentially at below-normal priority with Windows affinity restricted to at most two logical CPUs, bounded library thread settings and a timeout. The pipeline does not automatically render, upscale textures or bake simulations.

Generated scenes use EEVEE with 8 viewport samples, 32 render samples and ray tracing disabled. Particle previews are capped at eight particles per emitter. Switch to **Solid** and disable `FX` for the cheapest editing mode.

Worker limits do not restrict an independently opened interactive Blender window. Visible transparent effects still consume GPU time; utilization depends on clocks, viewport activity and other applications.

## Commands and troubleshooting

| Command | Purpose |
| --- | --- |
| `.\run.ps1 plan` | Write `reports/manifest-liberty.json` without building ships |
| `.\run.ps1 build` | Build Liberty using cached inputs where possible |
| `.\run.ps1 build -Force` | Force model conversion and ship assembly; unchanged ALE samples may still be cached |
| `.\run.ps1 verify` | Reopen and validate reported Liberty files without rendering |
| `.\run.ps1 plan -Scope all` | Inspect the full-game selection |
| `.\run.ps1 build -Scope all` | Build that scope after reviewing its manifest |
| `.\run.ps1 verify -Scope all` | Verify saved full-game outputs |
| `.\run.ps1 build -Scope all -Ship ge_transport` | Rebuild one selected ship using the shared asset cache |
| `.\run.ps1 verify -Scope all -Ship ge_transport` | Reopen and verify that ship only |

The current source is **Freelancer HD Edition**. Read [SOURCE_AUDIT.md](SOURCE_AUDIT.md)
for the registered loadout files, RTC model handling and UTILITY coverage.
`loadouts_regen.ini` is audited but is not registered by this installation.
The full manifest contains 64 distinct registered models, including RTC props.
`all` is a build selector only. Files are saved under `ships/<group>/<nickname>.blend`:
`liberty`, `bretonia`, `kusari`, `rheinland`, `corsairs`, `outcasts`, `order`,
`nomads`, `bounty_hunters`, `border_worlds`, `civilian`, `utility`, and `cinematic`.
Shared civilian, Border Worlds and utility hulls use ship-family groups because
they are operated by multiple factions. Legacy source folders named `pirate`
and `corsair` map to Corsairs and Outcasts respectively.
Aliases sharing a model do not create duplicate files. Equipment choices and
cargo metadata are embedded in each file; a model without a matching loadout
does not receive guessed equipment.

Model conversion uses batches of twelve assets with per-asset checkpoints.
Rerun the same command after correcting a failure to reuse completed assets.

Input, exporter, pipeline and Blender hashes control cache reuse. `cached` means the existing output matches its stored build signature. This is deterministic assembly, not guaranteed byte-identical Blender files. The cache does not detect manual edits to output files; use verification or rebuild as appropriate.

| Location | Contents |
| --- | --- |
| `cache/models/` | Converted GLBs and cache stamps |
| `cache/ale/`, `cache/textures/` | Sampled effects and extracted textures |
| `cache/convert.log`, `cache/effects.log` | Converter diagnostics |
| `cache/<ship>.log` | Blender assembly diagnostics |
| `cache/verify-<ship>.log` | Reopened-file verification diagnostics |
| `reports/manifest-<scope>.json` | Selected ships, dependencies and input hashes |
| `reports/<scope>/<ship>.json` | Build reports |
| `ships/<scope>/` | Generated Blender files |

For startup failures, check installation paths and the bundled Python location. For worker failures, read the log named in the error. Resolve missing source references or hardpoints rather than disabling checks or positioning equipment by eye.

## Developer guide

### Architecture

```text
Game INIs and native assets
  → dependency manifest and loadout selection
  → cached CPU model conversion and ALE sampling
  → fresh background Blender assembly
  → packed .blend and build report
  → saved-file verification
```

| Module | Responsibility |
| --- | --- |
| `pipeline/run.py` | CLI, dependency resolution, caching and bounded workers |
| `pipeline/ini.py`, `pipeline/utf.py` | Text/BINI and UTF resource parsing |
| `pipeline/build_blend.py` | Scene assembly, mounts, native actions and packing |
| `pipeline/build_fx.py` | Effect resolution, sampling and preview construction |
| `pipeline/fx_runtime.py` | Reference-derived Geometry Nodes particle animation |
| `pipeline/animation_preview.py` | Two-burst playback, EEVEE lighting and camera |
| `pipeline/navigation_lights.py` | Bulbs/glows, inherited properties and headlight controls |
| `pipeline/projectile_preview.py` | Cruiser main-gun ring effect and ammunition-timed straight flight |
| `pipeline/verify_blend.py` | Saved-file, motion and reference-pose checks |
| `pipeline/inspect_animation.py` | Local Defender/reference comparison utility |

`reference/convert.csx` and `reference/effects.csx` are active runtime templates, not merely historical examples. Some diagnostic/reference scripts retain workstation paths; the main CLI uses `config.json`. [EXPERIMENT.md](EXPERIMENT.md) records the investigation and subsequent corrections.

Mount equipment using the ship hardpoint and inverse equipment `HpConnect` transform. Preserve source pivots, action slots and base poses; keep collision meshes separate from render meshes.

### Test a change

```powershell
$cfg = Get-Content -Raw .\config.json | ConvertFrom-Json
$python = Join-Path (Split-Path $cfg.blender) '5.2/python/bin/python.exe'
& $python .\tests\test_pipeline.py
.\run.ps1 build
.\run.ps1 verify
.\run.ps1 build  # An unchanged rerun should report cached.
```

Unit tests cover text/BINI parsing, repeated equipment, shared Effect/VisEffect names and the native muzzle-flash parameter. Saved-file checks cover packed images, mount matrices, native actions, door motion/rest poses, both recoil bursts, sampled particle movement, navigation lights, headlight toggles and EEVEE setup.

The Defender is compared with `tests/defender_reference_motion.json`, sampled from `ships/elet.blend`. Automated checks do not prove every effect looks correct: inspect playback and Rendered shading for visual changes. Keep expensive renders out of the default batch workflow.

## Contributing

1. Create a branch and keep the change focused.
2. Identify the source INI, nickname, asset and hardpoint for Freelancer-specific behavior. Document approximations explicitly.
3. Add a regression test for behavioral fixes. Test animation motion and return to rest, not just action counts.
4. Run relevant tests and saved-file verification. State which ships and tool versions were checked.
5. Review the diff and commit small, coherent changes. Separate personal path changes from general implementation changes.

Change descriptions should explain the problem, resulting behavior, validation and effects on resource use or source fidelity. For bug reports, include the ship/loadout, frame number, tool versions, reproduction command and relevant log excerpt; screenshots help with visual issues.

Preserve worker limits and offline operation. Do not introduce runtime AI dependencies, invent replacement assets, or update reference fixtures merely to make a failing test pass. Explain intentional reference changes for review.

Cache, reports and generated ships are Git-ignored. `ships/elet.blend` is an explicitly tracked reference exception. Keep the current repository local unless distribution rights for included game-derived assets are resolved. Upstream projects retain their own licenses; this repository currently has no standalone license file.

## Fidelity and limitations

Original meshes, textures, hardpoints, LODs, SUR and native animation actions are retained through conversion. Selected visible equipment and referenced pilot assets use original game data.

Effects use extracted textures and sampled lifetime size/color/opacity curves. Engines sample SParam `.85`, thrusters `1`; particle density is capped and trails approximate straight flight at 80 m/s. These are **Blender recreations, not exact ALE imports**. Blinking, billboard orientation, transparency and flare-cone behavior also contain approximations.

TXM animated atlases use their source frame rectangles and FPS, driven by particle
age through a compact shader lookup. A Kusari engine ALE color curve evaluates
to NaN at the exact birth endpoint; that one sample uses its nearest finite color.
Raw sampled data remains available in the cache. Hardpoint-only equipment such
as the Nomad thruster is preserved without inventing a mesh.

Damage caps and fuse references are retained without automatically playing destruction. Runtime shields, AI aiming, general projectile simulation, audio and THN scripting are outside the current reconstruction. The cruiser's explicitly supported forward-gun preview uses source projectile speed and timing.

The full-game run converted 237 shared assets and saved 64 files (about 2.57 GiB
with packed textures). Assembly reported no missing mounts, missing textures or
unresolved requested effects. Every file was reopened to check packed assets,
mount transforms, stored actions, scheduled animation, particle clocks, light
controls and EEVEE defaults. These checks do not claim pixel-identical rendering
to Freelancer or a guaranteed GPU utilization percentage.
