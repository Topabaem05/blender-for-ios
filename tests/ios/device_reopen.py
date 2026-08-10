import json
import os
import traceback

import bpy


output_dir = os.path.expanduser("~/Documents/BlenderIOSQA")
report_path = os.path.join(output_dir, "reopen-report.json")
run_id = os.environ.get("BLENDER_IOS_QA_RUN_ID", "manual")


def write_report(report):
    os.makedirs(output_dir, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as report_file:
        json.dump(report, report_file, indent=2)


def verify_reopened_file():
    report = {"status": "failed", "run_id": run_id}
    try:
        blend_path = os.path.join(output_dir, "device-smoke.blend")
        cube = bpy.data.objects["Cube"]
        assert tuple(cube.location) == (1.25, -2.5, 3.75)

        screenshot_path = os.path.join(output_dir, "reopen-screen.png")
        assert bpy.ops.screen.screenshot(filepath=screenshot_path) == {"FINISHED"}
        assert os.path.getsize(screenshot_path) > 0

        report = {
            "status": "passed",
            "run_id": run_id,
            "cube_location": list(cube.location),
            "blend_bytes": os.path.getsize(blend_path),
            "screenshot_bytes": os.path.getsize(screenshot_path),
        }
    except BaseException:
        report["traceback"] = traceback.format_exc()
    finally:
        write_report(report)


def open_file():
    try:
        blend_path = os.path.join(output_dir, "device-smoke.blend")
        assert os.path.getsize(blend_path) > 0
        assert bpy.ops.wm.open_mainfile(filepath=blend_path) == {"FINISHED"}
        bpy.app.timers.register(verify_reopened_file, first_interval=3.0)
    except BaseException:
        write_report(
            {"status": "failed", "run_id": run_id, "traceback": traceback.format_exc()}
        )


bpy.app.timers.register(open_file, first_interval=3.0)
