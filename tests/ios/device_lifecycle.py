import json
import os
import traceback

import bpy


output_dir = os.path.expanduser("~/Documents/BlenderIOSQA")
report_path = os.path.join(output_dir, "lifecycle-report.json")
run_id = os.environ.get("BLENDER_IOS_QA_RUN_ID", "manual")


def write_report(report):
    os.makedirs(output_dir, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as report_file:
        json.dump(report, report_file, indent=2)


def verify_resume():
    report = {"status": "failed", "run_id": run_id}
    try:
        cube = bpy.data.objects["Cube"]
        assert tuple(cube.location) == (4.0, 5.0, 6.0)

        screenshot_path = os.path.join(output_dir, "lifecycle-screen.png")
        assert bpy.ops.screen.screenshot(filepath=screenshot_path) == {"FINISHED"}
        assert os.path.getsize(screenshot_path) > 0

        report = {
            "status": "passed",
            "run_id": run_id,
            "cube_location": list(cube.location),
            "screenshot_bytes": os.path.getsize(screenshot_path),
        }
    except BaseException:
        report["traceback"] = traceback.format_exc()
    finally:
        write_report(report)


def arm_test():
    cube = bpy.data.objects["Cube"]
    cube.location = (4.0, 5.0, 6.0)
    write_report({"status": "ready", "run_id": run_id})
    bpy.app.timers.register(verify_resume, first_interval=12.0)


bpy.app.timers.register(arm_test, first_interval=3.0)
