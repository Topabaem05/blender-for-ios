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
INTERFACE_HANDLERS = (
    Path(__file__).parents[4]
    / "source"
    / "blender"
    / "editors"
    / "interface"
    / "interface_handlers.cc"
)


class DeviceQAScriptTests(unittest.TestCase):
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
        self.assertIn("i=lambda s,c,e:", probe)
        self.assertNotIn("search_menu", probe)
        for unsafe_literal in ("__setitem__('", "n(b'", "type('", "search_menu('"):
            self.assertNotIn(unsafe_literal, probe)
        expression = "".join(re.findall(r'@?"([^"]*)"', probe))
        compile(expression, "<software-keyboard-probe>", "exec")

    def test_software_keyboard_uses_active_button_region(self):
        source = INTERFACE_HANDLERS.read_text(encoding="utf-8")
        ios_text_edit = source.split("#if (WITH_APPLE_CROSSPLATFORM)", 1)[1]
        ios_text_edit = ios_text_edit.split("#endif", 1)[0]
        self.assertIn("ARegion *region = data->region;", ios_text_edit)
        self.assertNotIn("ARegion *region = CTX_wm_region(C);", ios_text_edit)

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
