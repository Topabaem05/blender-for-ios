# Changelog

## Unreleased

### Added

- Defined the physical-iPhone full-editor acceptance contract and TDD evidence loop.
- Added a physical-device regression that opens the supplied Blender 5.2 file from iOS Documents,
  saves and reopens it, and round-trips OBJ, PLY, and STL exports.
- Added a synchronized physical-device regression for opening a `.blend` through the iOS Files URL
  delivery path.
- Added exact universal iPhone+iPad package validation and test coverage.
- Added reusable physical-iPhone smoke, reopen, and lifecycle checks for Blender editor behavior.
- Added an opt-in XCUITest target for physical viewport touch verification.
- Added package validation that rejects unresolved Git LFS pointers inside `Blender.app`.
- Added iPad Simulator regressions for viewport touch, Apple keyboard modifiers and shortcuts, and
  the supplied 141 MB `.blend` document lifecycle.
- Added package validation and focused tests for CPython iOS native modules stored as signed
  frameworks with `.fwork` and `.origin` redirects.
- Documented the iOS Python, bundled add-on, wheel, and runtime Extensions support policy.

### Fixed

- Prevented viewport thumbnail rendering from rebinding a Metal framebuffer owned by a no-longer
  active GPU context after an iOS file load.
- Kept the original iOS document URL alive through Blender's asynchronous open event so its
  security-scoped access is started and stopped on the same URL object.
- Corrected the iOS dependency Autoconf environment and target triplets for Python 3.13 builds.
- Copied Python cross-build sysconfig data from its installed, versioned location.
- Isolated iOS dependency discovery from host OpenEXR, OpenImageIO, FFmpeg, and fmt installations.
- Enabled both iPhone and iPad device families for the application and hosted XCTest bundle.
- Fixed legacy dependency CMake policy handling and disabled libheif's unused test build.
- Fixed iOS Imath/OpenEXR public include paths and the final OpenSSL, libffi, and Alembic ABI link.
- Removed host Python from iOS installs, signed installed NumPy extensions, and stopped packaging
  disabled USD/OSL runtime dylibs.
- Placed the hosted XCTest bundle under the Blender app's PlugIns directory for Xcode test builds.
- Made the physical viewport test wait for Blender's Python timer readiness before tapping.
- Restored the packaged brush, node, and startup-template `.blend` payloads from Git LFS.
- Routed this public fork's Git LFS downloads to the official Blender upstream object store.
- Enabled the macOS-style Command keymap conversion when Python reports the iOS platform.
- Made Simulator VBO-backed Metal textures use private mirrored storage, as required by the
  Simulator Metal runtime, without changing the physical-device path.
- Blocked subprocess-based Blender Extension installation and management with a deterministic iOS
  error while retaining bundled add-ons and document scripts.
- Packaged all 19 bundled NumPy extension modules as signed iOS frameworks and rejected loadable
  Python `.so` files left outside `Frameworks`.
- Kept `sys.executable` anchored to the Blender app binary on iOS so CPython's
  `AppleFrameworkLoader` can resolve packaged native modules.
- Selected `Python.framework` only when its binary exists and otherwise retained the available
  static iOS Python library, with an early configure error when neither runtime is present.

Verification updated: 2026-08-12 04:56 KST.
