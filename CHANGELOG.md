# Changelog

## Unreleased

### Added

- Defined the physical-iPhone full-editor acceptance contract and TDD evidence loop.
- Added exact universal iPhone+iPad package validation and test coverage.
- Added reusable physical-iPhone smoke, reopen, and lifecycle checks for Blender editor behavior.
- Added an opt-in XCUITest target for physical viewport touch verification.
- Added package validation that rejects unresolved Git LFS pointers inside `Blender.app`.

### Fixed

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

Verification updated: 2026-08-10 23:40 KST.
