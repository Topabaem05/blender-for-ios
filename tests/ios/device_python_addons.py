import json
import os
import sys
import traceback

import addon_utils
import bpy


output_dir = os.path.expanduser("~/Documents/BlenderIOSQA")
report_path = os.path.join(output_dir, "python-addons-report.json")
run_id = os.environ.get("BLENDER_IOS_QA_RUN_ID", "manual")


def run():
    report = {"status": "failed", "run_id": run_id}
    addon_name = "io_curve_svg"
    addon_was_enabled = addon_utils.check(addon_name)[1]
    try:
        os.makedirs(output_dir, exist_ok=True)
        assert sys.platform == "ios"
        assert sys.executable is not None
        assert os.path.dirname(sys.executable) == os.path.dirname(bpy.app.binary_path)

        import numpy
        from bl_pkg import bl_extension_utils

        namespace = {}
        exec("result = sum(range(5))", namespace)
        assert namespace["result"] == 10
        assert int(numpy.arange(4).sum()) == 6

        script_path = os.path.join(output_dir, "user-script.py")
        with open(script_path, "w", encoding="utf-8") as script_file:
            script_file.write(
                "import bpy\n"
                'bpy.context.scene["ios_user_script_result"] = 42\n'
            )
        assert bpy.ops.script.python_file_run(filepath=script_path) == {"FINISHED"}
        assert bpy.context.scene["ios_user_script_result"] == 42

        addon_module = addon_utils.enable(addon_name, default_set=False)
        assert addon_module is not None
        assert addon_utils.check(addon_name)[1]

        extension_messages = []
        for message_batch in bl_extension_utils.pkg_install_files(
                directory=output_dir,
                files=(os.path.join(output_dir, "missing-extension.zip"),),
                blender_version=bpy.app.version,
                python_version=sys.version_info[:3],
                use_idle=False,
                python_args=(),
        ):
            extension_messages.extend(message_batch)

        fatal_messages = [value for message_type, value in extension_messages if message_type == "FATAL_ERROR"]
        assert fatal_messages == [
            "Extension installation and management are unavailable on iOS; use bundled add-ons or scripts."
        ]

        screenshot_path = os.path.join(output_dir, "python-addons-screen.png")
        assert bpy.ops.screen.screenshot(filepath=screenshot_path) == {"FINISHED"}
        assert os.path.getsize(screenshot_path) > 0

        report = {
            "status": "passed",
            "run_id": run_id,
            "platform": sys.platform,
            "python_version": list(sys.version_info[:3]),
            "blender_version": bpy.app.version_string,
            "numpy_sum": int(numpy.arange(4).sum()),
            "user_script_result": bpy.context.scene["ios_user_script_result"],
            "bundled_addon": addon_name,
            "bundled_addon_enabled": True,
            "extension_messages": extension_messages,
            "screenshot_bytes": os.path.getsize(screenshot_path),
        }
    except BaseException:
        report["traceback"] = traceback.format_exc()
    finally:
        if not addon_was_enabled and addon_utils.check(addon_name)[1]:
            addon_utils.disable(addon_name, default_set=False)
        os.makedirs(output_dir, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as report_file:
            json.dump(report, report_file, indent=2)


bpy.app.timers.register(run, first_interval=3.0)
