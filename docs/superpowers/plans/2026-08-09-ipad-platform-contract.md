# iPad Platform Foundation Implementation Plan

> **Status:** The platform target in this historical plan is superseded by
> `docs/superpowers/plans/2026-08-09-ipad-firebase-xctest.md`, which changes the minimum device to
> iPad (10th generation) and the deployment floor to iPadOS 16.6. The RED-GREEN record below is kept
> unchanged.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Narrow the existing Blender iOS port to the approved iPadOS 18 target and introduce the first real TDD-protected input behavior: safe Apple Pencil pressure normalization.

**Architecture:** Keep build policy in the existing Apple CMake files. Extract only Pencil pressure normalization from the current Objective-C++ input handler into a small C++ function, call it from that handler, and exercise the real function with a dependency-free host executable. Configuration decisions receive focused diff verification rather than permanent tests that duplicate constants.

**Tech Stack:** C++17, Objective-C++, CMake configuration, Python-free host compilation with `c++`, Git.

## Global Constraints

- Keep `main` unchanged.
- Keep `ios/base-5.1.2` fixed at `a1de44dd54af75a4c8c4a29a5fed2a1334a87446`.
- Make changes only on `ios/ipad-mvp`.
- Set Xcode `TARGETED_DEVICE_FAMILY` to exactly `2`.
- Set physical-device and Simulator deployment targets to `18.00`.
- Leave macOS configuration unchanged.
- Add no GitHub Actions workflow and trigger no GitHub Actions run.
- Write and observe each functional test failing before production implementation.
- Change no unrelated Blender code or formatting.

---

### Task 1: Apply the Approved iPad Build Contract

**Files:**

- Modify: `build_files/cmake/platform/platform_apple.cmake`
- Modify: `build_files/cmake/platform/platform_apple_xcode.cmake`

**Interfaces:**

- Consumes: Existing Blender Apple cross-platform CMake branches.
- Produces: Xcode settings for iPad device family `2` and deployment target `18.00` on device and Simulator.

- [ ] **Step 1: Record the baseline settings**

Run:

```bash
rg -n 'TARGETED_DEVICE_FAMILY|OSX_MIN_DEPLOYMENT_TARGET' \
  build_files/cmake/platform/platform_apple.cmake \
  build_files/cmake/platform/platform_apple_xcode.cmake
```

Expected: device family `1,2`, two iOS values of `16.00`, and the unchanged macOS value `11.2`.

- [ ] **Step 2: Make the three minimum configuration edits**

In `build_files/cmake/platform/platform_apple.cmake`, change:

```cmake
set(CMAKE_XCODE_ATTRIBUTE_TARGETED_DEVICE_FAMILY "1,2")
```

to:

```cmake
set(CMAKE_XCODE_ATTRIBUTE_TARGETED_DEVICE_FAMILY "2")
```

In both the `ios` and `ios-simulator` branches of
`build_files/cmake/platform/platform_apple_xcode.cmake`, change:

```cmake
set(OSX_MIN_DEPLOYMENT_TARGET 16.00)
```

to:

```cmake
set(OSX_MIN_DEPLOYMENT_TARGET 18.00)
```

- [ ] **Step 3: Inspect the focused diff**

Run:

```bash
git diff --check
git diff -- \
  build_files/cmake/platform/platform_apple.cmake \
  build_files/cmake/platform/platform_apple_xcode.cmake
```

Expected: exactly three value changes and no macOS change.

- [ ] **Step 4: Commit the build contract**

```bash
git add build_files/cmake/platform/platform_apple.cmake \
  build_files/cmake/platform/platform_apple_xcode.cmake
git commit -m "build: target iPadOS 18 devices"
```

### Task 2: Normalize Valid Pencil Pressure

**Files:**

- Create: `intern/ghost/intern/GHOST_IOSInput.hh`
- Create: `intern/ghost/intern/GHOST_IOSInput.cc`
- Create: `intern/ghost/test/GHOST_IOSInput_test.cc`
- Modify: `intern/ghost/CMakeLists.txt`
- Modify: `intern/ghost/intern/GHOST_WindowIOS.mm`

**Interfaces:**

- Consumes: Apple Pencil `force` and `maximumPossibleForce` values.
- Produces: `float GHOST_IOS_normalizePressure(float force, float maximum_force)` returning Blender's normalized pressure.

- [ ] **Step 1: Write the first test for real pressure scaling**

Create `intern/ghost/test/GHOST_IOSInput_test.cc`:

```cpp
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

}  // namespace

int main()
{
  test_pressure_is_scaled_by_maximum_force();
  return 0;
}
```

- [ ] **Step 2: Compile and verify RED**

Run:

```bash
c++ -std=c++17 -Wall -Wextra -Werror \
  -Iintern/ghost/intern \
  intern/ghost/test/GHOST_IOSInput_test.cc \
  intern/ghost/intern/GHOST_IOSInput.cc \
  -o /tmp/blender_ios_input_test
```

Expected: compilation fails because `GHOST_IOSInput.hh` and `.cc` do not exist. This is the intended missing production behavior, not a test typo.

- [ ] **Step 3: Add the minimum pressure function**

Create `intern/ghost/intern/GHOST_IOSInput.hh`:

```cpp
/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

float GHOST_IOS_normalizePressure(float force, float maximum_force);
```

Create `intern/ghost/intern/GHOST_IOSInput.cc`:

```cpp
/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "GHOST_IOSInput.hh"

float GHOST_IOS_normalizePressure(const float force, const float maximum_force)
{
  return force / maximum_force;
}
```

Add both files to the `APPLE_TARGET_IOS` source list in `intern/ghost/CMakeLists.txt`:

```cmake
intern/GHOST_IOSInput.cc
intern/GHOST_IOSInput.hh
```

Include the header in `GHOST_WindowIOS.mm` and replace the direct division with:

```cpp
tablet_data.Pressure = GHOST_IOS_normalizePressure(
    current_pencil_touch.force, current_pencil_touch.maximumPossibleForce);
```

- [ ] **Step 4: Compile and run to verify GREEN**

Run:

```bash
c++ -std=c++17 -Wall -Wextra -Werror \
  -Iintern/ghost/intern \
  intern/ghost/test/GHOST_IOSInput_test.cc \
  intern/ghost/intern/GHOST_IOSInput.cc \
  -o /tmp/blender_ios_input_test
/tmp/blender_ios_input_test
```

Expected: compilation and execution both exit `0` with no output.

- [ ] **Step 5: Commit valid pressure normalization**

```bash
git add intern/ghost/CMakeLists.txt \
  intern/ghost/intern/GHOST_IOSInput.hh \
  intern/ghost/intern/GHOST_IOSInput.cc \
  intern/ghost/intern/GHOST_WindowIOS.mm \
  intern/ghost/test/GHOST_IOSInput_test.cc
git commit -m "feat: normalize iPad Pencil pressure"
```

### Task 3: Handle Invalid Maximum Force

**Files:**

- Modify: `intern/ghost/test/GHOST_IOSInput_test.cc`
- Modify: `intern/ghost/intern/GHOST_IOSInput.cc`

**Interfaces:**

- Consumes: The pressure function from Task 2.
- Produces: A defined `0.0` result when the maximum force is zero or negative.

- [ ] **Step 1: Write the failing invalid-maximum test**

Add before the namespace closes:

```cpp
void test_non_positive_maximum_force_has_no_pressure()
{
  expect_near(GHOST_IOS_normalizePressure(1.0f, 0.0f), 0.0f);
  expect_near(GHOST_IOS_normalizePressure(1.0f, -1.0f), 0.0f);
}
```

Call it from `main` after the existing test:

```cpp
test_non_positive_maximum_force_has_no_pressure();
```

- [ ] **Step 2: Compile and run to verify RED**

Run the Task 2 compile command, then `/tmp/blender_ios_input_test`.

Expected: the executable aborts on the new assertion because direct division does not return `0.0` for both invalid maxima.

- [ ] **Step 3: Add the minimum guard**

At the start of `GHOST_IOS_normalizePressure` add:

```cpp
if (maximum_force <= 0.0f) {
  return 0.0f;
}
```

- [ ] **Step 4: Compile and run to verify GREEN**

Run the Task 2 compile and execution commands.

Expected: both exit `0` with no output.

- [ ] **Step 5: Commit the invalid-input behavior**

```bash
git add intern/ghost/intern/GHOST_IOSInput.cc \
  intern/ghost/test/GHOST_IOSInput_test.cc
git commit -m "fix: handle invalid Pencil force limits"
```

### Task 4: Clamp Pencil Pressure to Blender's Range

**Files:**

- Modify: `intern/ghost/test/GHOST_IOSInput_test.cc`
- Modify: `intern/ghost/intern/GHOST_IOSInput.cc`

**Interfaces:**

- Consumes: Valid but out-of-range force samples.
- Produces: Pressure constrained to Blender's documented `[0.0, 1.0]` range.

- [ ] **Step 1: Write the failing range test**

Add before the namespace closes:

```cpp
void test_pressure_is_clamped_to_blender_range()
{
  expect_near(GHOST_IOS_normalizePressure(-1.0f, 4.0f), 0.0f);
  expect_near(GHOST_IOS_normalizePressure(5.0f, 4.0f), 1.0f);
}
```

Call it from `main` after the earlier tests:

```cpp
test_pressure_is_clamped_to_blender_range();
```

- [ ] **Step 2: Compile and run to verify RED**

Run the Task 2 compile and execution commands.

Expected: the executable aborts because the current function returns `-0.25` and `1.25`.

- [ ] **Step 3: Implement the minimum clamp**

Add:

```cpp
#include <algorithm>
```

Replace the final return with:

```cpp
return std::clamp(force / maximum_force, 0.0f, 1.0f);
```

- [ ] **Step 4: Compile and run the full host test to verify GREEN**

Run the Task 2 compile and execution commands.

Expected: both exit `0` with no output.

- [ ] **Step 5: Commit the range behavior**

```bash
git add intern/ghost/intern/GHOST_IOSInput.cc \
  intern/ghost/test/GHOST_IOSInput_test.cc
git commit -m "fix: clamp Pencil pressure samples"
```

### Task 5: Verify the Foundation Slice

**Files:**

- Verify only; no file changes expected.

**Interfaces:**

- Consumes: Tasks 1-4.
- Produces: Evidence that host behavior passes and the branch remains narrowly scoped.

- [ ] **Step 1: Rebuild and run the full host test**

```bash
c++ -std=c++17 -Wall -Wextra -Werror -pedantic \
  -Iintern/ghost/intern \
  intern/ghost/test/GHOST_IOSInput_test.cc \
  intern/ghost/intern/GHOST_IOSInput.cc \
  -o /tmp/blender_ios_input_test
/tmp/blender_ios_input_test
```

Expected: both exit `0` with no output.

- [ ] **Step 2: Inspect the branch diff and whitespace**

```bash
git diff --check a1de44dd54af75a4c8c4a29a5fed2a1334a87446...HEAD
git diff --stat a1de44dd54af75a4c8c4a29a5fed2a1334a87446...HEAD
git diff --name-only a1de44dd54af75a4c8c4a29a5fed2a1334a87446...HEAD
```

Expected production paths are limited to the two Apple CMake files and the GHOST iOS input files.

- [ ] **Step 3: Prove that no workflow changed**

```bash
test -z "$(git diff --name-only \
  a1de44dd54af75a4c8c4a29a5fed2a1334a87446...HEAD \
  -- .github/workflows)"
```

Expected: exit `0` with no output.

- [ ] **Step 4: Record the unavailable verification boundary**

Do not claim an iPad or Simulator build. The current environment has no Xcode, CMake executable, or physical iPad. A manually dispatched macOS build is deferred until a later integration milestone because the user explicitly requested that GitHub Actions not be used for each small change.

- [ ] **Step 5: Confirm a clean branch before push**

```bash
git status --short --branch
```

Expected: no unstaged or uncommitted files on `ios/ipad-mvp`.
