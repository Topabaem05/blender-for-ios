# Implementation Loop

For each port boundary:

1. Record an observable failing test or device scenario.
2. Apply the smallest production change that addresses the confirmed cause.
3. Run the focused test, then the relevant build.
4. Exercise the result on the connected physical iPhone.
5. Update the contract evidence and create a checkpoint commit only while GREEN.

No runtime workaround is accepted without a regression test or a reproducible device check.

## Current status

- Complete: universal iPhone+iPad target configuration, iOS dependency closure, final application
  link, install-stage runtime closure, nested signing, and physical-iPhone installation.
- Complete on the connected iPhone: cold launch, editor/Python/NumPy execution, `.blend` save,
  Workbench render, process-restart reopen, and background/foreground state preservation.
- Complete on the connected iPhone: readiness-synchronized XCUITest viewport tap followed by an
  in-process `bpy` Cube selection assertion and visual screenshot verification.
- Complete on the connected iPhone: the supplied 141 MB Blender 5.2 file opens with auto-execution
  disabled, saves and reopens in Documents, and round-trips OBJ, PLY, and STL without a crash.
- Complete on the connected iPhone: a Files-visible Blender Documents URL opens an identified
  `.blend` fixture through `UIApplication` and GHOST with auto-execution disabled.
- Complete: all packaged brush, node, and startup-template LFS payloads are materialized; package
  validation rejects pointer text and the physical launch log has zero asset-format warnings.
- Complete on iPad Simulator: 10 input/pressure tests, viewport touch, Apple keyboard shortcuts,
  full-editor landscape UI, and the supplied 141 MB file open/save/reopen plus OBJ/PLY/STL
  round-trips. The post-fix app remained alive with no Metal assertion.
- Complete on iPad Simulator: Python 3.13.9, `bpy`, NumPy, and a bundled SVG add-on run after all 19
  NumPy native modules are converted to signed frameworks. Runtime Extension management exits with
  the documented iOS error instead of attempting a subprocess.
- In progress: a fresh device build and signed staging app now contain 19 native-module frameworks,
  pass package/signing validation, and export every Python symbol those modules require. The first
  install attempt was stopped by Xcode reporting the paired iPhone unavailable; raw Xcode products
  were not installed and no repeated install was attempted while the connection remained down.
- Pending: a third-party Files-provider permission regression. Files-visible Blender Documents
  import and export are already complete.
- Known disabled feature: Cycles is not included in the current iOS build; files selecting it show
  an unavailable-engine warning and fall back to the enabled Workbench path for QA.
- Known platform debt: UIKit reports that scene lifecycle adoption will become mandatory and that
  the current full-screen plist key will be ignored in a future iOS release.
- Pending outside the available hardware: physical-iPad regression before universal release support.
