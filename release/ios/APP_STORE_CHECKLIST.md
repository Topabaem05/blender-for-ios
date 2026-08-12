# iOS App Store release gate

This checklist separates behavior that can be verified in the repository or on a development
device from decisions that require the release owner, App Store Connect, or Blender Foundation.
Do not submit an archive while an item under **Submission blockers** remains open.

## Submission blockers

- [ ] Obtain written permission from Blender Foundation to use **Blender** as the app name and the
  Blender logo as the App Store icon, or give the fork a unique name and brand. The current name and
  icon remain suitable only for development QA until this is resolved.
- [ ] Complete a GPL distribution review. Publish the complete corresponding source for the exact
  shipped binary, include the applicable licenses and notices, and confirm that the selected App
  Store terms do not add restrictions incompatible with the distributed GPLv3-or-later work.
- [ ] Create a Release archive with App Store distribution signing and pass Xcode Organizer's
  validation. Development signing is evidence for device QA only.
- [ ] Either implement and pass third-party-provider open-in-place testing with balanced
  security-scoped access, `NSFileCoordinator`, and `NSFilePresenter`, or disable open-in-place for
  the Store profile and ship a tested import-as-copy plus explicit export workflow. The app's
  Documents path and Files URL callback alone do not prove provider-coordinated access.
- [ ] Resolve or accept with a documented OS-version ceiling the pending UIKit scene-lifecycle
  migration warning.
- [ ] Run the universal release build on a physical iPad before claiming physical iPad support.
- [ ] Verify the configured Cycles build on device. If it is not stable within the agreed thermal
  and memory envelope, disable it for release and provide a clear unsupported-engine message.

## Automated package gate

- [ ] iPhone and iPad are both present in the targeted device family.
- [ ] The deployment target and linked platform are iOS, and every loadable binary has the expected
  device architecture.
- [ ] The 1024-pixel App Store icon has no alpha channel and the asset catalog compiles.
- [ ] Every declared launch and main storyboard exists and compiles.
- [ ] `PrivacyInfo.xcprivacy` is present in the app and embedded Python framework and contains only
  reasons supported by the final binary audit.
- [ ] There are no loadable Python `.so` files. Native Python modules are signed frameworks with
  matching `.fwork` and `.origin` redirects.
- [ ] All nested frameworks and the app pass signature verification, use the same provisioning
  identity, and have a closed loader dependency graph.
- [ ] The embedded Python sysconfig identifies iOS and its extension suffix matches the packaged
  native modules.
- [ ] Automatic Python execution from documents defaults to disabled in the generated build.
- [ ] No Git LFS pointer, host executable, test support, or developer-only artifact is packaged.
- [ ] App Store privacy declarations are regenerated after the final executable and dependency set
  is frozen.

Run the repository gate with:

```sh
python3 -m unittest discover -s release/ios/testlab/tests -v
python3 release/ios/testlab/validate_app.py /path/to/signed/Blender.app
```

## Physical iPhone gate

- [ ] Install only the signed staging app that passed the automated package gate.
- [ ] Cold launch shows the launch view and reaches the editor without a black-screen stall.
- [ ] Rotate through supported orientations; confirm the editor remains usable at the smallest
  supported iPhone size and respects the safe area.
- [ ] Confirm the single-window workflow remains usable without a mouse or hardware keyboard, and
  that touch targets, temporary regions, and essential editors remain reachable on the phone-sized
  viewport.
- [ ] Create and transform objects, undo/redo, save, terminate, relaunch, and reopen the saved file.
- [ ] Open the supplied Blender 5.2 splash file with document auto-execution disabled, save a copy,
  terminate, and reopen that copy.
- [ ] Export and reimport OBJ, PLY, and STL files from the app's Documents directory.
- [ ] Open a `.blend` delivered through the iOS Files URL callback. Repeat using iCloud Drive and a
  third-party provider, then verify overwrite/save-as and balanced security-scoped access.
- [ ] Exercise `bpy`, the bundled Python standard library, NumPy, a local user script, and one
  bundled add-on. Verify that a document cannot silently opt into auto-execution.
- [ ] Verify runtime Extension installation and native wheel installation stop with the documented
  iOS message and do not invoke a subprocess or download executable code.
- [ ] Render Workbench and Eevee frames. If Cycles is exposed, start with a tiny one-sample scene and
  stop the test on thermal, memory-pressure, or stability warning.
- [ ] Background and foreground the app repeatedly, lock and unlock once, and confirm the open file
  and unsaved-change state survive without a new crash report.
- [ ] Run a sustained large-scene session while observing memory, thermal state, storage growth, and
  app termination. Do not repeat launch/install attempts if the phone becomes unavailable.

## Keyboard and iPad Simulator gate

- [ ] On iPhone, verify software-keyboard focus, text entry, composition, backspace, return, escape
  replacement, and keyboard dismissal. A software keyboard cannot prove hardware modifiers.
- [ ] On iPad Simulator, run the touch UI suite and the Apple keyboard combinations for Shift,
  Control, Option, Command, Space, undo, duplicate, transform, and maximize-area behavior.
- [ ] Open, save, reopen, export, and reimport the supplied large scene on an iPad Simulator.
- [ ] Check landscape and portrait layout, modal dialogs, file browser, Python console, Scripting
  workspace, toolbar reachability, and no clipped controls.

## Runtime feature policy

| Capability | Release policy |
| --- | --- |
| Bundled Python and `bpy` | Allow; part of the signed app |
| User-selected external Python script | Development QA only until App Review/legal sign-off; safest Store profile disables execution |
| Python embedded in a `.blend` | Never run silently; consider disabling execution entirely in the Store profile |
| Bundled add-ons and pure-Python wheels | Allow only when selected and reviewed at build time |
| Native Python modules | Allow only as prebuilt, signed app frameworks |
| Runtime Extension install/update | Disable for the App Store build |
| Runtime native wheel or executable download | Disable |
| Subprocess-based tools | Disable on iOS |
| Network-enabled add-ons | Ship disabled unless their purpose, consent, privacy label, and review notes are complete |

The current `WITH_PYTHON_SECURITY` setting only makes document auto-execution default to off. It
does not hard-disable the preference, command-line override, Python Console, or Scripting workspace.
A Store profile that promises no user code execution needs a separate enforced gate and regression.

## App Store Connect and review package

- [ ] Provide iPhone and iPad screenshots from the release candidate, an accurate description, a
  support URL, a privacy-policy URL, age rating, and review notes for Python and Files behavior.
- [ ] Complete App Privacy answers from observed behavior of the final build, not from the empty
  privacy manifest alone.
- [ ] Complete export-compliance answers for the bundled cryptography with the release owner or
  counsel.
- [ ] Give App Review a deterministic sample `.blend`, steps for local scripting, and an explanation
  that runtime Extension/native-code installation is disabled.
- [ ] Publish the exact source revision, build instructions, patches, and third-party notices used by
  the submitted binary.
- [ ] Confirm the current Xcode/SDK upload requirement immediately before archive upload.

## Upstream contribution gate

- [ ] Coordinate significant iOS changes with the Blender iOS tablet maintainers before opening an
  upstream pull request, and avoid duplicating work already active in the shared iOS branch.
- [ ] The human contributor authors the commits, understands and manually reviews every submitted
  change, accepts quality and license responsibility, and personally verifies the affected behavior.
- [ ] For large or unfamiliar tool-assisted changes, describe the implementation methodology and
  write the pull-request description and review comments in the contributor's own words.

## Primary references

- [Apple App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Apple privacy manifest files](https://developer.apple.com/documentation/bundleresources/privacy-manifest-files)
- [Apple required-reason APIs](https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api)
- [Apple document picker](https://developer.apple.com/documentation/uikit/uidocumentpickerviewcontroller)
- [Apple upcoming requirements](https://developer.apple.com/news/upcoming-requirements/)
- [Blender license](https://www.blender.org/about/license/)
- [Blender trademark policy](https://www.blender.org/about/trademark-policy/)
- [Blender: Beyond Mouse & Keyboard](https://code.blender.org/2025/07/beyond-mouse-keyboard/)
- [Blender iOS dependency pull request](https://projects.blender.org/blender/blender/pulls/161747)
- [Blender iOS tablet chat](https://chat.blender.org/#/room/#ios-tablet:blender.org)
- [Blender AI contributions policy](https://developer.blender.org/docs/handbook/contributing/ai_contributions/)

This is an engineering release gate, not legal advice. Trademark and GPL/App Store compatibility
must be resolved by the release owner with the relevant rights holder or counsel.
