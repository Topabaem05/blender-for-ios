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

GHOST_TKey GHOST_IOS_keyFromHIDUsage(const uint32_t usage)
{
  if (usage >= 0x04 && usage <= 0x1d) {
    return GHOST_TKey(GHOST_kKeyA + usage - 0x04);
  }
  if (usage >= 0x1e && usage <= 0x26) {
    return GHOST_TKey(GHOST_kKey1 + usage - 0x1e);
  }
  if (usage >= 0x3a && usage <= 0x45) {
    return GHOST_TKey(GHOST_kKeyF1 + usage - 0x3a);
  }
  if (usage >= 0x59 && usage <= 0x61) {
    return GHOST_TKey(GHOST_kKeyNumpad1 + usage - 0x59);
  }
  if (usage >= 0x68 && usage <= 0x73) {
    return GHOST_TKey(GHOST_kKeyF13 + usage - 0x68);
  }

  switch (usage) {
    case 0x27:
      return GHOST_kKey0;
    case 0x28:
      return GHOST_kKeyEnter;
    case 0x29:
      return GHOST_kKeyEsc;
    case 0x2a:
      return GHOST_kKeyBackSpace;
    case 0x2b:
      return GHOST_kKeyTab;
    case 0x2c:
      return GHOST_kKeySpace;
    case 0x2d:
      return GHOST_kKeyMinus;
    case 0x2e:
      return GHOST_kKeyEqual;
    case 0x2f:
      return GHOST_kKeyLeftBracket;
    case 0x30:
      return GHOST_kKeyRightBracket;
    case 0x31:
      return GHOST_kKeyBackslash;
    case 0x33:
      return GHOST_kKeySemicolon;
    case 0x34:
      return GHOST_kKeyQuote;
    case 0x35:
      return GHOST_kKeyAccentGrave;
    case 0x36:
      return GHOST_kKeyComma;
    case 0x37:
      return GHOST_kKeyPeriod;
    case 0x38:
      return GHOST_kKeySlash;
    case 0x39:
      return GHOST_kKeyCapsLock;
    case 0x46:
      return GHOST_kKeyPrintScreen;
    case 0x47:
      return GHOST_kKeyScrollLock;
    case 0x48:
      return GHOST_kKeyPause;
    case 0x49:
      return GHOST_kKeyInsert;
    case 0x4a:
      return GHOST_kKeyHome;
    case 0x4b:
      return GHOST_kKeyUpPage;
    case 0x4c:
      return GHOST_kKeyDelete;
    case 0x4d:
      return GHOST_kKeyEnd;
    case 0x4e:
      return GHOST_kKeyDownPage;
    case 0x4f:
      return GHOST_kKeyRightArrow;
    case 0x50:
      return GHOST_kKeyLeftArrow;
    case 0x51:
      return GHOST_kKeyDownArrow;
    case 0x52:
      return GHOST_kKeyUpArrow;
    case 0x53:
      return GHOST_kKeyNumLock;
    case 0x54:
      return GHOST_kKeyNumpadSlash;
    case 0x55:
      return GHOST_kKeyNumpadAsterisk;
    case 0x56:
      return GHOST_kKeyNumpadMinus;
    case 0x57:
      return GHOST_kKeyNumpadPlus;
    case 0x58:
      return GHOST_kKeyNumpadEnter;
    case 0x62:
      return GHOST_kKeyNumpad0;
    case 0x63:
      return GHOST_kKeyNumpadPeriod;
    case 0x64:
      return GHOST_kKeyGrLess;
    case 0x65:
      return GHOST_kKeyApp;
    case 0xe0:
      return GHOST_kKeyLeftControl;
    case 0xe1:
      return GHOST_kKeyLeftShift;
    case 0xe2:
      return GHOST_kKeyLeftAlt;
    case 0xe3:
      return GHOST_kKeyLeftOS;
    case 0xe4:
      return GHOST_kKeyRightControl;
    case 0xe5:
      return GHOST_kKeyRightShift;
    case 0xe6:
      return GHOST_kKeyRightAlt;
    case 0xe7:
      return GHOST_kKeyRightOS;
    default:
      return GHOST_kKeyUnknown;
  }
}

int GHOST_IOS_modifierTransitions(const uint8_t previous_mask,
                                  const uint8_t current_mask,
                                  GHOST_IOSModifierTransition transitions[4])
{
  struct ModifierKey {
    uint8_t mask;
    GHOST_TKey key;
  };
  static constexpr ModifierKey modifier_keys[] = {
      {GHOST_IOS_MODIFIER_SHIFT, GHOST_kKeyLeftShift},
      {GHOST_IOS_MODIFIER_CONTROL, GHOST_kKeyLeftControl},
      {GHOST_IOS_MODIFIER_ALT, GHOST_kKeyLeftAlt},
      {GHOST_IOS_MODIFIER_OS, GHOST_kKeyLeftOS},
  };

  int count = 0;
  for (const ModifierKey &modifier : modifier_keys) {
    if ((previous_mask & modifier.mask) && !(current_mask & modifier.mask)) {
      transitions[count++] = {modifier.key, false};
    }
  }
  for (const ModifierKey &modifier : modifier_keys) {
    if (!(previous_mask & modifier.mask) && (current_mask & modifier.mask)) {
      transitions[count++] = {modifier.key, true};
    }
  }
  return count;
}
