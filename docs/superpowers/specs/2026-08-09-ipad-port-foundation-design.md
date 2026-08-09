# Blender for iPad Port Foundation Design

**Date:** 2026-08-09

**Repository:** `Topabaem05/blender-for-ios`

**Development branch:** `ios/ipad-mvp`

## Objective

Establish a stable, testable foundation for an iPad-first Blender port without changing the
repository's `main` branch. The first milestone narrows the existing universal iOS configuration to
an iPad-only, iPadOS 18-or-newer build contract. Later milestones will stabilize input, files,
lifecycle handling, rendering, and Apple Pencil support. iPhone work begins only after the iPad port
has passed its stability gates.

## Source and Branch Strategy

- Keep `main` unchanged as the current Blender upstream mirror.
- Keep `ios/base-5.1.2` fixed at commit
  `a1de44dd54af75a4c8c4a29a5fed2a1334a87446`, the official Blender iOS 5.1.2 baseline.
- Make all port changes on `ios/ipad-mvp`.
- Forward-port to a Blender LTS branch only after the iPad baseline builds and its host tests pass.
- Do not rewrite either `main` or `ios/base-5.1.2`.

## Product Scope

### First iPad MVP

- Target M1 iPad hardware with 8 GiB memory or newer.
- Support iPadOS 18 or newer.
- Build for arm64 physical devices and arm64 iOS Simulator.
- Open, save, and recover `.blend` documents.
- Support keyboard, mouse, trackpad, basic touch, and Apple Pencil input.
- Support selection, transform, basic mesh editing, Workbench, and EEVEE.

### Explicitly Deferred

- iPhone installation and iPhone-specific interface work.
- Cycles Metal stabilization.
- Sculpt-mode performance work.
- Large simulations.
- Runtime installation of downloaded native or Python extensions.
- Public App Store release.

## Architecture

UIKit, Pencil, keyboard, and pointer callbacks remain in thin Objective-C++ adapters. Logic that
normalizes events, tracks lifecycle state, or chooses safe features is implemented as small C++
units with platform-independent tests. These units feed the existing GHOST event layer; Blender core
code must not depend directly on UIKit.

```text
UIKit / Pencil / Pointer
        |
Thin Objective-C++ adapter
        |
Testable C++ policy and normalization
        |
GHOST events
        |
Blender core
```

Device-specific decisions must remain at the platform boundary. Generic touch or interface
improvements that also benefit desktop Blender should remain separable from iPad-only code so they
can be upstreamed independently.

## Platform Build Contract

The official iOS branch currently targets both iPhone and iPad and sets a minimum deployment target
of iOS 16. The foundation changes only this existing policy:

- Xcode `TARGETED_DEVICE_FAMILY` is exactly `2` for cross-platform iOS builds.
- The physical-device minimum deployment target is iPadOS 18.0.
- The Simulator minimum deployment target is iPadOS 18.0.
- macOS configuration remains unchanged.

These are configuration decisions rather than runtime behaviors. They are verified through a
focused diff and, when an Apple build environment is available, the generated Xcode build settings.
The project does not retain a source-text test that merely duplicates the chosen constants.

## First Functional TDD Slice: Pencil Pressure Normalization

The existing Objective-C++ handler divides Pencil force by `maximumPossibleForce` directly. Move
that calculation into a small C++ function that is called by the existing handler and can be tested
without UIKit.

The function must:

- map half of the maximum force to `0.5`;
- return `0.0` when maximum force is zero or negative;
- clamp negative force to `0.0`;
- clamp force above the maximum to `1.0`.

Each behavior is introduced with a failing host test before its minimum implementation. The helper
is not a speculative policy layer: the current Pencil handler consumes it immediately.

## Subsequent Milestones

1. **Reproducible iPad build:** document dependency provenance, verify source/LFS expectations, and
   compile an arm64 Simulator build.
2. **Input boundary:** extract and test keyboard, pointer, touch, and Pencil normalization before
   changing UIKit handlers.
3. **Lifecycle and documents:** adopt UIScene, remove the full-screen lifecycle dependency, use
   security-scoped document access, and add recovery behavior.
4. **Memory and rendering:** respond to memory pressure, make Workbench the safe fallback, and
   stabilize EEVEE on the minimum supported iPad.
5. **iPad interaction:** finish Pencil pressure and offset handling and validate common editing
   workflows.
6. **iPhone follow-up:** start a separate design and TDD cycle only after the iPad stability gates
   pass.

## Error Handling Principles

- On backgrounding, release all active key, pointer, and touch state to prevent stuck input.
- On memory pressure, save recovery state before purging caches or reducing rendering features.
- On document-access failure, preserve the original file and report a specific error.
- Never silently overwrite a damaged or partially written `.blend` file.
- Treat unsupported hardware as a controlled compatibility failure, not an unexplained crash.

## Testing Strategy

Use the smallest test layer capable of proving each behavior:

- Run dependency-free host tests locally for pure C++ logic.
- Use Objective-C++ Simulator integration tests only for behavior that requires Apple frameworks.
- Use physical-device checks for memory pressure, thermal behavior, Pencil, and pointer hardware.
- Do not treat a Simulator result as proof of physical-device stability.

Every production behavior follows RED, GREEN, REFACTOR:

1. Write one test for one behavior.
2. Run it and verify the expected failure.
3. Add only the implementation needed for that test.
4. Run the focused test and its related suite.
5. Refactor only after all tests are green.

## GitHub Actions Policy

- Do not add a workflow during the platform-contract slice.
- Do not run tests on every push or on a schedule.
- Add a manually dispatched workflow only when a Simulator build cannot be verified locally.
- Cancel duplicate runs on the same branch.
- Avoid uploading large build artifacts unless a specific device-testing handoff requires them.
- Never substitute hosted CI for a physical iPad stability gate.

## Acceptance Criteria

The foundation milestone is complete when:

- `main` and `ios/base-5.1.2` remain unchanged.
- `ios/ipad-mvp` contains the approved design and implementation plan.
- The Xcode device-family and deployment-target settings match the approved iPad contract.
- Each Pencil pressure test is observed failing for the intended missing behavior before passing.
- The current Objective-C++ Pencil handler calls the tested normalization function.
- The diff contains no GitHub Actions workflow and no unrelated Blender changes.
- The branch is pushed with reviewable, focused commits.

## iPhone Entry Gate

iPhone work may begin only after the iPad build can be repeatedly installed or distributed through
TestFlight, document save and recovery are stable, input regressions pass, and a representative
session runs for at least 30 minutes on the minimum supported iPad without a memory termination.
