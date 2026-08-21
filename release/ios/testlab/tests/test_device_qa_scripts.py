import builtins
import json
import os
import re
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


SMOKE_SCRIPT = Path(__file__).parents[4] / "tests" / "ios" / "device_smoke.py"
RENDER_SCRIPT = Path(__file__).parents[4] / "tests" / "ios" / "device_render_engines.py"
PYTHON_ADDONS_SCRIPT = Path(__file__).parents[4] / "tests" / "ios" / "device_python_addons.py"
DOCUMENTS_SCRIPT = Path(__file__).parents[4] / "tests" / "ios" / "device_documents.py"
OPEN_URL_SCRIPT = Path(__file__).parents[4] / "tests" / "ios" / "device_open_url.py"
UI_TESTS = Path(__file__).parents[4] / "tests" / "ios" / "BlenderUITests.m"
WINDOW_IOS = (
    Path(__file__).parents[4]
    / "intern"
    / "ghost"
    / "intern"
    / "GHOST_WindowIOS.mm"
)
INTERFACE_HANDLERS = (
    Path(__file__).parents[4]
    / "source"
    / "blender"
    / "editors"
    / "interface"
    / "interface_handlers.cc"
)
GPU_SHADER_CREATE_INFO = (
    Path(__file__).parents[4]
    / "source"
    / "blender"
    / "gpu"
    / "intern"
    / "gpu_shader_create_info.cc"
)
METAL_BACKEND = (
    Path(__file__).parents[4]
    / "source"
    / "blender"
    / "gpu"
    / "metal"
    / "mtl_backend.mm"
)
METAL_FRAMEBUFFER = (
    Path(__file__).parents[4]
    / "source"
    / "blender"
    / "gpu"
    / "metal"
    / "mtl_framebuffer.mm"
)
METAL_FRAMEBUFFER_HEADER = (
    Path(__file__).parents[4]
    / "source"
    / "blender"
    / "gpu"
    / "metal"
    / "mtl_framebuffer.hh"
)
METAL_SHADER = (
    Path(__file__).parents[4]
    / "source"
    / "blender"
    / "gpu"
    / "metal"
    / "mtl_shader.mm"
)
DEFERRED_CLASSIFY_SHADER = (
    Path(__file__).parents[4]
    / "source"
    / "blender"
    / "draw"
    / "engines"
    / "eevee"
    / "shaders"
    / "eevee_deferred_tile_classify_frag.glsl"
)


class DeviceQAScriptTests(unittest.TestCase):
    def test_simulator_deferred_tile_classifier_uses_image_read_fallback(self):
        create_info = GPU_SHADER_CREATE_INFO.read_text(encoding="utf-8")
        metal_backend = METAL_BACKEND.read_text(encoding="utf-8")
        metal_framebuffer = METAL_FRAMEBUFFER.read_text(encoding="utf-8")
        shader = DEFERRED_CLASSIFY_SHADER.read_text(encoding="utf-8")

        self.assertIn("#  include <TargetConditionals.h>", create_info)
        self.assertIn("#if TARGET_OS_SIMULATOR", create_info)
        self.assertIn("eevee_deferred_tile_classify.subpass_inputs_.clear();", create_info)
        self.assertIn(
            'eevee_deferred_tile_classify.image(1,',
            create_info,
        )
        self.assertIn(
            'eevee_deferred_tile_classify.define("EEVEE_DEFERRED_TILE_CLASSIFY_IMAGE_READ");',
            create_info,
        )
        self.assertRegex(
            metal_backend,
            r"#if TARGET_OS_SIMULATOR\s+"
            r"MTLBackend::capabilities\.supports_native_tile_inputs = false;",
        )
        self.assertIn("detached_subpass_attachments_", metal_framebuffer)
        self.assertIn("this->remove_color_attachment(i);", metal_framebuffer)
        self.assertIn("this->add_color_attachment(", metal_framebuffer)
        self.assertIn("#if TARGET_OS_SIMULATOR", metal_framebuffer)
        self.assertIn("#ifdef EEVEE_DEFERRED_TILE_CLASSIFY_IMAGE_READ", shader)
        self.assertIn(
            "imageLoad(in_gbuffer_header, int3(int2(gl_FragCoord.xy), 0)).r",
            shader,
        )

    def test_simulator_attachmentless_raster_uses_matching_dummy_target(self):
        framebuffer_header = METAL_FRAMEBUFFER_HEADER.read_text(encoding="utf-8")
        framebuffer = METAL_FRAMEBUFFER.read_text(encoding="utf-8")
        shader = METAL_SHADER.read_text(encoding="utf-8")

        self.assertIn("attachmentless_dummy_texture_", framebuffer_header)
        self.assertIn("ensure_attachmentless_dummy_texture", framebuffer_header)
        self.assertIn("MTLPixelFormatR8Unorm", framebuffer)
        self.assertIn("MTLTextureUsageRenderTarget", framebuffer)
        self.assertIn("MTLStorageModePrivate", framebuffer)
        self.assertIn("attachmentless_dummy_texture_ release", framebuffer)
        self.assertIn(
            "attachment.texture = this->ensure_attachmentless_dummy_texture()",
            framebuffer,
        )
        self.assertIn("attachment.storeAction = MTLStoreActionDontCare", framebuffer)
        self.assertRegex(
            framebuffer,
            r"(?s)#if TARGET_OS_SIMULATOR.*?total_num_attachments == 0.*?"
            r"ensure_attachmentless_dummy_texture",
        )
        self.assertRegex(
            shader,
            r"(?s)#if TARGET_OS_SIMULATOR.*?num_color_attachments == 0.*?"
            r"MTLPixelFormatR8Unorm",
        )

    def test_document_probes_reject_enabled_auto_execution(self):
        required_guard = (
            "assert not bpy.context.preferences.filepaths.use_scripts_auto_execute"
        )
        for script in (DOCUMENTS_SCRIPT, OPEN_URL_SCRIPT):
            source = script.read_text(encoding="utf-8")
            self.assertIn(required_guard, source, script.name)

    def test_python_probe_runs_a_documents_script_with_blender(self):
        source = PYTHON_ADDONS_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('script_path = os.path.join(output_dir, "user-script.py")', source)
        self.assertIn(
            'bpy.ops.script.python_file_run(filepath=script_path) == {"FINISHED"}',
            source,
        )
        self.assertIn('bpy.context.scene["ios_user_script_result"] == 42', source)

    def test_render_engine_probe_has_device_safe_limits(self):
        source = RENDER_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('resolution_x = 64', source)
        self.assertIn('resolution_y = 64', source)
        self.assertIn('scene.cycles.samples = 1', source)
        self.assertIn('scene.cycles.use_denoising = False', source)
        self.assertIn('BLENDER_IOS_QA_ENABLE_CYCLES', source)

    def test_software_keyboard_probe_survives_argv_quote_stripping(self):
        source = UI_TESTS.read_text(encoding="utf-8")
        probe = source.split("- (void)testSoftwareKeyboardCommitsTextToBlender", 1)[1]
        probe = probe.split("app.launchArguments", 1)[0]
        probe = probe.split("NSString *probe =", 1)[1]

        self.assertIn("S=lambda *v:bytes(v).decode()", probe)
        self.assertIn("invoke_props_dialog", probe)
        self.assertIn("cursor_warp", probe)
        self.assertIn("update=u", probe)
        self.assertIn("i=lambda s,c,e:", probe)
        self.assertNotIn("search_menu", probe)
        for unsafe_literal in ("__setitem__('", "n(b'", "type('", "search_menu('"):
            self.assertNotIn(unsafe_literal, probe)
        expression = "".join(re.findall(r'@?"([^"]*)"', probe))
        compile(expression, "<software-keyboard-probe>", "exec")

        test_body = source.split("- (void)testSoftwareKeyboardCommitsTextToBlender", 1)[1]
        test_body = test_body.split("- (void)testEditorSurvivesPortraitAndLandscapeRotation", 1)[0]
        self.assertIn("XCTDarwinNotificationExpectation *ready", test_body)
        self.assertIn("CGVectorMake(0.51, 0.47)", test_body)

    def test_software_keyboard_toolbar_actions_target_the_window(self):
        source = WINDOW_IOS.read_text(encoding="utf-8")
        toolbar = source.split("- (void)initToolbar", 1)[1].split(
            "- (void)generateKeyboardReturnEvent", 1
        )[0]
        self.assertEqual(toolbar.count("target:self"), 2)

    def test_software_keyboard_uses_active_button_region(self):
        source = INTERFACE_HANDLERS.read_text(encoding="utf-8")
        ios_text_edit = source.split("#if (WITH_APPLE_CROSSPLATFORM)", 1)[1]
        ios_text_edit = ios_text_edit.split("#endif", 1)[0]
        self.assertIn("ARegion *region = data->region;", ios_text_edit)
        self.assertNotIn("ARegion *region = CTX_wm_region(C);", ios_text_edit)

    def test_ui_tests_wait_for_selection_and_window_frame_observations(self):
        source = UI_TESTS.read_text(encoding="utf-8")
        viewport_test = source.split("- (void)testViewportTapSelectsCube", 1)[1]
        viewport_test = viewport_test.split("- (void)testAppleKeyboardShortcutsReachBlender", 1)[0]
        rotation_test = source.split("- (void)testEditorSurvivesPortraitAndLandscapeRotation", 1)[1]

        self.assertIn('@"org.blender.ios.ui-test.selected"', viewport_test)
        self.assertIn("XCTDarwinNotificationExpectation", viewport_test)
        self.assertIn("XCTWaiter waitForExpectations:@[ selected ]", viewport_test)
        self.assertNotIn("sleepForTimeInterval", viewport_test)

        probe = viewport_test.split("NSString *probe =", 1)[1]
        probe = probe.split("app.launchEnvironment", 1)[0]
        expression = "".join(re.findall(r'@?"([^"]*)"', probe))
        compile(expression, "<viewport-selection-probe>", "exec")

        notifications = []
        callbacks = []

        class Cube:
            def __init__(self):
                self.location = None
                self.selected = True

            def select_set(self, selected):
                self.selected = selected

            def select_get(self):
                return self.selected

        cube = Cube()
        fake_bpy = types.ModuleType("bpy")
        fake_bpy.data = types.SimpleNamespace(objects={"Cube": cube})
        fake_bpy.context = types.SimpleNamespace(
            view_layer=types.SimpleNamespace(objects=types.SimpleNamespace(active=cube))
        )
        fake_bpy.app = types.SimpleNamespace(
            timers=types.SimpleNamespace(
                register=lambda callback, **kwargs: callbacks.append((callback, kwargs))
            )
        )
        fake_ctypes = types.ModuleType("ctypes")
        fake_ctypes.CDLL = lambda _name: types.SimpleNamespace(
            notify_post=lambda notification: notifications.append(notification.decode())
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                mock.patch.dict(os.environ, {"HOME": temp_dir}, clear=False),
                mock.patch.dict(sys.modules, {"bpy": fake_bpy, "ctypes": fake_ctypes}),
            ):
                exec(compile(expression, "<viewport-selection-probe>", "exec"), {})
                persistent_callbacks = [
                    callback for callback, kwargs in callbacks if kwargs.get("persistent")
                ]
                self.assertEqual(len(persistent_callbacks), 1)
                persistent_callback = persistent_callbacks[0]
                persistent_callback()
                cube.select_set(True)
                persistent_callback()
                persistent_callback()
                self.assertEqual(notifications.count("org.blender.ios.ui-test.selected"), 1)

        self.assertNotIn("sleepForTimeInterval", rotation_test)
        self.assertIn('XCTDarwinNotificationExpectation *ready', rotation_test)
        self.assertIn('app.launchArguments = @[ @"--python-expr", probe ]', rotation_test)
        self.assertIn("XCTWaiter waitForExpectations:@[ ready ]", rotation_test)
        self.assertIn("app.windows.firstMatch", rotation_test)
        self.assertNotIn("mainWindowPredicate", rotation_test)
        rotation_probe = rotation_test.split("NSString *probe =", 1)[1]
        rotation_probe = rotation_probe.split("app.launchArguments", 1)[0]
        self.assertIn("S=lambda *v:bytes(v).decode()", rotation_probe)
        self.assertNotIn("b'", rotation_probe)
        expression = "".join(re.findall(r'@?"([^"]*)"', rotation_probe))
        compile(expression, "<rotation-ready-probe>", "exec")
        self.assertEqual(rotation_test.count("initWithPredicate:"), 2)
        self.assertEqual(rotation_test.count("XCTWaiter waitForExpectations"), 3)
        self.assertRegex(rotation_test, r"frame\.size\.height\s*>\s*frame\.size\.width")
        self.assertRegex(rotation_test, r"frame\.size\.width\s*>\s*frame\.size\.height")

    def test_render_engine_probe_attempts_required_engine_missing_from_enum(self):
        source = RENDER_SCRIPT.read_text(encoding="utf-8")
        render_calls = []

        class Render:
            engine = "BLENDER_EEVEE"
            resolution_x = 1920
            resolution_y = 1080
            resolution_percentage = 100
            filepath = ""
            image_settings = types.SimpleNamespace(file_format="PNG")

        class Scene:
            camera = object()
            render = Render()
            cycles = types.SimpleNamespace(
                samples=16,
                use_denoising=True,
                max_bounces=12,
                volume_bounces=2,
            )

        scene = Scene()

        def render(write_still):
            self.assertTrue(write_still)
            render_calls.append(scene.render.engine)
            Path(scene.render.filepath).write_bytes(b"png")
            return {"FINISHED"}

        fake_bpy = types.ModuleType("bpy")
        fake_bpy.context = types.SimpleNamespace(scene=scene)
        fake_bpy.types = types.SimpleNamespace(
            RenderSettings=types.SimpleNamespace(
                bl_rna=types.SimpleNamespace(
                    properties={
                        "engine": types.SimpleNamespace(
                            enum_items=[types.SimpleNamespace(identifier="BLENDER_EEVEE")]
                        )
                    }
                )
            )
        )
        fake_bpy.ops = types.SimpleNamespace(
            render=types.SimpleNamespace(render=render),
            screen=types.SimpleNamespace(
                screenshot=lambda filepath: (Path(filepath).write_bytes(b"png"), {"FINISHED"})[1]
            ),
        )
        fake_bpy.app = types.SimpleNamespace(
            timers=types.SimpleNamespace(register=lambda callback, **_kwargs: callback())
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                mock.patch.dict(os.environ, {"HOME": temp_dir}, clear=False),
                mock.patch.dict(sys.modules, {"bpy": fake_bpy}),
            ):
                exec(compile(source, str(RENDER_SCRIPT), "exec"), {"__name__": "__main__"})

            report_path = Path(temp_dir) / "Documents" / "BlenderIOSQA" / "render-engines-report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["results"]["BLENDER_WORKBENCH"]["status"], "passed")
            self.assertIn("BLENDER_WORKBENCH", render_calls)
            self.assertIn("BLENDER_EEVEE", render_calls)
            self.assertEqual(report["results"]["CYCLES"]["status"], "skipped")

            with (
                mock.patch.dict(os.environ, {"HOME": temp_dir, "BLENDER_IOS_QA_ENABLE_CYCLES": "1"}, clear=False),
                mock.patch.dict(sys.modules, {"bpy": fake_bpy}),
            ):
                exec(compile(source, str(RENDER_SCRIPT), "exec"), {"__name__": "__main__"})
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["results"]["CYCLES"]["status"], "passed")
            self.assertIn("CYCLES", render_calls)

    def test_render_engine_progress_persists_before_render_exception(self):
        source = RENDER_SCRIPT.read_text(encoding="utf-8")

        class Render:
            engine = "BLENDER_EEVEE"
            resolution_x = 1920
            resolution_y = 1080
            resolution_percentage = 100
            filepath = ""
            image_settings = types.SimpleNamespace(file_format="PNG")

        class Scene:
            camera = object()
            render = Render()
            cycles = types.SimpleNamespace(
                samples=16,
                use_denoising=True,
                max_bounces=12,
                volume_bounces=2,
            )

        scene = Scene()
        callbacks = []
        progress_at_failure = []

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "Documents" / "BlenderIOSQA"
            progress_path = output_dir / "render-engines-progress.json"

            def render(write_still):
                self.assertTrue(write_still)
                if scene.render.engine == "BLENDER_WORKBENCH":
                    progress_at_failure.append(
                        json.loads(progress_path.read_text(encoding="utf-8"))
                    )
                    raise RuntimeError("planned render failure")
                Path(scene.render.filepath).write_bytes(b"png")
                return {"FINISHED"}

            fake_bpy = types.ModuleType("bpy")
            fake_bpy.context = types.SimpleNamespace(scene=scene)
            fake_bpy.types = types.SimpleNamespace(
                RenderSettings=types.SimpleNamespace(
                    bl_rna=types.SimpleNamespace(
                        properties={
                            "engine": types.SimpleNamespace(
                                enum_items=[types.SimpleNamespace(identifier="BLENDER_EEVEE")]
                            )
                        }
                    )
                )
            )
            fake_bpy.ops = types.SimpleNamespace(
                render=types.SimpleNamespace(render=render),
                screen=types.SimpleNamespace(
                    screenshot=lambda filepath: (
                        Path(filepath).write_bytes(b"png"),
                        {"FINISHED"},
                    )[1]
                ),
            )
            fake_bpy.app = types.SimpleNamespace(
                timers=types.SimpleNamespace(
                    register=lambda callback, **_kwargs: callbacks.append(callback)
                )
            )

            environment = {
                "HOME": temp_dir,
                "BLENDER_IOS_QA_RUN_ID": "progress-render-exception",
            }
            with (
                mock.patch.dict(os.environ, environment, clear=False),
                mock.patch.dict(sys.modules, {"bpy": fake_bpy}),
            ):
                exec(compile(source, str(RENDER_SCRIPT), "exec"), {"__name__": "__main__"})
                self.assertEqual(len(callbacks), 1)
                callbacks[0]()

            self.assertEqual(
                progress_at_failure,
                [
                    {
                        "engine": "BLENDER_WORKBENCH",
                        "phase": "render-started",
                        "run_id": "progress-render-exception",
                    }
                ],
            )
            self.assertEqual(
                json.loads(progress_path.read_text(encoding="utf-8")),
                {
                    "engine": "BLENDER_EEVEE",
                    "phase": "engine-finished",
                    "run_id": "progress-render-exception",
                },
            )

            report_path = output_dir / "render-engines-report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(
                set(report),
                {
                    "status",
                    "run_id",
                    "available_engines",
                    "cycles_enabled",
                    "results",
                    "screenshot_bytes",
                },
            )
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["run_id"], "progress-render-exception")
            self.assertEqual(report["results"]["BLENDER_WORKBENCH"]["status"], "failed")
            self.assertEqual(
                report["results"]["BLENDER_EEVEE"],
                {"status": "passed", "render_bytes": 3},
            )
            self.assertEqual(report["results"]["CYCLES"], {"status": "skipped"})

    def test_smoke_writes_report_when_numpy_import_fails(self):
        source = SMOKE_SCRIPT.read_text(encoding="utf-8")
        original_import = builtins.__import__

        def import_with_numpy_failure(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "numpy":
                raise ImportError("numpy unavailable")
            return original_import(name, globals, locals, fromlist, level)

        fake_bpy = types.ModuleType("bpy")
        fake_bpy.app = types.SimpleNamespace(
            timers=types.SimpleNamespace(register=lambda callback, **_kwargs: callback())
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            environment = {
                "HOME": temp_dir,
                "BLENDER_IOS_QA_RUN_ID": "numpy-import-failure",
            }
            with (
                mock.patch.dict(os.environ, environment),
                mock.patch.dict(sys.modules, {"bpy": fake_bpy}),
                mock.patch("builtins.__import__", new=import_with_numpy_failure),
            ):
                try:
                    exec(compile(source, str(SMOKE_SCRIPT), "exec"), {"__name__": "__main__"})
                except ImportError:
                    pass

            report_path = Path(temp_dir) / "Documents" / "BlenderIOSQA" / "report.json"
            self.assertTrue(report_path.is_file(), "smoke script must persist import failures")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "failed")
            self.assertIn("numpy unavailable", report["traceback"])


if __name__ == "__main__":
    unittest.main()
