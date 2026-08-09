# Firebase Test Lab XCTest handoff

This directory packages the generated Blender iOS XCTest products for Firebase Test Lab. It is an
operator handoff, not proof that a package or Firebase matrix has already been verified.

## Prerequisites

- macOS with Xcode 16 or newer selected by `xcode-select`.
- CMake 4.0.1 or newer. This is required for the Xcode 16 `FindXCTest` support used by the hosted
  `BlenderFTLTests` bundle.
- Git LFS installed and the repository's LFS objects fetched.
- A populated `lib/ios_arm64/python` dependency directory.
- An Apple development team and an iOS bundle identifier owned by that team. Do not use the
  repository default bundle identifier for a build you intend to sign and install.
- A Firebase project with permission to run Test Lab and a current Google Cloud CLI.

From the repository root, fetch and check the iOS dependency prerequisite before configuring:

```bash
git lfs install
git lfs pull
test -d lib/ios_arm64/python
test -n "$(find lib/ios_arm64/python -mindepth 1 -print -quit)"
```

## Configure, build, and package on macOS

Set these values to identifiers you control; the shown values are placeholders and are not valid
signing inputs.

```bash
APPLE_TEAM_ID='YOUR_APPLE_DEVELOPMENT_TEAM_ID'
BLENDER_BUNDLE_ID='com.example.blender'
```

Generate an iOS device Xcode project with the hosted Test Lab bundle enabled:

```bash
cmake -S . -B build-ios-testlab -G Xcode \
  -DAPPLE_TARGET_DEVICE=ios \
  -DWITH_IOS_TESTLAB=ON \
  -DBLENDER_IOS_BUNDLE_IDENTIFIER="$BLENDER_BUNDLE_ID" \
  -DCMAKE_XCODE_ATTRIBUTE_DEVELOPMENT_TEAM="$APPLE_TEAM_ID"
```

The wrapper builds the generated `blender` scheme for a Generic iOS Device with
`build-for-testing`, requires the hosted test at
`Blender.app/PlugIns/BlenderFTLTests.xctest`, verifies the app and hosted test signatures, checks
that both `Blender.app/Blender` and the hosted `BlenderFTLTests` executable contain `arm64`, and
writes the requested ZIP. It uses a dedicated `DerivedData-xctest` directory inside the build
directory and does not clean existing build output. The output path must not already exist.

```bash
release/ios/testlab/build_xctest.sh \
  "$PWD/build-ios-testlab" \
  "$PWD/build-ios-testlab/BlenderFTLTests.zip"
```

Inspect the archive before upload. Its root must contain only `Debug-iphoneos/` and exactly one
`*_iphoneos16.6-arm64.xctestrun` file. The device products must include
`Debug-iphoneos/Blender.app/PlugIns/BlenderFTLTests.xctest` with its Info.plist and executable:

```bash
unzip -l build-ios-testlab/BlenderFTLTests.zip
```

The wrapper cannot complete on Linux and its success is the Apple build/signature boundary. Do not
claim the ZIP is valid until it has completed on the signed macOS/Xcode builder.

## Select a live Firebase device pair

Firebase model IDs and version IDs are runtime catalog inputs, not constants in this repository.
Immediately before submission, query the catalog and select the entry that is explicitly the iPad
(10th generation) and supports iPadOS 16.6. Do not substitute a different iPad or an iPhone if the
required pair is unavailable.

```bash
FIREBASE_PROJECT='YOUR_FIREBASE_PROJECT_ID'
gcloud firebase test ios models list --project="$FIREBASE_PROJECT"
gcloud firebase test ios versions list --project="$FIREBASE_PROJECT"

FTL_MODEL_ID='MODEL_ID_FROM_THE_LIVE_CATALOG'
FTL_VERSION_ID='VERSION_ID_FROM_THE_LIVE_CATALOG'
gcloud firebase test ios models describe "$FTL_MODEL_ID" \
  --project="$FIREBASE_PROJECT" \
  --format=json
gcloud firebase test ios versions describe "$FTL_VERSION_ID" \
  --project="$FIREBASE_PROJECT" \
  --format=json
```

Continue only when the model description confirms the selected model/version pair. The catalog
also reports the Xcode versions usable for the version; choose a compatible value if the project
requires a specific Xcode release.

## Run the matrix

With the live values selected above, submit the XCTest archive in landscape with a ten-minute
timeout:

```bash
gcloud firebase test ios run \
  --project="$FIREBASE_PROJECT" \
  --type=xctest \
  --test="$PWD/build-ios-testlab/BlenderFTLTests.zip" \
  --device="model=${FTL_MODEL_ID},version=${FTL_VERSION_ID},orientation=landscape" \
  --timeout=10m
```

Record the matrix ID, selected model and version IDs, device dimensions, Xcode version, and XCTest
result. Repeat on the newest Test Lab iPadOS version available for the same model. Firebase Test
Lab does not verify Apple Pencil hardware behavior; that remains an owned-device gate.
