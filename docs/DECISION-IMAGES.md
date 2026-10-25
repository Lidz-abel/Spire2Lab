# Original-game decision images

Implementation contract, 2026-10-25. This document specifies the next ordered
deliverable; it is not evidence that capture is installed or verified.

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
