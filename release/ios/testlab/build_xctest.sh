#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Build the CMake-generated device XCTest products and package them for Test Lab.
set -euo pipefail

usage() {
  echo "Usage: $0 BUILD_DIR OUTPUT_ZIP" >&2
  exit 64
}

die() {
  echo "error: $*" >&2
  exit 1
}

if [ "$#" -ne 2 ]; then
  usage
fi

if [ "$(uname -s)" != "Darwin" ]; then
  die "this command must run on macOS"
fi

for required_tool in xcodebuild cmake codesign ditto file lipo otool python3; do
  if ! command -v "$required_tool" >/dev/null 2>&1; then
    die "required tool not found: $required_tool"
  fi
done

build_dir=$1
output_zip=$2
project_path="$build_dir/Blender.xcodeproj"
derived_data="$build_dir/DerivedData-xctest"
build_app="$build_dir/bin/Debug/Blender.app"
build_test_bundle="$build_app/PlugIns/BlenderFTLTests.xctest"
build_executable="$build_app/Blender"
build_test_executable="$build_test_bundle/BlenderFTLTests"
output_parent=$(dirname "$output_zip")
script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

[ -d "$build_dir" ] || die "build directory does not exist: $build_dir"
[ -d "$project_path" ] || die "missing CMake-generated project: $project_path"
[ -d "$output_parent" ] || die "output directory does not exist: $output_parent"
[ ! -e "$output_zip" ] || die "output ZIP already exists: $output_zip"

xcodebuild_settings=()
if [ -n "${APPLE_TEAM_ID:-}" ]; then
  xcodebuild_settings+=("DEVELOPMENT_TEAM=$APPLE_TEAM_ID")
fi

xcodebuild \
  -project "$project_path" \
  -scheme blender \
  -configuration Debug \
  -sdk iphoneos \
  -destination 'generic/platform=iOS' \
  -derivedDataPath "$derived_data" \
  "${xcodebuild_settings[@]}" \
  build-for-testing

[ -d "$build_app" ] || die "missing CMake Blender application: $build_app"
[ -d "$build_test_bundle" ] || die "missing hosted XCTest bundle: $build_test_bundle"
[ -f "$build_executable" ] || die "missing Blender executable: $build_executable"
[ -f "$build_test_executable" ] || die "missing hosted XCTest executable: $build_test_executable"

shopt -s nullglob
xctestrun_files=("$build_dir"/build/*_iphoneos*-arm64.xctestrun)
[ "${#xctestrun_files[@]}" -eq 1 ] || die "expected exactly one device .xctestrun in $build_dir/build"
xctestrun=${xctestrun_files[0]}

package_root=$(mktemp -d "$build_dir/.xctest-package.XXXXXX")
case "$package_root" in
  "$build_dir"/.xctest-package.*) ;;
  *) die "unsafe package directory: $package_root" ;;
esac
trap 'rm -rf -- "$package_root"' EXIT INT TERM HUP
products_dir="$package_root/Products"
device_products="$products_dir/Debug-iphoneos"
blender_app="$device_products/Blender.app"
test_bundle="$blender_app/PlugIns/BlenderFTLTests.xctest"
blender_executable="$blender_app/Blender"
test_executable="$test_bundle/BlenderFTLTests"

mkdir -p "$device_products"
cmake --install "$build_dir" --config Debug --prefix "$device_products"
[ -d "$blender_app" ] || die "install did not produce Blender.app: $blender_app"
mkdir -p "$blender_app/PlugIns"
ditto "$build_test_bundle" "$test_bundle"
ditto "$xctestrun" "$products_dir/$(basename "$xctestrun")"

codesign_output=$(codesign --display --verbose=4 "$build_app" 2>&1)
signing_identity=$(printf '%s\n' "$codesign_output" | sed -n 's/^Authority=//p' | sed -n '1p')
[ -n "$signing_identity" ] || die "could not determine the built app signing identity"
codesign --force \
  --sign "$signing_identity" \
  --timestamp=none \
  --preserve-metadata=identifier,entitlements,requirements,flags \
  "$blender_app"

codesign --verify --deep --strict --verbose=2 "$test_bundle"
codesign --verify --deep --strict --verbose=2 "$blender_app"
lipo "$blender_executable" -verify_arch arm64
lipo "$test_executable" -verify_arch arm64
python3 "$script_dir/validate_app.py" --allow-xctest-support "$blender_app"

python3 "$script_dir/package_xctest.py" "$products_dir" "$output_zip"
