# Port Log

## 2026-08-13

- Reproduced the physical software-keyboard crash in `block_to_window_fl` and traced it to window
  conversion using a region that did not belong to the active button data.
- Updated `source/blender/editors/interface/interface_handlers.cc` to use the active button data's
  region. The post-fix native text field appeared on the connected iPhone and accepted Unicode
  text, Delete, and Done without an app crash.
- Passed the physical rotation, viewport tap, and Shift/Option/Command/Control modifier UI
  regressions; each reported one passing test and zero failing tests.
- Kept the software-keyboard end-to-end notification case locked after four attempts. The remaining
  issue is test probe/dialog exposure, not a newly observed app crash.
- Validated a new signed arm64 staging app across 55 loadable Mach-O files, deep code signing, and
  physical installation, and completed the full 54/54 testlab run.
- Hardened `.fwork` validation to require the referenced framework executable, a matching `.origin`
  redirect, and a loadable Mach-O executable. RED mutations confirmed each invalid chain is rejected.
- Passed host-authorized strict and deep code-signing checks. Isolated the sandbox trust failure as
  an environment restriction, not a signed-package defect.
- Kept the fresh iPad Simulator run and App Store P0 gates pending.

## 2026-08-12

- Completed the device `build-for-testing` pass across 4,250 compile units, staged the signed app,
  validated 55 loadable Mach-O files, and completed 54/54 testlab checks.
- Installed that staged app on the connected iPhone, observed a 30-second cold launch, and passed
  scene editing, NumPy, `.blend` save, Workbench render, and relaunch/reopen smoke checks.
- Passed Python 3.13, `bpy`, NumPy, a Documents `.py` script, and a bundled add-on; runtime Extension
  management remained blocked as required by the iOS policy.
- Passed limited Workbench, Eevee, and Cycles render checks.
- Opened the supplied 141,369,967-byte `.blend` with autoexec disabled, saved it, exported and
  reimported OBJ, PLY, and STL, and reopened the result after relaunch with autoexec still disabled.
- Preserved the same process through background/foreground and passed the iOS payload URL callback.
- Left the software-keyboard UI case locked and the fresh new iPad Simulator cases pending.
- Recorded the remaining App Store P0 gates: release-profile user-code enforcement, third-party
  open-in-place, Blender trademark permission, and GPL distribution review.
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
- Reproduced the iOS Extension manager entering a subprocess-only path and added a shared iOS guard
  that leaves bundled add-ons and user scripts available.
- Added TDD coverage for CPython iOS framework redirects and package rejection of loadable Python
  `.so` files outside `Frameworks`.
- Converted 19 NumPy native modules to signed frameworks, verified `.fwork` and `.origin` counts,
  deep code signing, and 74 loadable Mach-O files.
- Traced a Simulator NumPy import failure to Blender setting `sys.executable` to `None`; on iOS it
  now points to the already initialized Blender app binary used by `AppleFrameworkLoader`.
- Completed a clean fresh-run Simulator QA for Python 3.13.9, NumPy, the bundled SVG add-on, the
  runtime Extension policy, and a Blender-rendered screenshot. The app remained alive with no
  traceback, import, dyld, or resource-warning patterns.
- Isolated existing UIKit scene-lifecycle and full-screen plist deprecation warnings as remaining
  platform work rather than changing them inside the Python packaging checkpoint.
- Removed only reconstructable Blender build caches after the device build exhausted disk space;
  preserved the completed Simulator app, QA evidence, and active device objects.
- Reproduced a final device-link failure caused by forcing a missing `Python.framework`, added a RED
  regression, and selected the available framework or static Python runtime at configure time.
- Completed 27/27 testlab tests, both Simulator/device CMake branch checks, a successful device
  build, and a signed staging package with 19 arm64 iPhoneOS extension frameworks.
- Verified the staged app's 44 loadable Mach-O files, deep signature, provisioning match, reciprocal
  loader markers, and 383/383 required Python symbols before touching the phone.
- Kept the first failed install isolated to Xcode's unavailable-device state. The app was not
  launched, the install was not repeated, and the phone was not rebooted or otherwise reset.

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
