# iPad Firebase Test Lab Design

**Date:** 2026-08-09

**Repository:** `Topabaem05/blender-for-ios`

**Development branch:** `ios/ipad-mvp`

## Objective

Make the iPad port installable on iPad (10th generation) running iPadOS 16.6 or later and add the
smallest useful XCTest package path for Firebase Test Lab. The package must exercise code from the
real Blender app target and must not be replaced by a fake sample app.

## Revised Platform Contract

- The minimum supported device is iPad (10th generation).
- The minimum operating system is iPadOS 16.6.
- Device and Simulator deployment targets are both exactly `16.6`.
- Xcode `TARGETED_DEVICE_FAMILY` remains exactly `2`.
- The build remains arm64-only for iOS devices and Apple Silicon Simulators.
- APIs introduced after iPadOS 16.6 require an availability guard and a 16.6 fallback.
- iPhone remains deferred until the iPad stability gates pass.

The previous iPadOS 18 / M1 iPad contract is superseded by this document. iPad (10th generation)
is now the performance and memory floor, so Workbench is the first rendering gate. EEVEE remains an
MVP goal only after it survives the minimum-device memory and thermal checks.

## Considered Test Architectures

### Selected: CMake-hosted XCTest bundle

Use CMake's `FindXCTest` module to create `BlenderFTLTests` with the generated `Blender.app` target
as its test host. Compile the existing `GHOST_IOSInput.cc` into the test bundle and run its pressure
contract through XCTest on the device. A package that reaches the test methods has installed and
launched the real app host and loaded the real test bundle.

This keeps the generated Xcode project authoritative and avoids checking in a hand-maintained
`.pbxproj`. CMake 4.0.1 or newer is required because it contains the Xcode 16 `FindXCTest` fix.

### Rejected: separate checked-in Xcode test project

This gives direct scheme control but duplicates bundle IDs, signing, deployment targets, and target
references from the CMake build. The two project definitions can drift.

### Rejected: standalone Swift Package test harness

This can produce a small XCTest package but does not prove that the Blender app installs or launches.
It would test a sample harness rather than the port.

## Components

### Platform and signing configuration

The existing Apple CMake files own the `16.6` deployment floor and iPad-only device family. The app
Info.plist uses `$(PRODUCT_BUNDLE_IDENTIFIER)`, backed by a CMake cache variable, so a developer can
use a bundle identifier owned by their Apple team without editing source.

### `BlenderFTLTests`

The device XCTest bundle is opt-in through `WITH_IOS_TESTLAB=ON`. It is added only after the Blender
app target exists and is hosted by that target at
`Blender.app/PlugIns/BlenderFTLTests.xctest`. The first device tests cover the already TDD-protected
Pencil pressure contract:

- half force maps to `0.5`;
- a non-positive maximum maps to `0.0`;
- negative force clamps to `0.0`;
- force above the maximum clamps to `1.0`.

The host dependency makes app startup part of the test precondition, but these tests do not claim
viewport rendering, document I/O, Apple Pencil hardware injection, or long-session stability.

### Package validator

`package_xctest.py` consumes an Xcode `DerivedData/Build/Products` directory and writes one ZIP. It
accepts only:

- one `Debug-iphoneos/` product directory;
- one device `.xctestrun` file for `iphoneos16.6-arm64`;
- a `Blender.app` whose generated Info.plist reports `MinimumOSVersion=16.6` and
  `UIDeviceFamily=[2]`;
- a hosted `Blender.app/PlugIns/BlenderFTLTests.xctest` containing its Info.plist and
  `BlenderFTLTests` executable.

The ZIP root contains exactly the product directory and `.xctestrun` file. Extra root products,
missing or unhosted test artifacts, ambiguous inputs, Simulator artifacts, iPhone-capable apps, and
wrong-deployment artifacts fail closed. Source executable modes are preserved in the ZIP.

### macOS build wrapper

`build_xctest.sh` runs the generated `blender` app scheme with
`xcodebuild ... build-for-testing`. That scheme contains `BlenderFTLTests` as a hosted Testable.
The wrapper requires the test bundle inside `Blender.app/PlugIns`, verifies the app and hosted test
signatures and both arm64 executables, and invokes the package validator. It refuses to run outside
macOS or without the required Apple tools.

## Artifact Flow

```text
CMake 4.0.1+ and Xcode 16+
        |
Blender.xcodeproj with blender scheme
        |  (hosted BlenderFTLTests Testable)
        |
xcodebuild build-for-testing (generic iOS device)
        |
DerivedData/Build/Products
        |
signature, architecture, platform contract checks
        |
BlenderFTLTests.zip
        |
Firebase Test Lab device matrix
```

Firebase requires a Generic iOS Device `build-for-testing` result containing `Debug-iphoneos/` and
the generated `.xctestrun` at the ZIP root. The live device catalog is queried before submission;
model and version IDs are not hard-coded because Firebase treats them as mutable catalog data.

## Firebase Matrix Policy

- Required first gate: iPad (10th generation), iPadOS 16.6, landscape.
- Compatibility gate: the same model on the newest Test Lab iPadOS version available to the project.
- Query `gcloud firebase test ios models list` and `versions list` immediately before each run.
- Do not silently substitute an iPhone or a different iPad if the required pair is unavailable.
- Do not claim Apple Pencil coverage from Test Lab; Pencil hardware remains an owned-device gate.

## GitHub Actions Policy

No push, pull-request, or scheduled workflow is added. A manual packaging workflow may be introduced
only after the local/macOS command is proven and only when no signed macOS builder is available. It
must use `workflow_dispatch`, upload only the requested XCTest ZIP, and never run automatically.

## Verification Boundaries

This Linux workspace can run the package validator's behavior tests, the existing pure C++ tests,
shell syntax checks, and focused diffs. It cannot generate or sign an Apple device XCTest package.
The first valid ZIP therefore requires a macOS host with CMake 4.0.1+, Xcode 16+, the iOS dependency
bundle, signing configuration, and the repository's LFS assets.

## Acceptance Criteria

- The app and test deployment targets are exactly iPadOS 16.6.
- The app remains iPad-only and arm64-only.
- `BlenderFTLTests` is hosted by the generated Blender app target.
- The package validator is developed RED-GREEN and rejects invalid package inputs.
- A signed macOS/Xcode build produces one Firebase-compatible ZIP.
- The live Firebase catalog confirms the requested iPad/model pair before submission.
- GitHub Actions remain unused unless the explicit manual-build exception is invoked.

## Primary References

- [Firebase: Run an XCTest](https://firebase.google.com/docs/test-lab/ios/run-xctest)
- [Firebase: Test with gcloud](https://firebase.google.com/docs/test-lab/ios/command-line)
- [CMake: FindXCTest](https://cmake.org/cmake/help/latest/module/FindXCTest.html)
- [CMake 4.0.1 Xcode 16 fix](https://discourse.cmake.org/t/cmake-4-0-1-available-for-download/13909)
