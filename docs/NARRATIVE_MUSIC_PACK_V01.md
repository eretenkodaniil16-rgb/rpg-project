# Narrative Music Pack v01

## Scope

Four original narrative tracks for **Хроники странника**. This package extends the existing
MusicManager catalog only; it does not invent missing tavern/elevator/act scenes and does
not alter combat, saves, AI, or quest logic.

All four resources are `master_candidate` until they are checked in Godot on Android.

## Musical architecture

The package uses a new villain leitmotif:

`D – Eb – A – Ab – F – D`

It is intentionally asymmetrical and unstable. The motif is heard clearly in the Mad
Wizard theme, stretched and lowered during the elevator descent, and made heavier and
more destructive in the Act I finale.

The tavern track is deliberately outside that dark language. It provides a human,
warm contrast so the tower's music feels stranger when the player returns to it.

## Tracks

### `mad_wizard_theme_v01` — «Шёпот невозможной башни»

- 70 BPM, 7/8 grouped 3+2+2;
- D Phrygian/chromatic language;
- glass harmonics, detuned celesta, low bowed strings, breathy flute, choir and whisper texture;
- 32 bars / 96 s;
- seamless loop;
- context: `mad_wizard_theme`;
- intended use: signature theme for the Mad Wizard, discoveries tied to him, and selected narrative scenes.

The user referenced a track titled «Лабиринт». No melody, harmony, rhythm or arrangement
was transcribed. Only high-level descriptors were retained: mysterious, labyrinthine,
unstable and touched by madness.

### `tavern_commonroom_v01` — «Пена, струны и старые байки»

- 112 BPM, 6/8;
- D major with Mixolydian color;
- lute, fiddle, wood flute, plucked bass, frame drum and shaker;
- 32 bars / ~51.43 s;
- seamless dance loop;
- context: `tavern_commonroom`;
- no borrowed folk melody.

### `elevator_descent_floor01_v01` — «Ниже света»

- 58 BPM, 4/4;
- 16 bars / ~66.21 s;
- one-shot scripted cue;
- chromatically descending bass axis;
- the Mad Wizard motif appears only as increasingly low fragments;
- metallic mechanism pulses disappear as the descent continues;
- ends unresolved for a crossfade into first-floor ambience;
- context: `elevator_descent_floor01`.

### `act01_plan_broken_v01` — «Когда башня отвечает»

- 68 BPM, 4/4;
- 24 bars / ~84.71 s;
- one-shot Act I finale;
- starts with a restrained familiar heroic contour;
- the Mad Wizard motif progressively takes over the harmony;
- low choir, dark brass, war drums, glass alarms and mechanical fractures;
- no victory cadence; the ending collapses unresolved;
- context: `act01_plan_broken`.

## Runtime contract

The four contexts are registered in `data/audio/music_catalog.json` with
`activation = explicit_context_override`.

Until their corresponding narrative scenes exist, they are never selected by
`MusicManager._resolve_automatic_context()`.

Future integrations should use the existing API:

```gdscript
MusicManager.set_context_override(&"tavern_commonroom")
MusicManager.set_context_override(&"elevator_descent_floor01")
MusicManager.set_context_override(&"act01_plan_broken")
MusicManager.set_context_override(&"mad_wizard_theme")
```

When the scripted/location state ends:

```gdscript
MusicManager.clear_context_override()
```

This prevents scene-specific music rules from being embedded in the audio manager.

## Source and provenance

- deterministic NumPy renderer;
- 48 kHz stereo;
- Ogg Vorbis game masters;
- MIDI and MP3 diagnostics are generated in CI;
- no downloaded samples;
- no external recordings;
- no third-party melodies.

## Manual acceptance

Before approval:

1. listen to each full track with headphones;
2. listen on an Android phone speaker;
3. verify both looping tracks through at least two complete seams;
4. compare relative loudness against exploration and combat music;
5. confirm the tavern remains positive without becoming comedic;
6. confirm the elevator becomes darker over time instead of merely getting louder;
7. confirm the Act I finale communicates failure without sounding like a victory/boss ending;
8. verify the Mad Wizard theme is recognizable when its motif returns in the elevator and finale.

Do not call these tracks final before the in-game check.
