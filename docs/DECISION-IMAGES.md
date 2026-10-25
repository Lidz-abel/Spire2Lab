# Original-game decision images

Implementation contract, 2026-10-25. Transport, storage and live/replay UI are
implemented and tested. The installed Windows Mod and a fresh original battle
with 12 bound images are now verified; see [the evidence](DECISION-IMAGES-VALIDATION.json).

## Association and information boundary

Capture the actual Godot root viewport, never a Linux reconstruction of the
game. Request it only after a confirmed, settled observation and before issuing
the next action. The transport must bind an image to the exact game process,
game assembly, Mod assembly and `lab_state_token`. The laboratory adds its run
ID, decision ID and canonical public-observation digest. Images belong to
inspection and replay; the current semantic planner receives neither image
bytes nor raw privileged bridge states.

The bridge accepts a read-only request with the expected instance and token.
It checks execution idle and the settlement gate, waits for a rendered frame,
and checks again. A changed token, restarted process, unresolved action or
missing frame rejects capture. Readback and PNG encoding run on the game
thread. The reply contains PNG bytes, SHA-256, dimensions, frame counter,
capture time and the verified binding. A request may fail while the game is
minimized or rendering is suspended; report that failure without substituting
an older picture. This is a decision-boundary still image, not a video stream
or a guarantee that every cosmetic animation has stopped.

## Storage and presentation

- Validate the expected binding, PNG signature, dimensions, decoded byte limit
  and content hash before storing. Keep PNG files and raw capture data under
  ignored `artifacts/`; never publish game assets in Git.
- Write an immutable image record into the same hash-chained laboratory trace
  before its associated action. Use content-addressed image storage and an
  explicit capture-failure record. Do not append anything after session close.
- The live panel shows only the picture whose run/decision/digest matches its
  displayed observation. Label it as an original capture and show association
  details. Simulator sessions do not display an original-game image.
- Replay reads the stored image record for that frame and performs no game
  request. Missing or changed bytes show an unavailable state. Never display
  the previous frame's image under the next decision.
- The server resolves only validated identifiers within its artifact directory,
  verifies the stored hash, and serves PNG with an explicit content type. No
  caller-provided filesystem paths or arbitrary external image URLs.
- Capture errors do not become gameplay transitions or successful evidence.
  Normal semantic sessions remain usable with an explicit unavailable image;
  image acceptance runs require every declared boundary to capture correctly.

## Verification

Test stale instance/token/build, changed state during capture, busy execution,
invalid/corrupted/oversized PNG, path containment, missing replay files and
simulator sessions. Use fake images only for these mechanics tests and label
them synthetic. Rebuild the attributed pinned Mod with the new extension,
archive the previous package, then verify the installed fingerprint on Windows.
Run a fresh original battle, preserve a picture for each declared boundary,
inspect real images, and verify live/replay association with zero replay action
requests. Compilation and synthetic tests alone cannot complete this item.

The original phase-one captures retain their old Mod fingerprint. Rebuilding
the bridge must not rewrite those captures or imply the new bridge inherited
their live certification. Audit historical evidence against its archived build
and report fresh image evidence separately.

## Current implementation and evidence

The read-only `GET /api/v1/lab/image?instance=...&token=...` endpoint uses
`RenderingServer.FramePostDraw`, rejects concurrent image requests and has a
five-second deadline. The PNG is capped at 16 MiB and 16,777,216 pixels. The
Python receiver checks chunk CRCs, bounded decompression, frame counter,
process/build/token, dimensions and hash before content-addressed storage.
The server also checks each image's run/decision/public-observation digest
against the hash-chained trace before serving bytes. Images are absent from
planner inputs. Missing capture is explicit and does not fabricate a transition.

175 tests passed, including the production C# association gate compiled without
the game. Synthetic browser checks passed for valid display, clearing the old
image after capture failure, missing/corrupt bytes, mobile layout and replay
without mutation requests. These checks used synthetic PNGs, not game pixels.
Local evidence: `artifacts/phase2-v2/full-image-tests.xml` and
`artifacts/phase2-v2/image-fixture/browser-report.json`.

The compiled Mod SHA-256 is
`b6c1a3ab3ca649be06a3ec0aeb2a995d4aa82daedf5d95b51ce87a8773e5c61b`.
It targets the unchanged game assembly recorded in the private build manifest.
Install that package from this phase-two checkout on Windows, retain the
existing port configuration, then verify the actual running fingerprint and
real decision captures. The old phase-one checkout and Mod package remain
available. Historical 60+1 evidence was last audited before this bridge change;
the current-bridge acceptance cache is therefore stale, as intended.

API references: Godot's [viewport texture readback](https://docs.godotengine.org/en/stable/classes/class_viewport.html#class-viewport-method-get-texture)
and [post-draw signal](https://docs.godotengine.org/en/stable/classes/class_renderingserver.html#class-renderingserver-signal-frame-post-draw).
The [Godot 4.5 rendering server source](https://github.com/godotengine/godot/blob/4.5/servers/rendering/rendering_server_default.cpp)
was inspected to check post-draw dispatch; no engine code was copied. Compilation
against the user's GodotSharp DLL checks API availability, not live capture.

## Installed verification

The user installed and restarted the image-enabled Mod. Its actual hash matched
`b6c1a3ab...`; the game assembly and experiment profile also matched. A fresh
Nibbit seed-1 hierarchical-search battle completed 11 actions at 74 HP, with
12 original 3072×1728 viewport images including the terminal reward screen.
Every image matched its private capture token, instance/build, laboratory run,
decision, public-observation digest, dimensions and content hash. Actor-state
comparison and policy replay passed. All twelve browser replay frames matched;
desktop/mobile and live checks recorded zero mutation requests and JS errors.
Old-token and wrong-instance image requests returned 409 without changing game
state or the last action. These are real Windows captures, kept private.

The opening image was visually inspected and includes a turn-start banner.
Semantic settlement does not promise cosmetic animations have finished. This
verification is one debug-staged starter battle, not a full-act reference.
