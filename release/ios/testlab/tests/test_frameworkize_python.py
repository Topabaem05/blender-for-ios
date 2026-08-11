import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "frameworkize_python.py"
PLATFORM_APPLE = Path(__file__).parents[4] / "build_files/cmake/platform/platform_apple.cmake"


class FrameworkizePythonTests(unittest.TestCase):
    def test_moves_extension_into_framework_and_writes_loader_markers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app = Path(temp_dir) / "Blender.app"
            module_root = (
                app
                / "Assets"
                / "5.1"
                / "python"
                / "lib"
                / "python3.13"
                / "site-packages"
            )
            extension = (
                module_root
                / "numpy"
                / "_core"
                / "_multiarray_umath.cpython-313-iphoneos.so"
            )
            extension.parent.mkdir(parents=True)
            extension.write_bytes(b"extension")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(app),
                    str(module_root),
                    "--bundle-identifier",
                    "org.example.blender",
                    "--platform",
                    "iPhoneOS",
                    "--minimum-os",
                    "16.6",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            module_name = "numpy._core._multiarray_umath"
            framework = app / "Frameworks" / f"{module_name}.framework"
            binary = framework / module_name
            marker = extension.with_suffix(".fwork")
            self.assertFalse(extension.exists())
            self.assertEqual(binary.read_bytes(), b"extension")
            self.assertEqual(
                marker.read_text(),
                f"Frameworks/{module_name}.framework/{module_name}\n",
            )
            self.assertEqual(
                (framework / f"{module_name}.origin").read_text(),
                f"{marker.relative_to(app).as_posix()}\n",
            )
            with (framework / "Info.plist").open("rb") as plist_file:
                info = plistlib.load(plist_file)
            self.assertEqual(info["CFBundleExecutable"], module_name)
            self.assertEqual(
                info["CFBundleIdentifier"],
                "org.example.blender.numpy.-core.-multiarray-umath",
            )
            self.assertEqual(info["CFBundlePackageType"], "FMWK")
            self.assertEqual(info["CFBundleSupportedPlatforms"], ["iPhoneOS"])
            self.assertEqual(info["MinimumOSVersion"], "16.6")


class PlatformAppleTests(unittest.TestCase):
    def test_selects_an_available_python_runtime_for_ios(self):
        source = PLATFORM_APPLE.read_text()

        self.assertIn('if(EXISTS "${PYTHON_FRAMEWORK_DIR}/Python")', source)
        self.assertIn(
            'elseif(EXISTS "${PYTHON_LIBPATH}/libpython${PYTHON_VERSION}.a")',
            source,
        )
        self.assertIn(
            'set(PYTHON_LIBRARY "${PYTHON_LIBPATH}/libpython${PYTHON_VERSION}.a")',
            source,
        )


if __name__ == "__main__":
    unittest.main()
