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
- Complete: the current device `build-for-testing` compiled 4,250 units; the signed staging app
  passed validation across 55 loadable Mach-O files, and testlab passed 54/54 checks.
- Complete: the latest signed arm64 staging app again passed validation across 55 loadable Mach-O
  files, host-authorized strict/deep code-signing validation, physical installation, and 54/54
  full testlab checks. A sandbox trust failure was isolated from this result.
- Complete: every `.fwork` marker is now validated through its framework executable and matching
  `.origin` redirect, including loadable Mach-O verification. RED mutation cases cover broken
  targets, missing or mismatched redirects, and invalid executables.
- Complete on the connected iPhone: a 30-second cold launch, scene edit, NumPy, `.blend` save,
  Workbench render, process-restart reopen, and same-PID background/foreground preservation.
- Complete on the connected iPhone: Python 3.13, `bpy`, NumPy, a `.py` script stored in Documents,
  a bundled add-on, the runtime Extensions block, and limited Workbench, Eevee, and Cycles renders.
- Complete on the connected iPhone: readiness-synchronized XCUITest viewport tap followed by an
  in-process `bpy` Cube selection assertion and visual screenshot verification.
- Complete on the connected iPhone: the supplied 141 MB Blender 5.2 file opens with auto-execution
  disabled, saves and reopens in Documents, round-trips OBJ, PLY, and STL, and reopens after an app
  relaunch. The observed input size was 141,369,967 bytes.
- Complete on the connected iPhone: a Files-visible Blender Documents URL opens an identified
  `.blend` fixture through `UIApplication` and GHOST with auto-execution disabled.
- Complete on the connected iPhone: rotation, viewport tap, and Shift, Option, Command, and Control
  modifier UI regressions each passed with one passing test and zero failing tests.
- Fixed and manually observed on the connected iPhone: `interface_handlers.cc` now uses the active
  button data's region for software-keyboard window conversion. The pre-fix path crashed in
  `block_to_window_fl`; the post-fix native text field accepted Unicode text, Delete, and Done
  without crashing.
- Complete: all packaged brush, node, and startup-template LFS payloads are materialized; package
  validation rejects pointer text and the physical launch log has zero asset-format warnings.
- Previous iPad Simulator baseline: 10 input/pressure tests, viewport touch, Apple keyboard
  shortcuts, full-editor landscape UI, and the supplied 141 MB file open/save/reopen plus
  OBJ/PLY/STL round-trips. The post-fix app remained alive with no Metal assertion.
- Previous iPad Simulator baseline: Python 3.13.9, `bpy`, NumPy, and a bundled SVG add-on run after
  all 19 NumPy native modules are converted to signed frameworks. Runtime Extension management
  exits with the documented iOS error instead of attempting a subprocess.
- Pending: after four attempts, the software-keyboard end-to-end notification remains locked on
  test probe/dialog exposure; this is not a newly observed app crash. The new iPad Simulator UI
  cases still need a fresh run.
- App Store P0 blockers: enforce the user-code policy in the release profile, finish or disable
  third-party open-in-place, and resolve Blender trademark and GPL distribution requirements.
- Known platform debt: UIKit reports that scene lifecycle adoption will become mandatory and that
  the current full-screen plist key will be ignored in a future iOS release.
- Pending outside the available hardware: physical-iPad regression before universal release support.
