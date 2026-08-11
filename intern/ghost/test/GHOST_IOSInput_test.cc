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

void test_hid_letters_and_numbers_map_to_ghost_keys()
{
  assert(GHOST_IOS_keyFromHIDUsage(0x04) == GHOST_kKeyA);
  assert(GHOST_IOS_keyFromHIDUsage(0x1d) == GHOST_kKeyZ);
  assert(GHOST_IOS_keyFromHIDUsage(0x1e) == GHOST_kKey1);
  assert(GHOST_IOS_keyFromHIDUsage(0x27) == GHOST_kKey0);
}

void test_hid_navigation_and_modifiers_map_to_ghost_keys()
{
  assert(GHOST_IOS_keyFromHIDUsage(0x28) == GHOST_kKeyEnter);
  assert(GHOST_IOS_keyFromHIDUsage(0x29) == GHOST_kKeyEsc);
  assert(GHOST_IOS_keyFromHIDUsage(0x50) == GHOST_kKeyLeftArrow);
  assert(GHOST_IOS_keyFromHIDUsage(0x52) == GHOST_kKeyUpArrow);
  assert(GHOST_IOS_keyFromHIDUsage(0xe0) == GHOST_kKeyLeftControl);
  assert(GHOST_IOS_keyFromHIDUsage(0xe3) == GHOST_kKeyLeftOS);
  assert(GHOST_IOS_keyFromHIDUsage(0xe7) == GHOST_kKeyRightOS);
}

void test_hid_punctuation_function_and_numpad_keys_map_to_ghost_keys()
{
  assert(GHOST_IOS_keyFromHIDUsage(0x2d) == GHOST_kKeyMinus);
  assert(GHOST_IOS_keyFromHIDUsage(0x38) == GHOST_kKeySlash);
  assert(GHOST_IOS_keyFromHIDUsage(0x3a) == GHOST_kKeyF1);
  assert(GHOST_IOS_keyFromHIDUsage(0x73) == GHOST_kKeyF24);
  assert(GHOST_IOS_keyFromHIDUsage(0x54) == GHOST_kKeyNumpadSlash);
  assert(GHOST_IOS_keyFromHIDUsage(0x61) == GHOST_kKeyNumpad9);
}

void test_unknown_hid_usage_stays_unknown()
{
  assert(GHOST_IOS_keyFromHIDUsage(0x00) == GHOST_kKeyUnknown);
}

void test_modifier_transitions_release_before_press()
{
  GHOST_IOSModifierTransition transitions[4];
  const int count = GHOST_IOS_modifierTransitions(GHOST_IOS_MODIFIER_SHIFT |
                                                      GHOST_IOS_MODIFIER_OS,
                                                  GHOST_IOS_MODIFIER_CONTROL |
                                                      GHOST_IOS_MODIFIER_ALT,
                                                  transitions);

  assert(count == 4);
  assert(transitions[0].key == GHOST_kKeyLeftShift && !transitions[0].key_down);
  assert(transitions[1].key == GHOST_kKeyLeftOS && !transitions[1].key_down);
  assert(transitions[2].key == GHOST_kKeyLeftControl && transitions[2].key_down);
  assert(transitions[3].key == GHOST_kKeyLeftAlt && transitions[3].key_down);
}

void test_unchanged_modifier_mask_has_no_transitions()
{
  GHOST_IOSModifierTransition transitions[4];
  assert(GHOST_IOS_modifierTransitions(GHOST_IOS_MODIFIER_SHIFT,
                                       GHOST_IOS_MODIFIER_SHIFT,
                                       transitions) == 0);
}

}  // namespace

int main()
{
  test_pressure_is_scaled_by_maximum_force();
  test_non_positive_maximum_force_has_no_pressure();
  test_pressure_is_clamped_to_blender_range();
  test_hid_letters_and_numbers_map_to_ghost_keys();
  test_hid_navigation_and_modifiers_map_to_ghost_keys();
  test_hid_punctuation_function_and_numpad_keys_map_to_ghost_keys();
  test_unknown_hid_usage_stays_unknown();
  test_modifier_transitions_release_before_press();
  test_unchanged_modifier_mask_has_no_transitions();
  return 0;
}
