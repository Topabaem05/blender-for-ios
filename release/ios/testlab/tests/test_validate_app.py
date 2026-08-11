import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "validate_app.py"
SPEC = importlib.util.spec_from_file_location("validate_app", SCRIPT)
validate_app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_app)


class ValidateAppTests(unittest.TestCase):
    def create_app(self, root):
        app = root / "Blender.app"
        executable = app / "Blender"
        library = app / "Assets" / "lib" / "libdependency.dylib"
        library.parent.mkdir(parents=True)
        executable.write_bytes(b"main")
        library.write_bytes(b"library")
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

    def test_rejects_app_without_loadable_macho(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app, executable, library = self.create_app(Path(temp_dir))

            with self.assertRaisesRegex(ValueError, "no loadable Mach-O"):
                validate_app.validate_runtime(app, command_runner=lambda command: "ASCII text")

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
