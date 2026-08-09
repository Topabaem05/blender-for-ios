/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "GHOST_IOSInput.hh"

#include <cassert>
#include <cmath>

namespace {

constexpr float epsilon = 1.0e-6f;

void expect_near(const float actual, const float expected)
{
  assert(std::fabs(actual - expected) < epsilon);
}

void test_pressure_is_scaled_by_maximum_force()
{
  expect_near(GHOST_IOS_normalizePressure(2.0f, 4.0f), 0.5f);
}

void test_non_positive_maximum_force_has_no_pressure()
{
  expect_near(GHOST_IOS_normalizePressure(1.0f, 0.0f), 0.0f);
  expect_near(GHOST_IOS_normalizePressure(1.0f, -1.0f), 0.0f);
}

void test_pressure_is_clamped_to_blender_range()
{
  expect_near(GHOST_IOS_normalizePressure(-1.0f, 4.0f), 0.0f);
  expect_near(GHOST_IOS_normalizePressure(5.0f, 4.0f), 1.0f);
}

}  // namespace

int main()
{
  test_pressure_is_scaled_by_maximum_force();
  test_non_positive_maximum_force_has_no_pressure();
  test_pressure_is_clamped_to_blender_range();
  return 0;
}
