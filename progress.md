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

Current loop: final regression, checkpoint push, and independent evaluation.
