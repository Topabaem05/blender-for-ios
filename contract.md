# iPhone Editor Port Contract

The port is complete when the connected physical iPhone can install and cold-launch the same
Blender editor target as iPad, then complete these observable flows without a crash or data loss:

- open the default scene and reach every visible editor region;
- select and transform the default object with touch;
- execute a Python expression inside Blender;
- save a `.blend` file, background and resume the app, reopen the file, and confirm the edit;
- render the default scene with the primary renderer enabled by the iOS build;
- package the app and hosted XCTest with `UIDeviceFamily` exactly `{1, 2}`.

Desktop-only modules already disabled by the iOS platform configuration are outside this contract.
Physical iPad regression remains required before declaring universal iPhone+iPad release support.
