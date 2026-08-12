# Progress

- Branch: `ios/universal-editor` from `ios/ipad-mvp`.
- Connected physical iPhone and Xcode device SDK confirmed.
- Required release LFS objects and pinned macOS/iOS dependency submodules verified.
- RED: Blender 5.1 requires Python 3.13 while the pinned iOS dependency bundle contains 3.11.
- RED: the current dependency generator exports a macOS deployment target while compiling for iOS.

The official iOS Python 3.13 dependency build is GREEN.

- GREEN: avoid macOS-only deployment variables for Apple mobile cross-compilation and identify the
  Autoconf host as arm64 Darwin while detecting the native build machine.
- Python 3.13 compiled and installed; its final sysconfig copy now uses the installed path.
- Generated and verified iOS builds of fmt, Eigen, Abseil, Ceres, and NumPy; bundled the pure-Python
  requests/certificate runtime from the pinned iOS dependency set.
- CMake now resolves OpenEXR, OpenImageIO, FFmpeg, fmt, Rubberband, Eigen, and Ceres without
  Homebrew or Conda target-library contamination.
- RED then GREEN: package validation now requires the exact integer device-family set `{1, 2}`.
- Xcode reports `TARGETED_DEVICE_FAMILY = 1,2` for both Blender and BlenderFTLTests.

The signed universal editor and physical-iPhone workflow are GREEN.

- Rebuilt OpenImageIO/OpenEXR/Imath plus the OpenSSL, libffi, and Alembic ABI boundaries for iOS
  arm64, then completed the Blender application link.
- Installed a development-signed app with a closed `@rpath` dependency graph and 39 verified nested
  signatures on the connected iPhone.
- Cold launch remained alive, and the device smoke test completed `bpy` editing, NumPy execution,
  `.blend` saving, a Workbench render, and a UI screenshot.
- A new process reopened the saved file and preserved the edited cube coordinates.
- The same process survived a real Settings-app background transition and produced a new screenshot
  after returning to the foreground.
- A physical-device XCUITest now waits for a Blender Python readiness notification, taps the 3D
  viewport, and records `selected=true` for the Cube from inside the running app.
- Restored 18 Git LFS-backed brush, node, and startup-template `.blend` payloads from the upstream
  Blender LFS store. The installed app starts with zero asset-format warnings.
- RED then GREEN: package validation rejects Git LFS pointer text inside `Blender.app`; all 12
  packaging tests pass.
- The public fork now resolves its inherited LFS payloads from the official Blender upstream object
  store instead of the empty GitHub fork endpoint.
- RED: saving the supplied Blender 5.2 file aborted while an offscreen thumbnail path rebound a
  framebuffer from the GPU context that had been active before the file load.
- GREEN: offscreen viewport drawing now restores a framebuffer only when its owning GPU context is
  still active. A freshly built and signed app opened the 141,369,967-byte input, saved and reopened
  141,884,312 bytes, round-tripped OBJ/PLY/STL, and remained alive with no new crash report.
- RED: the iOS document callback converted its security-scoped `NSURL` to a path before queuing the
  asynchronous GHOST file-open event, so the later scope request used a different URL object.
- GREEN: GHOST now retains the original URL until `WM_file_read` balances access. After observer
  readiness, a Files-visible Documents URL opened the marked 97,004-byte fixture, kept autoexec off,
  and produced a 518,706-byte screenshot on the connected iPhone.
- RED then GREEN: UIKit delivered Shift, Control, Option, and Command correctly, but XCTest's Enter
  and Escape synthesis corrupted modal state and iOS omitted macOS-style Command keymaps. Native
  Space confirmation plus the iOS keymap conversion made all five observable shortcuts pass.
- RED: the supplied 141 MB scene aborted on iPad Simulator because Simulator Metal rejects linear
  textures backed by a shared VBO.
- GREEN: Simulator-only private VBO mirrors preserved host-visible uploads and rendered the scene.
  The app opened 1 scene with 343 objects and 202 meshes, saved and reopened 141,304,004 bytes,
  round-tripped OBJ/PLY/STL, produced an 871,219-byte screenshot, and remained alive.
- GREEN after the Metal fix: 2/2 touch and Apple-keyboard UI tests and 10/10 input/pressure tests
  passed. The FTL host's shader-cache assertion occurs only after XCTest forces process exit and is
  also present in the pre-fix result.
- RED then GREEN: iOS Extension management previously entered its subprocess path. The shared JSON
  command runner now returns one deterministic fatal message on iOS, while `bpy`, NumPy, and the
  bundled SVG add-on remain usable.
- RED then GREEN: package validation allowed loadable Python `.so` files. The install step now moves
  all 19 NumPy binaries into signed frameworks, writes CPython `.fwork`/`.origin` redirects, and
  validates a package containing 74 loadable Mach-O files with no remaining Python `.so` files.
- RED: CPython's `AppleFrameworkLoader` crashed on the first NumPy import because Blender replaced
  the missing standalone iOS Python executable with `sys.executable = None`.
- GREEN: iOS Python initialization now uses the Blender app binary as `sys.executable`. A fresh
  Simulator run imported NumPy, enabled the bundled add-on, exercised the Extension policy, wrote a
  2,091,108-byte Blender screenshot, and had zero traceback, import, dyld, or resource-warning log
  patterns.
- RED: the device build reached its final link but the Apple platform configuration replaced the
  discovered static Python archive with a `Python.framework` path that did not exist in the device
  dependency overlay.
- GREEN: availability-aware Python runtime selection keeps the Simulator framework path and uses the
  device static archive when needed. All 27 testlab tests pass, both generated Xcode projects select
  the intended input, and the device build exits successfully.
- GREEN before device install: CMake staging converted 19 native modules with zero remaining Python
  `.so` files; validator checked 44 loadable Mach-O files, deep signing and provisioning matched,
  and all 383 Python symbols required by the extension frameworks are exported by the app.
- Earlier connection gate: one CoreDevice install attempt found the paired iPhone unavailable, and
  an independent Xcode discovery refresh returned the same device-preparation state. No second
  install or device reboot was attempted.

The current signed device and physical-iPhone checkpoint are GREEN.

- `build-for-testing` completed 4,250 compile units; the staged signed app passed validation for 55
  loadable Mach-O files, and testlab passed 54/54 checks.
- The signed staging app installed on the connected iPhone and remained alive for a 30-second cold
  launch. Smoke QA edited the scene, imported NumPy, saved a `.blend`, and rendered with Workbench;
  relaunch QA reopened the saved state.
- Python 3.13, `bpy`, NumPy, a Documents `.py` script, and a bundled add-on passed. Runtime Blender
  Extension management remained blocked by the iOS policy.
- Limited Workbench, Eevee, and Cycles render checks passed on the phone.
- The supplied 141,369,967-byte `.blend` opened with autoexec disabled, saved, exported and
  reimported OBJ/PLY/STL, and reopened after relaunch with autoexec still disabled.
- Background/foreground preserved the same process, and the iOS payload callback opened its file.
- RED: the physical software-keyboard path crashed in `block_to_window_fl` while converting a
  button block with a stale region.
- GREEN: `interface_handlers.cc` now uses the active button data's region. On the connected iPhone,
  the native text field appeared and accepted Unicode text, Delete, and Done without crashing.
- GREEN: physical rotation, viewport tap, and Shift/Option/Command/Control modifier UI regressions
  each reported one passing test and zero failing tests.
- GREEN: a new signed arm64 staging app passed validation for 55 loadable Mach-O files, deep code
  signing, installation, and the complete 54/54 testlab run.
- RED then GREEN: mutation cases showed that `.fwork` presence alone could not prove a usable native
  module. Validation now follows each marker to its framework executable, requires the matching
  `.origin` redirect, and confirms the executable is loadable Mach-O.
- GREEN: host-authorized strict and deep code-signing validation passed. The sandbox trust failure
  was isolated as an execution-environment restriction rather than a package-signing failure.

Current loop: expose the software-keyboard dialog/probe notification after four locked attempts and
freshly run the new iPad Simulator cases. No new app crash was observed in those locked attempts.
App Store P0 remains gated by the release-profile user-code restriction, third-party open-in-place,
Blender trademark permission, and GPL distribution review.
