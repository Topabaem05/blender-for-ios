# Port Log

## 2026-08-12

- Verified five Apple keyboard paths on iPad Simulator: unmodified transform, Shift duplicate,
  Option clear location, Command undo, and Control full-screen toggle.
- Reproduced a Simulator-only `MTLSimBuffer` assertion while drawing the supplied Blender 5.2
  scene and traced it to the runtime requirement that linear textures use private storage.
- Added a private mirror only for shared VBO buffer textures on Simulator and invalidated it after
  partial VBO updates; the physical-device buffer path is unchanged.
- Re-ran the 141 MB open/save/reopen and OBJ/PLY/STL lifecycle successfully, visually inspected the
  full-editor landscape screenshot, and observed no post-fix crash or Metal assertion.
- Re-ran 2/2 UI tests and 10/10 FTL tests. The shader-cache assertion after FTL completion is an
  existing XCTest-host teardown artifact also present in the pre-fix result.
- Recorded that Cycles is not included in this iOS build; the supplied scene displays the expected
  unavailable-engine warning while Workbench remains functional.

## 2026-08-11

- Reproduced a physical-iPhone `SIGABRT` while saving the supplied Blender 5.2 file and traced it to
  `ED_view3d_draw_offscreen_imbuf` restoring a framebuffer after the active Metal context changed.
- Added the minimum context-identity guard and a staged physical-device Documents regression.
- Built and signed a runtime-closed arm64 app, installed it through CoreDevice, and observed the
  supplied 141 MB file open, save, reopen, OBJ/PLY/STL round-trip, and screenshot successfully.
- Confirmed the Blender process remained alive and no new Blender crash report appeared.
- Reproduced the asynchronous iOS document URL boundary and retained the original security-scoped
  URL until Blender's existing `WM_file_read` start/stop calls complete.
- Added a persistent, readiness-synchronized openURL test and observed a Files-visible Documents
  fixture load with its marker intact, autoexec disabled, and the full editor visible.

## 2026-08-10

- Selected `ios/ipad-mvp` as the smallest complete iOS baseline.
- Confirmed the explicit iPad-only gates are the app target, hosted XCTest target, and package validator.
- Reproduced the Python 3.13 configuration blocker and the iOS Autoconf environment failure.
- Repaired the local host build tools without changing product code.
- Built the Python 3.13 runtime closure, NumPy 2.3.4, fmt, Eigen, Abseil, and Ceres for iOS arm64.
- Reproduced and removed host-library leakage from OpenEXR, OpenImageIO, FFmpeg, and fmt discovery.
- Reproduced the iPad-only package and Xcode settings, then made the exact universal family contract
  pass 11 packaging tests and generated Xcode build-setting checks.
- Rebuilt the OpenImageIO 3.1.7, OpenEXR 3.4.3, Imath 3.2.2, OpenSSL 3.5.2, libffi 3.5.2, and
  Alembic 1.8.3 iOS boundaries required by the final Blender link.
- Removed host Python from the app install, fixed install-time NumPy signing, and excluded disabled
  USD/OSL runtime dylibs so the packaged dependency graph closes without missing `@rpath` edges.
- Signed the app and all 39 nested code objects with one development identity, installed it on the
  connected iPhone, and observed a successful cold launch.
- Ran physical-device smoke scripts for editor/Python/NumPy/save/Workbench render/UI screenshot,
  process-restart reopen, and background/foreground state preservation.
- Added an opt-in physical-device UI test target. Its first `build-for-testing` run exposed and fixed
  the hosted XCTest output-directory mismatch.
- Fixed the UI test's unsupported foreground-wait selector and forced its `.xctestrun` to install the
  signed staging app instead of the incomplete raw Xcode product.
- Confirmed Xcode strips quote characters from iOS launch expressions before Blender receives them.
  Reverted an ineffective GHOST argv-copy attempt and replaced the test probe with a quote-free
  expression.
- Replaced a fixed startup delay with a Darwin readiness notification from Blender's first Python
  timer tick. The physical tap then produced `selected=true` in the app report and a selected-Cube
  screenshot.
- Found 18 packaged `.blend` files that were Git LFS pointers, restored their payloads from upstream,
  and verified the physical launch log contains no unrecognized asset-format warnings.
- Added a package regression that rejects Git LFS pointers inside `Blender.app`; all 12 tests pass.
- GitHub rejected uploading the 18 inherited objects to a public fork, so `.lfsconfig` now routes
  LFS downloads to the official Blender upstream store that supplied the verified payloads.
