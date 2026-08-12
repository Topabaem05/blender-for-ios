import json
import os
import traceback

import bpy


output_dir = os.path.expanduser("~/Documents/BlenderIOSQA")
report_path = os.path.join(output_dir, "render-engines-report.json")
run_id = os.environ.get("BLENDER_IOS_QA_RUN_ID", "manual")


def render_engine(scene, engine):
    result = {"status": "failed"}
    try:
        scene.render.engine = engine
        if engine == "CYCLES":
            scene.cycles.samples = 1
            scene.cycles.use_denoising = False
            scene.cycles.max_bounces = 1
            scene.cycles.volume_bounces = 0

        render_path = os.path.join(output_dir, engine.lower() + ".png")
        scene.render.filepath = render_path
        assert bpy.ops.render.render(write_still=True) == {"FINISHED"}
        render_bytes = os.path.getsize(render_path)
        assert render_bytes > 0
        result = {"status": "passed", "render_bytes": render_bytes}
    except BaseException:
        result["traceback"] = traceback.format_exc()
    return result


def run():
    report = {"status": "failed", "run_id": run_id}
    scene = bpy.context.scene
    previous = (
        scene.render.engine,
        scene.render.resolution_x,
        scene.render.resolution_y,
        scene.render.resolution_percentage,
        scene.render.filepath,
        scene.render.image_settings.file_format,
    )
    try:
        os.makedirs(output_dir, exist_ok=True)
        assert scene.camera is not None
        scene.render.resolution_x = 64
        scene.render.resolution_y = 64
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"

        available = {
            item.identifier
            for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
        }
        cycles_enabled = os.environ.get("BLENDER_IOS_QA_ENABLE_CYCLES") == "1"
        engines = ("BLENDER_WORKBENCH", "BLENDER_EEVEE", "CYCLES")
        results = {}
        for engine in engines:
            if engine == "CYCLES" and not cycles_enabled:
                results[engine] = {"status": "skipped"}
            else:
                results[engine] = render_engine(scene, engine)
        required = ("BLENDER_WORKBENCH", "BLENDER_EEVEE")
        passed = all(results[engine]["status"] == "passed" for engine in required)
        if cycles_enabled:
            passed = passed and results["CYCLES"]["status"] == "passed"

        screenshot_path = os.path.join(output_dir, "render-engines-screen.png")
        assert bpy.ops.screen.screenshot(filepath=screenshot_path) == {"FINISHED"}
        report = {
            "status": "passed" if passed else "failed",
            "run_id": run_id,
            "available_engines": sorted(available),
            "cycles_enabled": cycles_enabled,
            "results": results,
            "screenshot_bytes": os.path.getsize(screenshot_path),
        }
    except BaseException:
        report["traceback"] = traceback.format_exc()
    finally:
        (
            scene.render.engine,
            scene.render.resolution_x,
            scene.render.resolution_y,
            scene.render.resolution_percentage,
            scene.render.filepath,
            scene.render.image_settings.file_format,
        ) = previous
        os.makedirs(output_dir, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as report_file:
            json.dump(report, report_file, indent=2)


bpy.app.timers.register(run, first_interval=3.0)
