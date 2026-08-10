# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

find_package(XCTest REQUIRED)

xctest_add_bundle(BlenderFTLTests blender)

target_sources(BlenderFTLTests PRIVATE
  BlenderFTLTests.mm
  ../../intern/ghost/intern/GHOST_IOSInput.cc
)

target_include_directories(BlenderFTLTests PRIVATE
  ../../intern/ghost/intern
)

set_target_properties(BlenderFTLTests PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${EXECUTABLE_OUTPUT_PATH}"
  XCODE_ATTRIBUTE_PRODUCT_BUNDLE_IDENTIFIER "${BLENDER_IOS_BUNDLE_IDENTIFIER}.tests"
  XCODE_ATTRIBUTE_TARGETED_DEVICE_FAMILY "1,2"
  XCODE_ATTRIBUTE_CODE_SIGN_ENTITLEMENTS ""
  XCODE_ATTRIBUTE_IPHONEOS_DEPLOYMENT_TARGET "16.6"
)

# FindXCTest attaches hosted test bundles to the testee application's scheme.
set_target_properties(blender PROPERTIES XCODE_GENERATE_SCHEME TRUE)

option(WITH_IOS_UI_TESTS "Build physical-device UI tests" OFF)

if(WITH_IOS_UI_TESTS)
  xctest_add_bundle(BlenderUITests blender)

  target_sources(BlenderUITests PRIVATE
    BlenderUITests.m
  )

  set_target_properties(BlenderUITests PROPERTIES
    XCODE_PRODUCT_TYPE "com.apple.product-type.bundle.ui-testing"
    XCODE_ATTRIBUTE_PRODUCT_BUNDLE_IDENTIFIER "${BLENDER_IOS_BUNDLE_IDENTIFIER}.uitests"
    XCODE_ATTRIBUTE_TARGETED_DEVICE_FAMILY "1,2"
    XCODE_ATTRIBUTE_CODE_SIGN_ENTITLEMENTS ""
    XCODE_ATTRIBUTE_IPHONEOS_DEPLOYMENT_TARGET "16.6"
    XCODE_ATTRIBUTE_BUNDLE_LOADER ""
    XCODE_ATTRIBUTE_TEST_HOST ""
    XCODE_ATTRIBUTE_TEST_TARGET_NAME "blender"
  )
endif()
