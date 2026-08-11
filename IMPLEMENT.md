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
- Pending: a third-party Files-provider permission regression and the iOS
  scripting/add-on/Extensions policy.
- Known disabled feature: Cycles is not included in the current iOS build; files selecting it show
  an unavailable-engine warning and fall back to the enabled Workbench path for QA.
- Pending outside the available hardware: physical-iPad regression before universal release support.
