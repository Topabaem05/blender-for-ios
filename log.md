# Port Log

## 2026-08-10

- Selected `ios/ipad-mvp` as the smallest complete iOS baseline.
- Confirmed the explicit iPad-only gates are the app target, hosted XCTest target, and package validator.
- Reproduced the Python 3.13 configuration blocker and the iOS Autoconf environment failure.
- Repaired the local host build tools without changing product code.
- Built the Python 3.13 runtime closure, NumPy 2.3.4, fmt, Eigen, Abseil, and Ceres for iOS arm64.
- Reproduced and removed host-library leakage from OpenEXR, OpenImageIO, FFmpeg, and fmt discovery.
- Reproduced the iPad-only package and Xcode settings, then made the exact universal family contract
  pass 11 packaging tests and generated Xcode build-setting checks.
