import importlib.util
import plistlib
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "validate_app.py"
SPEC = importlib.util.spec_from_file_location("validate_app", SCRIPT)
validate_app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_app)


class ValidateAppTests(unittest.TestCase):
    def privacy_manifest(self):
        return {
            "NSPrivacyTracking": False,
            "NSPrivacyTrackingDomains": [],
            "NSPrivacyCollectedDataTypes": [],
            "NSPrivacyAccessedAPITypes": [
                {
                    "NSPrivacyAccessedAPIType": "NSPrivacyAccessedAPICategoryFileTimestamp",
                    "NSPrivacyAccessedAPITypeReasons": ["C617.1", "3B52.1"],
                },
                {
                    "NSPrivacyAccessedAPIType": "NSPrivacyAccessedAPICategorySystemBootTime",
                    "NSPrivacyAccessedAPITypeReasons": ["35F9.1"],
                },
                {
                    "NSPrivacyAccessedAPIType": "NSPrivacyAccessedAPICategoryDiskSpace",
                    "NSPrivacyAccessedAPITypeReasons": ["E174.1"],
                },
            ],
        }

    def create_app(self, root):
        app = root / "Blender.app"
        executable = app / "Blender"
        library = app / "Assets" / "lib" / "libdependency.dylib"
        library.parent.mkdir(parents=True)
        executable.write_bytes(b"main")
        library.write_bytes(b"library")
        (app / "Assets.car").write_bytes(b"compiled assets")
        (app / "Main.storyboardc").mkdir()
        (app / "Info.plist").write_bytes(
            plistlib.dumps(
                {
                    "UIDeviceFamily": [1, 2],
                    "UILaunchStoryboardName": "Main",
                    "UIMainStoryboardFile": "Main",
                }
            )
        )
        (app / "PrivacyInfo.xcprivacy").write_bytes(
            plistlib.dumps(self.privacy_manifest())
        )
        python_dir = app / "Assets" / "5.1" / "python" / "lib" / "python3.13"
        python_dir.mkdir(parents=True)
        (python_dir / "_sysconfigdata__ios_arm64-iphoneos.py").write_text(
            "build_time_vars = {'MACHDEP': 'ios', "
            "'EXT_SUFFIX': '.cpython-313-iphoneos.so'}\n"
        )
        return app, executable, library

    def command_runner(self, executable, library, *, main_dependency="@rpath/libdependency.dylib"):
        def run(command):
            tool = command[0]
            path = Path(command[-1])
            if tool == "file":
                if path in {executable, library}:
                    return "Mach-O 64-bit executable arm64"
                return "ASCII text"
            if command[:2] == ["otool", "-L"]:
                dependency = main_dependency if path == executable else "/usr/lib/libSystem.B.dylib"
                return f"{path}:\n\t{dependency} (compatibility version 1.0.0, current version 1.0.0)\n"
            if command[:2] == ["otool", "-l"]:
                if path == executable:
                    return (
                        "Load command 0\n"
                        "          cmd LC_RPATH\n"
                        "      cmdsize 40\n"
                        "         path @loader_path/Assets/lib (offset 12)\n"
                    )
                return ""
            raise AssertionError(command)

        return run

    def test_accepts_closed_app_runtime(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))

            result = validate_app.validate_runtime(
                app,
                command_runner=self.command_runner(executable, library),
            )

            self.assertEqual(result, {"loadable_machos": 2})

    def test_accepts_scene_delegate_without_main_storyboard(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            info_path = app / "Info.plist"
            info = plistlib.loads(info_path.read_bytes())
            info.pop("UIMainStoryboardFile")
            info["UIApplicationSceneManifest"] = {
                "UISceneConfigurations": {
                    "UIWindowSceneSessionRoleApplication": [
                        {"UISceneDelegateClassName": "IOSSceneDelegate"}
                    ]
                }
            }
            info_path.write_bytes(plistlib.dumps(info))

            result = validate_app.validate_runtime(
                app,
                command_runner=self.command_runner(executable, library),
            )

            self.assertEqual(result, {"loadable_machos": 2})

    def test_rejects_app_without_main_storyboard_or_scene_delegate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            info_path = app / "Info.plist"
            info = plistlib.loads(info_path.read_bytes())
            info.pop("UIMainStoryboardFile")
            info_path.write_bytes(plistlib.dumps(info))

            with self.assertRaisesRegex(ValueError, "missing app startup configuration"):
                validate_app.validate_runtime(
                    app,
                    command_runner=self.command_runner(executable, library),
                )

    def test_rejects_missing_app_privacy_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            (app / "PrivacyInfo.xcprivacy").unlink()

            with self.assertRaisesRegex(ValueError, "missing app privacy manifest"):
                validate_app.validate_runtime(
                    app,
                    command_runner=self.command_runner(executable, library),
                )

    def test_rejects_missing_compiled_asset_catalog(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            (app / "Assets.car").unlink()

            with self.assertRaisesRegex(ValueError, "missing compiled asset catalog"):
                validate_app.validate_runtime(
                    app,
                    command_runner=self.command_runner(executable, library),
                )

    def test_rejects_missing_compiled_storyboard(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            (app / "Main.storyboardc").rmdir()

            with self.assertRaisesRegex(ValueError, "missing compiled launch storyboard"):
                validate_app.validate_runtime(
                    app,
                    command_runner=self.command_runner(executable, library),
                )

    def test_rejects_missing_python_framework_privacy_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            python = app / "Frameworks" / "Python.framework" / "Python"
            python.parent.mkdir(parents=True)
            python.write_bytes(b"python")

            with self.assertRaisesRegex(ValueError, "missing Python framework privacy manifest"):
                validate_app.validate_runtime(
                    app,
                    command_runner=self.command_runner(executable, library),
                )

    def test_rejects_missing_rpath_dependency(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))

            with self.assertRaisesRegex(ValueError, "unresolved dependency"):
                validate_app.validate_runtime(
                    app,
                    command_runner=self.command_runner(
                        executable,
                        library,
                        main_dependency="@rpath/libmissing.dylib",
                    ),
                )

    def test_rejects_nonportable_absolute_dependency(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))

            with self.assertRaisesRegex(ValueError, "nonportable dependency"):
                validate_app.validate_runtime(
                    app,
                    command_runner=self.command_runner(
                        executable,
                        library,
                        main_dependency="/private/build/libdependency.dylib",
                    ),
                )

    def test_rejects_python_extension_outside_frameworks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            extension = (
                app
                / "Assets"
                / "5.1"
                / "python"
                / "lib"
                / "python3.13"
                / "site-packages"
                / "numpy"
                / "_core"
                / "_multiarray_umath.cpython-313-iphoneos.so"
            )
            extension.parent.mkdir(parents=True)
            extension.write_bytes(b"extension")
            base_runner = self.command_runner(executable, library)

            def run(command):
                path = Path(command[-1])
                if path != extension:
                    return base_runner(command)
                if command[0] == "file":
                    return "Mach-O 64-bit bundle arm64"
                if command[:2] == ["otool", "-L"]:
                    return (
                        f"{path}:\n\t/usr/lib/libSystem.B.dylib "
                        "(compatibility version 1.0.0, current version 1.0.0)\n"
                    )
                if command[:2] == ["otool", "-l"]:
                    return ""
                raise AssertionError(command)

            with self.assertRaisesRegex(ValueError, "Python extension outside Frameworks"):
                validate_app.validate_runtime(app, command_runner=run)

    def test_rejects_app_without_loadable_macho(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))

            with self.assertRaisesRegex(ValueError, "no loadable Mach-O"):
                validate_app.validate_runtime(app, command_runner=lambda command: "ASCII text")

    def test_rejects_darwin_python_runtime_for_ios(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            python_dir = app / "Assets" / "5.1" / "python" / "lib" / "python3.13"
            (python_dir / "_sysconfigdata__ios_arm64-iphoneos.py").unlink()
            (python_dir / "_sysconfigdata__darwin_arm64-iphoneos.py").write_text(
                "build_time_vars = {'MACHDEP': 'darwin', 'EXT_SUFFIX': "
                "'.cpython-313-arm64-iphoneos.so'}\n"
            )

            with self.assertRaisesRegex(ValueError, "Python runtime is not configured for iOS"):
                validate_app.validate_runtime(
                    app,
                    command_runner=self.command_runner(executable, library),
                )

    def test_rejects_missing_python_sysconfig(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            (
                app
                / "Assets"
                / "5.1"
                / "python"
                / "lib"
                / "python3.13"
                / "_sysconfigdata__ios_arm64-iphoneos.py"
            ).unlink()

            with self.assertRaisesRegex(ValueError, "missing Python sysconfig file"):
                validate_app.validate_runtime(
                    app,
                    command_runner=self.command_runner(executable, library),
                )

    def test_rejects_python_framework_marker_with_wrong_extension_suffix(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            python_dir = app / "Assets" / "5.1" / "python" / "lib" / "python3.13"
            (python_dir / "_sysconfigdata__ios_arm64-iphoneos.py").unlink()
            module_dir = python_dir / "site-packages" / "numpy" / "_core"
            module_dir.mkdir(parents=True)
            (python_dir / "_sysconfigdata__ios_arm64-iphoneos.py").write_text(
                "build_time_vars = {'MACHDEP': 'ios', "
                "'EXT_SUFFIX': '.cpython-313-iphoneos.so'}\n"
            )
            (module_dir / "_multiarray_umath.cpython-313-arm64-iphoneos.fwork").write_text(
                "Frameworks/numpy._core._multiarray_umath.framework/"
                "numpy._core._multiarray_umath\n"
            )

            with self.assertRaisesRegex(ValueError, "Python framework marker has wrong suffix"):
                validate_app.validate_runtime(
                    app,
                    command_runner=self.command_runner(executable, library),
                )

    def test_accepts_ios_python_framework_marker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            python_dir = app / "Assets" / "5.1" / "python" / "lib" / "python3.13"
            module_dir = python_dir / "site-packages" / "numpy" / "_core"
            module_dir.mkdir(parents=True)
            (python_dir / "_sysconfigdata__ios_arm64-iphoneos.py").write_text(
                "build_time_vars = {'MACHDEP': 'ios', "
                "'EXT_SUFFIX': '.cpython-313-iphoneos.so'}\n"
            )
            (module_dir / "_multiarray_umath.cpython-313-iphoneos.fwork").write_text(
                "Frameworks/numpy._core._multiarray_umath.framework/"
                "numpy._core._multiarray_umath\n"
            )
            framework = (
                app
                / "Frameworks"
                / "numpy._core._multiarray_umath.framework"
            )
            framework.mkdir(parents=True)
            (framework / "numpy._core._multiarray_umath").write_bytes(b"framework")
            (framework / "numpy._core._multiarray_umath.origin").write_text(
                f"{(module_dir / '_multiarray_umath.cpython-313-iphoneos.fwork').relative_to(app).as_posix()}\n"
            )
            framework_binary = framework / "numpy._core._multiarray_umath"
            base_runner = self.command_runner(executable, library)

            def run(command):
                if Path(command[-1]) == framework_binary and command[0] == "file":
                    return "Mach-O 64-bit bundle arm64"
                return base_runner(command)

            result = validate_app.validate_runtime(
                app,
                command_runner=run,
            )

            self.assertEqual(result, {"loadable_machos": 3})

    def test_rejects_python_framework_marker_with_missing_executable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            python_dir = app / "Assets" / "5.1" / "python" / "lib" / "python3.13"
            module_dir = python_dir / "site-packages" / "numpy" / "_core"
            module_dir.mkdir(parents=True)
            marker = module_dir / "_multiarray_umath.cpython-313-iphoneos.fwork"
            marker.write_text(
                "Frameworks/numpy._core._multiarray_umath.framework/"
                "numpy._core._multiarray_umath\n"
            )

            with self.assertRaisesRegex(ValueError, "framework executable"):
                validate_app.validate_runtime(
                    app,
                    command_runner=self.command_runner(executable, library),
                )

    def test_rejects_python_framework_marker_outside_frameworks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            python_dir = app / "Assets" / "5.1" / "python" / "lib" / "python3.13"
            module_dir = python_dir / "site-packages" / "numpy" / "_core"
            module_dir.mkdir(parents=True)
            marker = module_dir / "_multiarray_umath.cpython-313-iphoneos.fwork"
            marker.write_text("Assets/not-a-framework\n")
            target = app / "Assets" / "not-a-framework"
            target.write_bytes(b"placeholder")
            (app / "Assets" / "not-a-framework.origin").write_text(
                f"{marker.relative_to(app).as_posix()}\n"
            )
            base_runner = self.command_runner(executable, library)

            def run(command):
                if Path(command[-1]) == target and command[0] == "file":
                    return "Mach-O 64-bit bundle arm64"
                return base_runner(command)

            with self.assertRaisesRegex(ValueError, "invalid target"):
                validate_app.validate_runtime(app, command_runner=run)

    def test_rejects_python_framework_marker_with_missing_origin(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            python_dir = app / "Assets" / "5.1" / "python" / "lib" / "python3.13"
            module_dir = python_dir / "site-packages" / "numpy" / "_core"
            module_dir.mkdir(parents=True)
            marker = module_dir / "_multiarray_umath.cpython-313-iphoneos.fwork"
            marker.write_text(
                "Frameworks/numpy._core._multiarray_umath.framework/"
                "numpy._core._multiarray_umath\n"
            )
            framework = (
                app
                / "Frameworks"
                / "numpy._core._multiarray_umath.framework"
            )
            framework.mkdir(parents=True)
            target = framework / "numpy._core._multiarray_umath"
            target.write_bytes(b"framework")
            base_runner = self.command_runner(executable, library)

            def run(command):
                if Path(command[-1]) == target and command[0] == "file":
                    return "Mach-O 64-bit bundle arm64"
                return base_runner(command)

            with self.assertRaisesRegex(ValueError, "missing origin"):
                validate_app.validate_runtime(app, command_runner=run)

    def test_rejects_python_framework_marker_with_mismatched_origin(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            python_dir = app / "Assets" / "5.1" / "python" / "lib" / "python3.13"
            module_dir = python_dir / "site-packages" / "numpy" / "_core"
            module_dir.mkdir(parents=True)
            marker = module_dir / "_multiarray_umath.cpython-313-iphoneos.fwork"
            marker.write_text(
                "Frameworks/numpy._core._multiarray_umath.framework/"
                "numpy._core._multiarray_umath\n"
            )
            framework = (
                app
                / "Frameworks"
                / "numpy._core._multiarray_umath.framework"
            )
            framework.mkdir(parents=True)
            (framework / "numpy._core._multiarray_umath").write_bytes(b"framework")
            (framework / "numpy._core._multiarray_umath.origin").write_text(
                "Assets/5.1/python/lib/python3.13/site-packages/other.fwork\n"
            )

            with self.assertRaisesRegex(ValueError, "origin"):
                validate_app.validate_runtime(
                    app,
                    command_runner=self.command_runner(executable, library),
                )

    def test_rejects_python_framework_marker_with_non_macho_executable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            python_dir = app / "Assets" / "5.1" / "python" / "lib" / "python3.13"
            module_dir = python_dir / "site-packages" / "numpy" / "_core"
            module_dir.mkdir(parents=True)
            marker = module_dir / "_multiarray_umath.cpython-313-iphoneos.fwork"
            marker.write_text(
                "Frameworks/numpy._core._multiarray_umath.framework/"
                "numpy._core._multiarray_umath\n"
            )
            framework = (
                app
                / "Frameworks"
                / "numpy._core._multiarray_umath.framework"
            )
            framework.mkdir(parents=True)
            (framework / "numpy._core._multiarray_umath").write_bytes(b"placeholder")
            (framework / "numpy._core._multiarray_umath.origin").write_text(
                f"{marker.relative_to(app).as_posix()}\n"
            )

            with self.assertRaisesRegex(ValueError, "loadable Mach-O"):
                validate_app.validate_runtime(
                    app,
                    command_runner=self.command_runner(executable, library),
                )

    def test_allows_only_xcode_xctest_support_dependencies_when_requested(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            xctest_support = app / "Frameworks" / "XCTest.framework" / "XCTest"
            xctest_support.parent.mkdir(parents=True)
            xctest_support.write_bytes(b"xctest support")

            def run(command):
                path = Path(command[-1])
                if command[0] == "file":
                    if path in {executable, library, xctest_support}:
                        return "Mach-O 64-bit executable arm64"
                    return "ASCII text"
                if command[:2] == ["otool", "-L"]:
                    if path == executable:
                        dependency = "@rpath/libdependency.dylib"
                    elif path == xctest_support:
                        dependency = "/Developer/Library/PrivateFrameworks/XCTestSupport.framework/XCTestSupport"
                    else:
                        dependency = "/usr/lib/libSystem.B.dylib"
                    return f"{path}:\n\t{dependency} (compatibility version 1.0.0, current version 1.0.0)\n"
                if command[:2] == ["otool", "-l"]:
                    if path == executable:
                        return (
                            "Load command 0\n"
                            "          cmd LC_RPATH\n"
                            "      cmdsize 40\n"
                            "         path @loader_path/Assets/lib (offset 12)\n"
                        )
                    return ""
                raise AssertionError(command)

            with self.assertRaisesRegex(ValueError, "nonportable dependency"):
                validate_app.validate_runtime(app, command_runner=run)

            result = validate_app.validate_runtime(
                app,
                command_runner=run,
                allow_xctest_support=True,
            )

            self.assertEqual(result, {"loadable_machos": 3})

    def test_xctest_mode_still_rejects_non_xcode_framework_dependencies(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))
            user_framework = app / "Frameworks" / "User.framework" / "User"
            user_framework.parent.mkdir(parents=True)
            user_framework.write_bytes(b"user framework")

            base_runner = self.command_runner(executable, library)

            def run(command):
                path = Path(command[-1])
                if path != user_framework:
                    return base_runner(command)
                if command[0] == "file":
                    return "Mach-O 64-bit executable arm64"
                if command[:2] == ["otool", "-L"]:
                    return f"{path}:\n\t/private/build/User (compatibility version 1.0.0, current version 1.0.0)\n"
                if command[:2] == ["otool", "-l"]:
                    return ""
                raise AssertionError(command)

            with self.assertRaisesRegex(ValueError, "nonportable dependency"):
                validate_app.validate_runtime(
                    app,
                    command_runner=run,
                    allow_xctest_support=True,
                )


if __name__ == "__main__":
    unittest.main()
