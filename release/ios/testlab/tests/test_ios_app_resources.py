import json
import plistlib
import struct
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).parents[4]
CREATOR_CMAKE = SOURCE_ROOT / "source" / "creator" / "CMakeLists.txt"
PLATFORM_APPLE = SOURCE_ROOT / "build_files" / "cmake" / "platform" / "platform_apple.cmake"
ROOT_CMAKE = SOURCE_ROOT / "CMakeLists.txt"
PRIVACY_MANIFEST = SOURCE_ROOT / "release" / "ios" / "Blender.app" / "PrivacyInfo.xcprivacy"
INFO_PLIST = SOURCE_ROOT / "release" / "ios" / "Blender.app" / "Info.plist"
ENTITLEMENTS = SOURCE_ROOT / "release" / "ios" / "entitlements.plist"
WINDOW_IOS = SOURCE_ROOT / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"
SYSTEM_IOS = SOURCE_ROOT / "intern" / "ghost" / "intern" / "GHOST_SystemIOS.mm"
CREATOR_ARGS = SOURCE_ROOT / "source" / "creator" / "creator_args.cc"
WM_EVENT_SYSTEM = (
    SOURCE_ROOT / "source" / "blender" / "windowmanager" / "intern" / "wm_event_system.cc"
)
WM_FILES = SOURCE_ROOT / "source" / "blender" / "windowmanager" / "intern" / "wm_files.cc"
WM_INIT_EXIT = (
    SOURCE_ROOT / "source" / "blender" / "windowmanager" / "intern" / "wm_init_exit.cc"
)
RNA_USERDEF = SOURCE_ROOT / "source" / "blender" / "makesrna" / "intern" / "rna_userdef.cc"
APP_ICON_SET = (
    SOURCE_ROOT
    / "release"
    / "ios"
    / "Blender.app"
    / "AppIcon.xcassets"
    / "AppIcon.appiconset"
)


class IOSAppResourceTests(unittest.TestCase):
    def test_app_store_profile_hardens_user_code_and_file_import(self):
        root_cmake = ROOT_CMAKE.read_text(encoding="utf-8")
        platform = PLATFORM_APPLE.read_text(encoding="utf-8")
        creator = CREATOR_CMAKE.read_text(encoding="utf-8")
        creator_args = CREATOR_ARGS.read_text(encoding="utf-8")
        wm_events = WM_EVENT_SYSTEM.read_text(encoding="utf-8")
        wm_files = WM_FILES.read_text(encoding="utf-8")
        wm_init = WM_INIT_EXIT.read_text(encoding="utf-8")
        rna_userdef = RNA_USERDEF.read_text(encoding="utf-8")

        self.assertIn('option(WITH_IOS_APP_STORE', root_cmake)
        self.assertIn("WITH_IOS_APP_STORE requires an iOS build", root_cmake)
        self.assertIn("-DWITH_IOS_APP_STORE", platform)
        self.assertIn("BLENDER_IOS_OPEN_IN_PLACE", creator)
        self.assertRegex(creator_args, r"#\s*ifndef WITH_IOS_APP_STORE")
        for operator in (
            '"CONSOLE_OT_execute"',
            '"SCRIPT_OT_python_file_run"',
            '"TEXT_OT_run_script"',
            '"SCRIPT_OT_reload"',
        ):
            self.assertIn(operator, wm_events)
        self.assertIn("RNA_property_boolean_set(op->ptr, prop, false);", wm_files)
        self.assertIn("!defined(WITH_IOS_APP_STORE)", wm_init)
        self.assertIn("bpy.utils.load_scripts_extensions()", wm_init)
        self.assertIn('STREQ(ot->idname, "PREFERENCES_OT_addon_install")', wm_events)
        self.assertIn('STREQ(ot->idname, "PREFERENCES_OT_addon_remove")', wm_events)
        self.assertRegex(rna_userdef, r"#\s*ifdef WITH_IOS_APP_STORE")
        self.assertIn("INFOPLIST_KEY_LSSupportsOpeningDocumentsInPlace", creator)
        self.assertIn("INFOPLIST_KEY_UISupportsDocumentBrowser", creator)

    def test_scene_lifecycle_owns_blender_window_startup(self):
        system_source = SYSTEM_IOS.read_text(encoding="utf-8")
        window_source = WINDOW_IOS.read_text(encoding="utf-8")

        app_delegate = system_source.split("@implementation IOSAppDelegate", 1)[1].split(
            "@end", 1
        )[0]
        scene_delegate = system_source.split("@implementation IOSSceneDelegate", 1)[1].split(
            "@end", 1
        )[0]
        self.assertNotIn("main_ios_callback", app_delegate)
        self.assertIn("willConnectToSession", scene_delegate)
        self.assertIn("main_ios_callback", scene_delegate)
        self.assertIn("handleOpenDocumentRequest", scene_delegate)
        self.assertIn("sceneWillResignActive", scene_delegate)
        self.assertIn("GHOST_kEventWindowDeactivate", scene_delegate)
        self.assertIn("GHOST_kEventWindowActivate", scene_delegate)
        self.assertIn("GHOST_IOSSetSceneWindow", system_source)
        self.assertIn("g_scene_delegate.window = window", system_source)
        self.assertIn("self.window = nil", scene_delegate)
        self.assertIn("initWithWindowScene", window_source)
        self.assertIn("GHOST_IOSSetSceneWindow(rootWindow)", window_source)
        self.assertIn("UIWindowLevelNormal", window_source)
        self.assertIn("shouldAutorotate", window_source)
        self.assertIn("UIInterfaceOrientationMaskAll", window_source)

        with INFO_PLIST.open("rb") as info_file:
            info = plistlib.load(info_file)
        scene_configuration = info["UIApplicationSceneManifest"][
            "UISceneConfigurations"
        ]["UIWindowSceneSessionRoleApplication"][0]
        self.assertEqual(scene_configuration["UISceneDelegateClassName"], "IOSSceneDelegate")
        self.assertNotIn("UIMainStoryboardFile", info)

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
        self.assertTrue(launch_storyboard.is_file())
        self.assertIn(
            'launchScreen="YES"',
            launch_storyboard.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
