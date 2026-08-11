import os
import plistlib
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "build_xctest.sh"


class BuildXCTestTests(unittest.TestCase):
    def write_tool(self, directory, name, body):
        tool = directory / name
        tool.write_text("#!/bin/sh\nset -eu\n" + body)
        tool.chmod(0o755)

    def create_runtime_app(self, root):
        app = root / "Blender.app"
        app.mkdir(parents=True)
        (app / "Info.plist").write_bytes(
            plistlib.dumps(
                {
                    "CFBundleShortVersionString": "5.1.2",
                    "MinimumOSVersion": "16.6",
                    "UIDeviceFamily": [1, 2],
                }
            )
        )
        executable = app / "Blender"
        executable.write_text("runtime executable")
        executable.chmod(0o755)
        for relative_path in (
            "Assets/5.1/scripts/startup.py",
            "Assets/5.1/python/os.py",
            "Assets/lib/libdependency.dylib",
        ):
            asset = app / relative_path
            asset.parent.mkdir(parents=True, exist_ok=True)
            asset.write_text("runtime asset")
        return app

    def create_build_products(self, build_dir):
        (build_dir / "Blender.xcodeproj").mkdir(parents=True)
        app = build_dir / "bin" / "Debug" / "Blender.app"
        test_bundle = app / "PlugIns" / "BlenderFTLTests.xctest"
        test_bundle.mkdir(parents=True)
        executable = app / "Blender"
        executable.write_text("build executable")
        executable.chmod(0o755)
        (test_bundle / "Info.plist").write_bytes(
            plistlib.dumps({"CFBundleName": "BlenderFTLTests"})
        )
        test_executable = test_bundle / "BlenderFTLTests"
        test_executable.write_text("test executable")
        test_executable.chmod(0o755)

        xctestrun = build_dir / "build" / "blender_iphoneos26.5-arm64.xctestrun"
        xctestrun.parent.mkdir()
        xctestrun.write_bytes(
            plistlib.dumps(
                {
                    "BlenderFTLTests": {
                        "TestBundlePath": "__TESTHOST__/PlugIns/BlenderFTLTests.xctest",
                        "TestHostPath": str(app),
                        "DependentProductPaths": [str(app), str(test_bundle)],
                    }
                }
            )
        )

    def create_fake_tools(self, fake_bin):
        self.write_tool(fake_bin, "uname", 'echo Darwin\n')
        self.write_tool(
            fake_bin,
            "xcodebuild",
            'printf "%s\\n" "$@" > "$FAKE_XCODEBUILD_ARGS"\n',
        )
        self.write_tool(
            fake_bin,
            "lipo",
            'printf "%s\\n" "$*" >> "$FAKE_LIPO_ARGS"\n'
            '[ "$#" -eq 3 ]\n'
            'case "$1" in */Blender|*/BlenderFTLTests) ;; *) exit 65;; esac\n'
            '[ "$2" = "-verify_arch" ]\n'
            '[ "$3" = "arm64" ]\n',
        )
        self.write_tool(
            fake_bin,
            "codesign",
            'for argument in "$@"; do\n'
            '  case "$argument" in -d|--display) echo "Authority=Test Identity" >&2; exit 0;; esac\n'
            'done\n'
            'exit 0\n',
        )
        self.write_tool(
            fake_bin,
            "cmake",
            'prefix=\n'
            'while [ "$#" -gt 0 ]; do\n'
            '  if [ "$1" = "--prefix" ]; then shift; prefix=$1; fi\n'
            '  shift\n'
            'done\n'
            '[ -n "$prefix" ]\n'
            '/bin/mkdir -p "$prefix"\n'
            '/usr/bin/ditto "$FAKE_RUNTIME_APP" "$prefix/Blender.app"\n',
        )
        self.write_tool(
            fake_bin,
            "file",
            'last=\n'
            'for argument in "$@"; do last=$argument; done\n'
            'case "$last" in\n'
            '  */Blender|*/BlenderFTLTests) echo "Mach-O 64-bit executable arm64";;\n'
            '  *) echo "ASCII text";;\n'
            'esac\n',
        )
        self.write_tool(
            fake_bin,
            "otool",
            'mode=$1\n'
            'last=\n'
            'for argument in "$@"; do last=$argument; done\n'
            'if [ "$mode" = "-L" ]; then\n'
            '  echo "$last:"\n'
            '  echo "\t/usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1.0.0)"\n'
            'fi\n',
        )

    def test_packages_cmake_install_app_with_hosted_test_and_current_sdk_xctestrun(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            build_dir = temp_path / "build"
            build_dir.mkdir()
            self.create_build_products(build_dir)
            runtime_app = self.create_runtime_app(temp_path / "runtime")
            fake_bin = temp_path / "fake-bin"
            fake_bin.mkdir()
            self.create_fake_tools(fake_bin)
            output_zip = temp_path / "BlenderFTLTests.zip"
            environment = os.environ.copy()
            environment["PATH"] = str(fake_bin) + os.pathsep + environment["PATH"]
            environment["FAKE_RUNTIME_APP"] = str(runtime_app)
            environment["FAKE_XCODEBUILD_ARGS"] = str(temp_path / "xcodebuild-args.txt")
            environment["FAKE_LIPO_ARGS"] = str(temp_path / "lipo-args.txt")
            environment["APPLE_TEAM_ID"] = "TESTTEAM"

            result = subprocess.run(
                ["bash", str(SCRIPT), str(build_dir), str(output_zip)],
                capture_output=True,
                text=True,
                env=environment,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(output_zip) as archive:
                names = set(archive.namelist())
                self.assertIn("Debug-iphoneos/Blender.app/Assets/5.1/scripts/startup.py", names)
                self.assertIn(
                    "Debug-iphoneos/Blender.app/PlugIns/BlenderFTLTests.xctest/BlenderFTLTests",
                    names,
                )
                self.assertIn("blender_iphoneos26.5-arm64.xctestrun", names)
                self.assertEqual(
                    archive.read("Debug-iphoneos/Blender.app/Blender"),
                    b"runtime executable",
                )
            self.assertIn(
                "DEVELOPMENT_TEAM=TESTTEAM",
                Path(environment["FAKE_XCODEBUILD_ARGS"]).read_text().splitlines(),
            )
            lipo_calls = Path(environment["FAKE_LIPO_ARGS"]).read_text().splitlines()
            self.assertEqual(len(lipo_calls), 2)
            self.assertTrue(lipo_calls[0].endswith("/Blender -verify_arch arm64"))
            self.assertTrue(lipo_calls[1].endswith("/BlenderFTLTests -verify_arch arm64"))


if __name__ == "__main__":
    unittest.main()
