# Liberty experiment — 2026-09-09

## Animation correction

The first batch omitted the second firing burst and hid animated effects. The
preview now shows both bursts (72–120 and 168–216), with the reference ALE
Geometry Nodes implementation retaining lifetime size/color/alpha curves at an
eight-particle budget. Thrusters use SParam 1; engines use .85. EEVEE Rendered preview
and FX are enabled when files open. Hide FX or use Solid for minimum viewport cost.

Validation now checks actual motion and return-to-rest poses, using each ship's
native door duration (capital ship doors take longer). It also checks evaluated
particle movement. The Defender's sampled poses are compared against the tracked
fixture extracted from ships/elet.blend. All six files passed these checks.
The original inventory and initial preview limitations below describe the first
build; the animation correction above supersedes the static-card/hidden-FX defaults.

All six files generated, reopened and validated. An unchanged second invocation
reported all six cached; no converter or Blender worker was needed for that run.
Three regression tests pass (BINI/repeated entries, shared Effect/VisEffect names,
and the native muzzle-flash parameter name).

| File in ships/liberty | Visible vertices | Validated mounts incl. pilot | Native actions | Optional FX emitters |
|---|---:|---:|---:|---:|
| li_fighter.blend | 3,667 | 7 | 15 | 15 |
| li_elite.blend | 5,936 | 11 | 27 | 21 |
| li_elite2.blend | 5,167 | 10 | 24 | 21 |
| li_freighter.blend | 5,543 | 9 | 22 | 21 |
| li_cruiser.blend | 8,185 | 8 | 3 | 23 |
| li_dreadnought.blend | 14,865 | 10 | 3 | 15 |

The 43 unique converted assets are cached. Original textures are packed. Ship
aliases, candidate loadouts, equipment definitions, fuses and their steps, source
references and build reports are embedded into each blend as text datablocks.

Resource check during extraction: the background worker had BelowNormal priority,
affinity mask 51539607552 (two logical CPUs), and approximately 171 MB working set
at the sampled moment. This is a sample, not a peak-memory guarantee. The live
Blender window is separate and is not affinity-limited by the batch pipeline.

## Accuracy and deliberate limits

- Models, equipment pivots, hardpoints, textures and native actions use original
  game assets, converted with LibreLancer 2025.11. No invented hulls or weapons.
- Engine, thruster, contrail and muzzle effects use native ALE references, CRCs,
  extracted textures and sampled parameters. They are lightweight previews:
  at most eight cards per emitter, fixed SParam .85, sampled color/size, and
  straight trails at 80 m/s. These are not exact ALE simulations.
- Original ALE samples stay in cache; effect provenance and preview limitations
  stay in the blend. The saved geometry/material/driver setup needs no cache.
- Lights use inherited colors/sizes and original bulb texture. Blinks are
  deterministic approximations; docking lights start off. Billboard orientation,
  additive composition and flare-cone behavior are not exact engine rendering.
- Collision hulls, LODs and damage caps are preserved separately. Damage/fuse
  sequences are documented, not automatically played. Shield runtime behavior,
  AI turret aiming, projectile simulation, audio and THN scene scripting are not
  reproduced by this experiment.
- Native animation actions are retained. Only available native door and
  equipment-requested recoil clips are put onto the demonstration timeline.
- FX are excluded by default. Enable the FX collection and use EEVEE Rendered preview
  to inspect them. Default solid viewing avoids transparent overdraw entirely.
- Full-game scope is implemented but has not been executed or validated yet.

## Reproduction

`run.ps1 build` rebuilds only changed inputs. `run.ps1 build -Force` forces model
conversion and ship assembly. `run.ps1 verify` reopens saved outputs without
rendering. No AI, Blender MCP, network service or token consumption is involved.

The original hand-assembled rendered Defender was moved from Downloads to
ships/elet.blend. It remains distinct from the inexpensive generated li_elite.blend.

