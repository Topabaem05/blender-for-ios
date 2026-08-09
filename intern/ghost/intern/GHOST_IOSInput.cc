/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "GHOST_IOSInput.hh"

#include <algorithm>

float GHOST_IOS_normalizePressure(const float force, const float maximum_force)
{
  if (maximum_force <= 0.0f) {
    return 0.0f;
  }
  return std::clamp(force / maximum_force, 0.0f, 1.0f);
}
