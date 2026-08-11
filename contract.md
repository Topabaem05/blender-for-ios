# iPhone Editor Port Contract

The port is complete when the connected physical iPhone can install and cold-launch the same
Blender editor target as iPad, then complete these observable flows without a crash or data loss:

- open the default scene and reach every visible editor region;
- select and transform the default object with touch;
- execute a Python expression inside Blender;
- save a `.blend` file, background and resume the app, reopen the file, and confirm the edit;
- open a supplied `.blend` from iOS Files/Documents with auto-execution disabled, then save it and
  round-trip the enabled OBJ, PLY, and STL formats inside the app container;
- receive a Files-provider open-in-place URL without losing its security-scoped access;
- receive Apple hardware-keyboard keys and Shift, Control, Option, and Command modifiers so core
  Blender shortcuts perform observable edits;
- render the default scene with the primary renderer enabled by the iOS build;
- show a usable full-editor layout and complete core editing smoke checks in an iPad Simulator;
- define and enforce which embedded Python scripts, add-ons, native wheels, and Extensions can run
  within iOS code-signing and App Store constraints;
- package the app and hosted XCTest with `UIDeviceFamily` exactly `{1, 2}`.

Desktop-only modules already disabled by the iOS platform configuration are outside this contract.
Physical iPad regression remains required before declaring universal iPhone+iPad release support.
