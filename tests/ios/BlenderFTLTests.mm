/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#import <XCTest/XCTest.h>

#include "GHOST_IOSInput.hh"

@interface BlenderFTLTests : XCTestCase
@end

@implementation BlenderFTLTests

- (void)testPressureIsScaledByMaximumForce
{
  XCTAssertEqual(GHOST_IOS_normalizePressure(2.0f, 4.0f), 0.5f);
}

- (void)testZeroMaximumForceHasNoPressure
{
  XCTAssertEqual(GHOST_IOS_normalizePressure(1.0f, 0.0f), 0.0f);
}

- (void)testPressureIsClampedAtZero
{
  XCTAssertEqual(GHOST_IOS_normalizePressure(-1.0f, 4.0f), 0.0f);
}

- (void)testPressureIsClampedAtOne
{
  XCTAssertEqual(GHOST_IOS_normalizePressure(5.0f, 4.0f), 1.0f);
}

- (void)testKeyboardHIDLettersAndNumbers
{
  XCTAssertEqual(GHOST_IOS_keyFromHIDUsage(0x04), GHOST_kKeyA);
  XCTAssertEqual(GHOST_IOS_keyFromHIDUsage(0x1d), GHOST_kKeyZ);
  XCTAssertEqual(GHOST_IOS_keyFromHIDUsage(0x1e), GHOST_kKey1);
  XCTAssertEqual(GHOST_IOS_keyFromHIDUsage(0x27), GHOST_kKey0);
}

- (void)testKeyboardHIDModifiersAndNavigation
{
  XCTAssertEqual(GHOST_IOS_keyFromHIDUsage(0x28), GHOST_kKeyEnter);
  XCTAssertEqual(GHOST_IOS_keyFromHIDUsage(0x50), GHOST_kKeyLeftArrow);
  XCTAssertEqual(GHOST_IOS_keyFromHIDUsage(0xe1), GHOST_kKeyLeftShift);
  XCTAssertEqual(GHOST_IOS_keyFromHIDUsage(0xe3), GHOST_kKeyLeftOS);
}

- (void)testKeyboardHIDPunctuationFunctionAndNumpad
{
  XCTAssertEqual(GHOST_IOS_keyFromHIDUsage(0x2d), GHOST_kKeyMinus);
  XCTAssertEqual(GHOST_IOS_keyFromHIDUsage(0x38), GHOST_kKeySlash);
  XCTAssertEqual(GHOST_IOS_keyFromHIDUsage(0x3a), GHOST_kKeyF1);
  XCTAssertEqual(GHOST_IOS_keyFromHIDUsage(0x73), GHOST_kKeyF24);
  XCTAssertEqual(GHOST_IOS_keyFromHIDUsage(0x54), GHOST_kKeyNumpadSlash);
  XCTAssertEqual(GHOST_IOS_keyFromHIDUsage(0x61), GHOST_kKeyNumpad9);
}

- (void)testUnknownKeyboardHIDUsage
{
  XCTAssertEqual(GHOST_IOS_keyFromHIDUsage(0x00), GHOST_kKeyUnknown);
}

- (void)testKeyboardModifierTransitionsReleaseBeforePress
{
  GHOST_IOSModifierTransition transitions[4];
  const int count = GHOST_IOS_modifierTransitions(GHOST_IOS_MODIFIER_SHIFT |
                                                      GHOST_IOS_MODIFIER_OS,
                                                  GHOST_IOS_MODIFIER_CONTROL |
                                                      GHOST_IOS_MODIFIER_ALT,
                                                  transitions);

  XCTAssertEqual(count, 4);
  XCTAssertEqual(transitions[0].key, GHOST_kKeyLeftShift);
  XCTAssertFalse(transitions[0].key_down);
  XCTAssertEqual(transitions[1].key, GHOST_kKeyLeftOS);
  XCTAssertFalse(transitions[1].key_down);
  XCTAssertEqual(transitions[2].key, GHOST_kKeyLeftControl);
  XCTAssertTrue(transitions[2].key_down);
  XCTAssertEqual(transitions[3].key, GHOST_kKeyLeftAlt);
  XCTAssertTrue(transitions[3].key_down);
}

- (void)testUnchangedKeyboardModifierMaskHasNoTransitions
{
  GHOST_IOSModifierTransition transitions[4];
  XCTAssertEqual(GHOST_IOS_modifierTransitions(GHOST_IOS_MODIFIER_SHIFT,
                                                GHOST_IOS_MODIFIER_SHIFT,
                                                transitions),
                 0);
}

@end
