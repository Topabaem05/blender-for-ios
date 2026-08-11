/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include <cstdint>

#include "GHOST_Types.hh"

enum GHOST_IOSModifierMask : uint8_t {
  GHOST_IOS_MODIFIER_SHIFT = 1 << 0,
  GHOST_IOS_MODIFIER_CONTROL = 1 << 1,
  GHOST_IOS_MODIFIER_ALT = 1 << 2,
  GHOST_IOS_MODIFIER_OS = 1 << 3,
};

struct GHOST_IOSModifierTransition {
  GHOST_TKey key;
  bool key_down;
};

float GHOST_IOS_normalizePressure(float force, float maximum_force);
GHOST_TKey GHOST_IOS_keyFromHIDUsage(uint32_t usage);
int GHOST_IOS_modifierTransitions(uint8_t previous_mask,
                                  uint8_t current_mask,
                                  GHOST_IOSModifierTransition transitions[4]);
