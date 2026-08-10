import plistlib
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "package_xctest.py"


def create_products(products_dir, *, minimum_os_version="16.6", device_family=None,
                    xctestrun_name="Blender_iphoneos16.6-arm64.xctestrun"):
    if device_family is None:
        device_family = [1, 2]

    debug_dir = products_dir / "Debug-iphoneos"
    app_dir = debug_dir / "Blender.app"
    app_dir.mkdir(parents=True)
    (app_dir / "Info.plist").write_bytes(plistlib.dumps({
        "MinimumOSVersion": minimum_os_version,
        "UIDeviceFamily": device_family,
    }))
    executable = app_dir / "Blender"
    executable.write_text("device executable")
    executable.chmod(0o755)

    test_bundle = app_dir / "PlugIns" / "BlenderFTLTests.xctest"
    test_bundle.mkdir(parents=True)
    (test_bundle / "Info.plist").write_bytes(plistlib.dumps({"CFBundleName": "BlenderFTLTests"}))
    test_executable = test_bundle / "BlenderFTLTests"
    test_executable.write_text("device test executable")
    test_executable.chmod(0o755)

    (products_dir / xctestrun_name).write_bytes(plistlib.dumps({"FormatVersion": 2}))


class PackageXCTestTests(unittest.TestCase):
    def test_packages_root_relative_device_products(self):
        """Break caught: package command is absent or omits required device products."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            products_dir = temp_path / "products"
            products_dir.mkdir()
            create_products(products_dir)
            output_zip = temp_path / "Blender-xctest.zip"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(products_dir), str(output_zip)],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(output_zip) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {
                        "Debug-iphoneos/Blender.app/Info.plist",
                        "Debug-iphoneos/Blender.app/Blender",
                        "Debug-iphoneos/Blender.app/PlugIns/BlenderFTLTests.xctest/Info.plist",
                        "Debug-iphoneos/Blender.app/PlugIns/BlenderFTLTests.xctest/BlenderFTLTests",
                        "Blender_iphoneos16.6-arm64.xctestrun",
                    },
                )
                self.assertEqual(
                    archive.getinfo("Debug-iphoneos/Blender.app/Blender").external_attr
                    >> 16
                    & 0o777,
                    0o755,
                )
                self.assertEqual(
                    archive.getinfo(
                        "Debug-iphoneos/Blender.app/PlugIns/BlenderFTLTests.xctest/BlenderFTLTests"
                    ).external_attr >> 16 & 0o777,
                    0o755,
                )

    def test_rejects_extra_root_product_directory(self):
        """Break caught: a simulator or Release product is included beside device products."""
        for extra_directory in ("Debug-iphonesimulator", "Release-iphoneos"):
            with (
                self.subTest(extra_directory=extra_directory),
                tempfile.TemporaryDirectory() as temp_dir,
            ):
                temp_path = Path(temp_dir)
                products_dir = temp_path / "products"
                products_dir.mkdir()
                create_products(products_dir)
                (products_dir / extra_directory).mkdir()
                output_zip = temp_path / "Blender-xctest.zip"

                result = subprocess.run(
                    [sys.executable, str(SCRIPT), str(products_dir), str(output_zip)],
                    capture_output=True,
                    text=True,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output_zip.exists())

    def test_rejects_unhosted_sibling_test_bundle(self):
        """Break caught: the XCTest bundle is outside Blender.app/PlugIns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            products_dir = temp_path / "products"
            products_dir.mkdir()
            create_products(products_dir)
            hosted_bundle = (
                products_dir
                / "Debug-iphoneos"
                / "Blender.app"
                / "PlugIns"
                / "BlenderFTLTests.xctest"
            )
            hosted_bundle.rename(products_dir / "Debug-iphoneos" / "BlenderFTLTests.xctest")
            output_zip = temp_path / "Blender-xctest.zip"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(products_dir), str(output_zip)],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output_zip.exists())

    def test_rejects_hosted_test_bundle_without_info_plist(self):
        """Break caught: the hosted XCTest bundle has no Info.plist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            products_dir = temp_path / "products"
            products_dir.mkdir()
            create_products(products_dir)
            (
                products_dir
                / "Debug-iphoneos"
                / "Blender.app"
                / "PlugIns"
                / "BlenderFTLTests.xctest"
                / "Info.plist"
            ).unlink()
            output_zip = temp_path / "Blender-xctest.zip"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(products_dir), str(output_zip)],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output_zip.exists())

    def test_rejects_hosted_test_bundle_without_executable(self):
        """Break caught: the hosted XCTest bundle has no test executable."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            products_dir = temp_path / "products"
            products_dir.mkdir()
            create_products(products_dir)
            (
                products_dir
                / "Debug-iphoneos"
                / "Blender.app"
                / "PlugIns"
                / "BlenderFTLTests.xctest"
                / "BlenderFTLTests"
            ).unlink()
            output_zip = temp_path / "Blender-xctest.zip"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(products_dir), str(output_zip)],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output_zip.exists())

    def test_rejects_multiple_xctestrun_files(self):
        """Break caught: packaging accepts more than one .xctestrun file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            products_dir = temp_path / "products"
            products_dir.mkdir()
            create_products(products_dir)
            (products_dir / "Second_iphoneos16.6-arm64.xctestrun").write_bytes(
                plistlib.dumps({"FormatVersion": 2})
            )
            output_zip = temp_path / "Blender-xctest.zip"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(products_dir), str(output_zip)],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output_zip.exists())

    def test_rejects_iphonesimulator_xctestrun(self):
        """Break caught: packaging accepts a simulator .xctestrun file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            products_dir = temp_path / "products"
            products_dir.mkdir()
            create_products(
                products_dir,
                xctestrun_name="Blender_iphonesimulator16.6-arm64.xctestrun",
            )
            output_zip = temp_path / "Blender-xctest.zip"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(products_dir), str(output_zip)],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output_zip.exists())

    def test_rejects_device_name_without_required_underscore(self):
        """Break caught: packaging accepts a device-like name without the required underscore."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            products_dir = temp_path / "products"
            products_dir.mkdir()
            create_products(
                products_dir,
                xctestrun_name="Blenderiphoneos16.6-arm64.xctestrun",
            )
            output_zip = temp_path / "Blender-xctest.zip"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(products_dir), str(output_zip)],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output_zip.exists())

    def test_rejects_incorrect_minimum_os_version(self):
        """Break caught: packaging accepts an app that requires iOS 18.0."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            products_dir = temp_path / "products"
            products_dir.mkdir()
            create_products(products_dir, minimum_os_version="18.0")
            output_zip = temp_path / "Blender-xctest.zip"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(products_dir), str(output_zip)],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output_zip.exists())

    def test_rejects_git_lfs_pointer_in_app_bundle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            products_dir = temp_path / "products"
            products_dir.mkdir()
            create_products(products_dir)
            asset = products_dir / "Debug-iphoneos" / "Blender.app" / "Assets" / "startup.blend"
            asset.parent.mkdir()
            asset.write_text(
                "version https://git-lfs.github.com/spec/v1\n"
                "oid sha256:" + "0" * 64 + "\n"
                "size 123\n"
            )
            output_zip = temp_path / "Blender-xctest.zip"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(products_dir), str(output_zip)],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output_zip.exists())

    def test_accepts_reordered_universal_device_family(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            products_dir = temp_path / "products"
            products_dir.mkdir()
            create_products(products_dir, device_family=[2, 1])
            output_zip = temp_path / "Blender-xctest.zip"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(products_dir), str(output_zip)],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output_zip.is_file())

    def test_rejects_non_universal_device_families(self):
        invalid_families = (
            [],
            [1],
            [2],
            [1, 1, 2],
            [1, 2, 3],
            ["1", 2],
            [True, 2],
        )
        for device_family in invalid_families:
            with (
                self.subTest(device_family=device_family),
                tempfile.TemporaryDirectory() as temp_dir,
            ):
                temp_path = Path(temp_dir)
                products_dir = temp_path / "products"
                products_dir.mkdir()
                create_products(products_dir, device_family=device_family)
                output_zip = temp_path / "Blender-xctest.zip"

                result = subprocess.run(
                    [sys.executable, str(SCRIPT), str(products_dir), str(output_zip)],
                    capture_output=True,
                    text=True,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output_zip.exists())


if __name__ == "__main__":
    unittest.main()
