import json
import os
import traceback

import bpy


output_dir = os.path.expanduser("~/Documents/BlenderIOSQA")
report_path = os.path.join(output_dir, "report.json")
run_id = os.environ.get("BLENDER_IOS_QA_RUN_ID", "manual")


def run():
    report = {"status": "failed", "run_id": run_id}
    try:
        import numpy

        os.makedirs(output_dir, exist_ok=True)

        cube = bpy.data.objects["Cube"]
        cube.location = (1.25, -2.5, 3.75)
        assert tuple(cube.location) == (1.25, -2.5, 3.75)
        assert int(numpy.arange(4).sum()) == 6

        blend_path = os.path.join(output_dir, "device-smoke.blend")
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)
        assert os.path.getsize(blend_path) > 0

        scene = bpy.context.scene
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.render.resolution_x = 64
        scene.render.resolution_y = 64
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        render_path = os.path.join(output_dir, "render.png")
        scene.render.filepath = render_path
        assert bpy.ops.render.render(write_still=True) == {"FINISHED"}
        assert os.path.getsize(render_path) > 0

        screenshot_path = os.path.join(output_dir, "screen.png")
        assert bpy.ops.screen.screenshot(filepath=screenshot_path) == {"FINISHED"}
        assert os.path.getsize(screenshot_path) > 0

        report = {
            "status": "passed",
            "run_id": run_id,
            "blender_version": bpy.app.version_string,
            "cube_location": list(cube.location),
            "numpy_sum": int(numpy.arange(4).sum()),
            "blend_bytes": os.path.getsize(blend_path),
            "render_bytes": os.path.getsize(render_path),
            "screenshot_bytes": os.path.getsize(screenshot_path),
        }
    except BaseException:
        report["traceback"] = traceback.format_exc()
    finally:
        os.makedirs(output_dir, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as report_file:
            json.dump(report, report_file, indent=2)


bpy.app.timers.register(run, first_interval=3.0)
