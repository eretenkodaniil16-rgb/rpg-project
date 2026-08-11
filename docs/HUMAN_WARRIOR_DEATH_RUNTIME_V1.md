# Human Warrior Death Runtime v1

Death Runtime v1 connects the approved directional death renders to the production player without replacing the current `main` runtime stack. It is limited to the human fighter hero; Irina and NPC visuals are unchanged.

The integration branch is based on `main` commit `ae44e9b`. `game_death_runtime_v1.gd` extends the existing `game_ai_stealth_v2_ui_runtime.gd` entrypoint, so the inherited Combat AI Coordination v1 layer remains active.

## Asset contract

- Variants: `death_01_base`, `death_02_base`, `death_03_base`.
- Atlas layout: 768×384 RGBA, eight 96×96 frames per direction.
- Direction rows: down, left, right, up.
- Playback: 10 FPS, non-looping, 0.8 seconds.
- Frame 8 is held indefinitely as the corpse pose; frames 7 and 8 are pixel-identical in every direction.
- Selection weights are data-driven and currently equal (`1.0` each).
- The immediately previous variant is excluded when at least two variants are available.
- Missing requested art falls back to `death_01_base`; if that set is also unavailable, the existing static character visual is held for the same minimum interval.

The three runtime atlases were assembled without scaling or resampling from the 96 approved frames in `local_20260810_death_directional_cycles_v01_render_final2`. The source run-manifest SHA-256 is `857f0dc53619611edf40a481768a5fbfec51ae98149fca6768c336e29a0688f3`. Source provenance points to PR #101 / commit `a9184e7b90e2470c0368ae40908b05bee3118449`; Death Runtime v1 does not depend on that branch at runtime.

## Runtime semantics

The production scene uses `game_death_runtime_v1.gd`. A death presentation starts only after the SRD combat state sets `dead = true`, including a third death-save failure or massive instant death. Merely reaching 0 HP, being unconscious, stabilizing, or a nonlethal knockout does not trigger it.

Priority is:

1. confirmed death;
2. hit reaction;
3. attack and movement animation.

Confirmed death cancels active attack/hit visuals, clears queued hit reactions, locks movement and facing, closes pending reaction prompts, and preserves the last look direction. The existing guard-post death/load transition remains in charge of scene recovery and begins its transition no earlier than its one-second delay, after the 0.8-second death animation has completed.

`PlayerCharacter` serializes `last_death_variant_id` and a normalized `death_visual_state` containing variant, direction, `playing`/`corpse_hold`, and frame index. Loading a zero-HP corpse restores its exact variant, direction and held pose, marks the transient combat state as finally dead, and resumes the protected last-save transition. Living characters discard stale corpse state. These fields are optional, so older saves remain compatible.

## Verification

`validate-human-warrior-death-runtime-v1.yml` runs on Godot 4.7.1 Standard and verifies:

- atlas hashes, dimensions, binary alpha, baseline, edges, final holds and `death_03` weapon separation;
- equal weighted selection, no immediate repeat and the two-stage fallback;
- legacy and corpse-state serialization;
- ordinary 0 HP and stabilization do not trigger death;
- third death-save failure and massive instant death do trigger the directional animation;
- all 12 variant/direction cycles resolve to the correct Godot animation and anchor;
- movement, facing, attacks and hit reactions yield to death;
- frame 8 and directional anchor compensation persist;
- static fallback also respects the 0.8-second minimum;
- attack, hit, damage/fall, nonlethal and controllable-ally regressions;
- the production death entrypoint still exposes and passes the current Combat AI Coordination v1 runtime contract.

Repository-wide Android PR workflows separately build the debug APK with Godot 4.7.1 and validate the Android export.
