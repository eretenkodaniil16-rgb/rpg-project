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
Wizard theme. In `elevator_descent_floor01_v01` revision 02 it fractures between `D/Eb`
and `A/Ab` while the lift keeps descending; in `act01_plan_broken_v01` revision 02 the
same semitone cells become an obsessive panic loop.

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

### `elevator_descent_floor01_v01` — «Ниже света», revision 02

- 61 BPM, 4/4;
- 17 bars / ~66.89 s;
- one-shot scripted cue;
- chromatically descending physical bass axis remains slow and unavoidable;
- the lift mechanism begins regular, then loses metric symmetry;
- `D/Eb` and `A/Ab` fragments split the Mad Wizard leitmotif into unstable semitone pairs;
- high celesta flashes and whispers become increasingly intrusive while the low register continues downward;
- in the final section a faster internal panic pulse appears over the still-slow descent, creating the sensation that the character is sinking into fear rather than merely travelling downward;
- ends unresolved for a crossfade into first-floor ambience;
- context: `elevator_descent_floor01`.

The revision deliberately avoids a simple volume crescendo. The dramatic mechanism is a
loss of perceptual stability: the machine is physically slow, while the mind starts to
hear increasingly fast and asymmetric patterns.

### `act01_plan_broken_v01` — «Когда башня отвечает», revision 02

- 82 BPM, 4/4;
- 27 bars / ~79.02 s;
- one-shot Act I finale;
- a familiar contour survives only briefly and already stutters;
- obsessive `D/Eb` and `A/Ab` repetitions become progressively faster;
- irregular war-drum accents stop respecting a stable heroic pulse;
- short dark-brass stabs and high glass alarms interrupt rather than support the harmony;
- two brief panic dropouts break continuity before the score slams back in;
- the final section approaches a hysterical loop but cuts off unresolved instead of cadencing;
- context: `act01_plan_broken`.

This revision is intentionally less "epic failure" and more immediate loss of control:
the player should feel that several bad things are happening at once and nobody has time
to process them.

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

- deterministic NumPy renderers;
- revision 01 renderer remains authoritative for Mad Wizard and tavern;
- `procedural_narrative_music_renderer_v02` is isolated to the revised elevator and Act I finale;
- 48 kHz stereo;
- Ogg Vorbis game masters;
- MIDI and MP3 diagnostics are generated in CI;
- no downloaded samples;
- no external recordings;
- no third-party melodies.

## Revision 02 verified render contracts

`elevator_descent_floor01_v01`:

- Linux Ogg size: 1,077,508 bytes;
- Ogg SHA-256: `3ed4542122c85e865050665b6622055597e19076bc9d2963965393fc9a9e4528`;
- PCM fingerprint: `46e3937b9e02dd93236b7b4db2d92ff493204c07dad6497b1ebe27914bf7d16b`;
- peak: -1.25 dBFS;
- RMS: -14.5526 dBFS.

`act01_plan_broken_v01`:

- Linux Ogg size: 1,304,990 bytes;
- Ogg SHA-256: `36e60f2a92679710c7bbf3f9e6378e378b738cb59be3b2850cef7267bfde3334`;
- PCM fingerprint: `ae789214ed333c97c298a43852ae34f74c042d5acedd7d7c4a96264492f6e3f4`;
- peak: -0.9 dBFS;
- RMS: -15.6652 dBFS.

## Manual acceptance

Before approval:

1. listen to each full track with headphones;
2. listen on an Android phone speaker;
3. verify both looping tracks through at least two complete seams;
4. compare relative loudness against exploration and combat music;
5. confirm the tavern remains positive without becoming comedic;
6. confirm «Ниже света» starts physically controlled but gradually feels mentally unstable and frightening;
7. confirm «Когда башня отвечает» reads as nervous, hysterical and panicked rather than simply dark or epic;
8. verify the Mad Wizard theme is recognizable when its motif mutates in the elevator and finale.

Do not call these tracks final before the in-game check.
