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

for required_tool in xcodebuild codesign lipo python3; do
  if ! command -v "$required_tool" >/dev/null 2>&1; then
    die "required tool not found: $required_tool"
  fi
done

build_dir=$1
output_zip=$2
project_path="$build_dir/Blender.xcodeproj"
derived_data="$build_dir/DerivedData-xctest"
products_dir="$derived_data/Build/Products"
device_products="$products_dir/Debug-iphoneos"
blender_app="$device_products/Blender.app"
test_bundle="$blender_app/PlugIns/BlenderFTLTests.xctest"
blender_executable="$blender_app/Blender"
test_executable="$test_bundle/BlenderFTLTests"
output_parent=$(dirname "$output_zip")
script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

[ -d "$build_dir" ] || die "build directory does not exist: $build_dir"
[ -d "$project_path" ] || die "missing CMake-generated project: $project_path"
[ -d "$output_parent" ] || die "output directory does not exist: $output_parent"
[ ! -e "$output_zip" ] || die "output ZIP already exists: $output_zip"

xcodebuild \
  -project "$project_path" \
  -scheme blender \
  -configuration Debug \
  -sdk iphoneos \
  -destination 'generic/platform=iOS' \
  -derivedDataPath "$derived_data" \
  build-for-testing

[ -d "$device_products" ] || die "missing device products: $device_products"
[ -d "$blender_app" ] || die "missing Blender application: $blender_app"
[ -d "$test_bundle" ] || die "missing hosted XCTest bundle: $test_bundle"
[ -f "$blender_executable" ] || die "missing Blender executable: $blender_executable"
[ -f "$test_executable" ] || die "missing hosted XCTest executable: $test_executable"

codesign --verify --deep --strict --verbose=2 "$test_bundle"
codesign --verify --deep --strict --verbose=2 "$blender_app"
lipo -verify_arch arm64 "$blender_executable"
lipo -verify_arch arm64 "$test_executable"

python3 "$script_dir/package_xctest.py" "$products_dir" "$output_zip"
