import json
import plistlib
import struct
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).parents[4]
CREATOR_CMAKE = SOURCE_ROOT / "source" / "creator" / "CMakeLists.txt"
PLATFORM_APPLE = SOURCE_ROOT / "build_files" / "cmake" / "platform" / "platform_apple.cmake"
PRIVACY_MANIFEST = SOURCE_ROOT / "release" / "ios" / "Blender.app" / "PrivacyInfo.xcprivacy"
INFO_PLIST = SOURCE_ROOT / "release" / "ios" / "Blender.app" / "Info.plist"
ENTITLEMENTS = SOURCE_ROOT / "release" / "ios" / "entitlements.plist"
WINDOW_IOS = SOURCE_ROOT / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"
APP_ICON_SET = (
    SOURCE_ROOT
    / "release"
    / "ios"
    / "Blender.app"
    / "AppIcon.xcassets"
    / "AppIcon.appiconset"
)


class IOSAppResourceTests(unittest.TestCase):
    def test_fullscreen_frame_is_applied_to_new_window(self):
        source = WINDOW_IOS.read_text(encoding="utf-8")
        self.assertIn(
            "CGRect rect = [UIScreen mainScreen].bounds;\n"
            "    ghost_rootWindow.frame = rect;",
            source,
        )

    def test_app_icon_is_connected_and_store_ready(self):
        cmake_source = CREATOR_CMAKE.read_text(encoding="utf-8")
        resources = cmake_source.split("set(ios_app_resources", 1)[1].split(")", 1)[0]
        self.assertNotIn("AppIcon.xcassets", resources)
        self.assertIn(
            "set(ios_asset_catalog ${OSX_APP_SOURCEDIR}/AppIcon.xcassets)",
            cmake_source,
        )
        self.assertIn(
            "set_source_files_properties(${ios_asset_catalog} PROPERTIES",
            cmake_source,
        )
        self.assertIn("MACOSX_PACKAGE_LOCATION Resources", cmake_source)
        self.assertIn(
            'XCODE_ATTRIBUTE_ASSETCATALOG_COMPILER_APPICON_NAME "AppIcon"',
            cmake_source,
        )

        contents = json.loads((APP_ICON_SET / "Contents.json").read_text(encoding="utf-8"))
        self.assertEqual(
            contents["images"],
            [
                {
                    "filename": "AppIcon.png",
                    "idiom": "universal",
                    "platform": "ios",
                    "size": "1024x1024",
                }
            ],
        )

        icon = (APP_ICON_SET / "AppIcon.png").read_bytes()
        self.assertEqual(icon[:8], b"\x89PNG\r\n\x1a\n")
        width, height, _bit_depth, color_type = struct.unpack(">IIBB", icon[16:26])
        self.assertEqual((width, height), (1024, 1024))
        self.assertIn(color_type, (0, 2, 3), "App Store icon must not contain alpha")

    def test_privacy_manifest_is_bundled_for_app_and_python(self):
        creator_source = CREATOR_CMAKE.read_text(encoding="utf-8")
        platform_source = PLATFORM_APPLE.read_text(encoding="utf-8")
        self.assertIn("${OSX_APP_SOURCEDIR}/PrivacyInfo.xcprivacy", creator_source)
        self.assertIn("${BLENDER_IOS_PRIVACY_MANIFEST}", platform_source)
        self.assertIn('DESTINATION "./Blender.app/Frameworks/Python.framework"', platform_source)

        with PRIVACY_MANIFEST.open("rb") as manifest_file:
            manifest = plistlib.load(manifest_file)
        self.assertFalse(manifest["NSPrivacyTracking"])
        self.assertEqual(manifest["NSPrivacyTrackingDomains"], [])
        self.assertEqual(manifest["NSPrivacyCollectedDataTypes"], [])
        self.assertEqual(
            {
                item["NSPrivacyAccessedAPIType"]: item["NSPrivacyAccessedAPITypeReasons"]
                for item in manifest["NSPrivacyAccessedAPITypes"]
            },
            {
                "NSPrivacyAccessedAPICategoryFileTimestamp": ["C617.1", "3B52.1"],
                "NSPrivacyAccessedAPICategorySystemBootTime": ["35F9.1"],
                "NSPrivacyAccessedAPICategoryDiskSpace": ["E174.1"],
            },
        )

    def test_memory_limit_is_a_signing_entitlement_only(self):
        with INFO_PLIST.open("rb") as info_file:
            info = plistlib.load(info_file)
        with ENTITLEMENTS.open("rb") as entitlements_file:
            entitlements = plistlib.load(entitlements_file)

        key = "com.apple.developer.kernel.increased-memory-limit"
        self.assertNotIn(key, info)
        self.assertTrue(entitlements[key])

    def test_declared_storyboards_exist(self):
        with INFO_PLIST.open("rb") as info_file:
            info = plistlib.load(info_file)

        app_template = INFO_PLIST.parent
        launch_storyboard = app_template / f"{info['UILaunchStoryboardName']}.storyboard"
        main_storyboard = app_template / f"{info['UIMainStoryboardFile']}.storyboard"
        self.assertTrue(launch_storyboard.is_file())
        self.assertTrue(main_storyboard.is_file())
        self.assertIn(
            'launchScreen="YES"',
            launch_storyboard.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
