# Blender iOS Python and Extensions

The iOS app embeds Python and does not depend on a separate Python executable.

## Supported

- Blender scripting through `bpy` and the bundled Python standard library.
- Scripts opened from user-accessible documents in development QA builds, subject to Blender's
  existing auto-execution consent setting.
- Add-ons shipped inside the signed app bundle.
- Pure-Python wheels bundled at build time.
- Native Python modules prepared at build time as individually signed frameworks. Their original
  import locations contain `.fwork` redirects, and each framework contains the matching `.origin`
  redirect required by CPython on iOS.

## Not supported at runtime

- Blender Extension install, update, or management commands that require a subprocess.
- Downloading or installing new native wheels or other executable code after signing.
- Treating a conventional `.so` file in `site-packages` as a loadable iOS module.

The current project policy disables runtime Extension management on iOS as one boundary. This keeps
the signed executable set deterministic and avoids accepting an archive that may contain native
code. Add-ons, wheels, and Extensions intended for distribution must be selected during the app
build and included in the signed package.

`WITH_PYTHON_SECURITY` makes automatic document scripts default to off, but users can still run
local scripts through Blender. That is intentional for full-feature development testing and is not
by itself an App Store enforcement boundary. Before submission, follow `APP_STORE_CHECKLIST.md` and
either add a tested Store-profile hard gate for user code execution or obtain explicit review and
legal sign-off for the exposed scripting behavior.

References:

- [CPython: Using Python on iOS](https://docs.python.org/3.13/using/ios.html#binary-extension-modules)
- [Blender: Python Wheels](https://docs.blender.org/manual/en/latest/advanced/extensions/python_wheels.html)
- [Apple App Review Guidelines 2.5.2](https://developer.apple.com/app-store/review/guidelines/#software-requirements)
