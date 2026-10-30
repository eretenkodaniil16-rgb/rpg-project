# The Living Scroll V3 — no download needed

This is an **isolated development branch**. Nothing here changes RPG runtime or the `main` branch.

## What is already in GitHub

- `generate_assets.py`: reproducible artistic fallback layers, using Pillow and NumPy.
- `blender_scene.py`: animated 2.5D scene, Blender camera, procedurally animated birds, scroll geometry and material keyframes.
- `.github/workflows/living-scroll-v3-ci.yml`: automatically installs a verified Blender **5.2.0 LTS** binary, Python 3.12 + pinned Pillow/NumPy, headless rendering dependencies and FFmpeg.
- Workflow automatically renders **six preview PNGs** on a push to this development branch, and saves an editable `.blend` file.
- Optional **workflow_dispatch → render_mode=full** renders 288 frames and encodes a 12-second 720x1280 MP4.

**No ZIP download, phone upload, premium Blender addons or Gemini/vidIQ credits are required.**

## Crucial artistic quality caveat

The original 17 MB V3 artwork ZIP could not be transferred into GitHub automatically from the ChatGPT file workspace. Rather than block the entire project, the CI pipeline now generates replacement procedural artistic textures itself. This is a functional fallback, **not a pixel-perfect copy of the more elaborate original reference art**. Once a reliable binary-artifact transfer route is available, the authored source art can replace these fallback images without changing the Blender scene API.

## Dependencies

| Component | Purpose | Provisioning |
|---|---|---|
| Blender 5.2.0 LTS | 3D scene, EEVEE, camera, materials, animation | Pinned Linux download and verified SHA256 |
| Python 3.12 | PNG assets pipeline | actions/setup-python |
| Pillow 11.3.0 | Drawing and image operations | pip |
| NumPy 2.2.6 | Paper texture and noise | pip |
| Xvfb, OpenGL libraries | Headless Blender UI/EEVEE context | apt |
| FFmpeg | Optional MP4 encoding of 288-frame render | apt |

Grease Pencil, Geometry Nodes, Blender compositor and shader nodes are bundled in Blender itself; no extension marketplace install is necessary for the current scene. Avoid installing unrelated plugins (BlenderKit, external Render Farms, unknown MCP extensions) without a concrete need and dependency review.

## View the result from a phone

1. Open the GitHub [Actions workflow](https://github.com/eretenkodaniil16-rgb/rpg-project/actions/workflows/living-scroll-v3-ci.yml).
2. Open the newest run from branch `art/living-scroll-v3-blender`.
3. Check the job status and download `living-scroll-v3-<run-id>-<attempt>` under **Artifacts** (contains `.blend`, six previews, logs).
4. To render the full MP4, open **Run workflow**, select branch `art/living-scroll-v3-blender`, set `render_mode=full`, and confirm. Full renders consume GitHub Actions minutes.

## Remaining work

1. Verify a successful real Blender run in GitHub Actions; syntax validation alone is insufficient.
2. Inspect the six frames for layout/alpha problems, then improve continuity and shading.
3. Replace fallback paintings with higher-quality master art in the asset pipeline (without modifying scene IDs).
4. Only then execute a full MP4 render.
