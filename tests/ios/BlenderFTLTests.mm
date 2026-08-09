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

@end
