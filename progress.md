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

Current loop: compile and sign the universal Blender iOS application.
