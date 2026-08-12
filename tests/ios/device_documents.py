import json
import os
import traceback

import bpy


documents_dir = os.path.expanduser("~/Documents")
output_dir = os.path.join(documents_dir, "BlenderIOSQA")
report_path = os.path.join(output_dir, "documents-report.json")
input_path = os.environ.get(
    "BLENDER_IOS_EXTERNAL_BLEND",
    os.path.join(documents_dir, "blender-5.2-splash.blend"),
)
run_id = os.environ.get("BLENDER_IOS_QA_RUN_ID", "manual")
source_stats = None
saved_bytes = None
export_bytes = None


def write_report(report):
    os.makedirs(output_dir, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as report_file:
        json.dump(report, report_file, indent=2)


def write_failure():
    write_report(
        {
            "status": "failed",
            "run_id": run_id,
            "traceback": traceback.format_exc(),
        }
    )


def export_and_reimport(operator_name, extension):
    export_path = os.path.join(output_dir, "export-test." + extension)
    export_operator = getattr(bpy.ops.wm, operator_name + "_export")
    import_operator = getattr(bpy.ops.wm, operator_name + "_import")

    assert export_operator(
        filepath=export_path,
        export_selected_objects=True,
    ) == {"FINISHED"}
    assert os.path.getsize(export_path) > 0

    bpy.data.objects.remove(bpy.context.active_object, do_unlink=True)
    assert import_operator(filepath=export_path) == {"FINISHED"}
    assert any(item.type == "MESH" for item in bpy.context.selected_objects)
    return os.path.getsize(export_path)


def verify_saved_file():
    try:
        saved_path = os.path.join(output_dir, "blender-5.2-splash-ios.blend")
        assert len(bpy.data.scenes) == source_stats["scenes"]
        assert os.path.samefile(bpy.data.filepath, saved_path)

        screenshot_path = os.path.join(output_dir, "documents-screen.png")
        assert bpy.ops.screen.screenshot(filepath=screenshot_path) == {"FINISHED"}
        assert os.path.getsize(screenshot_path) > 0

        write_report({
            "status": "passed",
            "run_id": run_id,
            "blender_version": bpy.app.version_string,
            "source_stats": source_stats,
            "saved_bytes": saved_bytes,
            "export_bytes": export_bytes,
            "screenshot_bytes": os.path.getsize(screenshot_path),
            "autoexec_enabled": bpy.context.preferences.filepaths.use_scripts_auto_execute,
        })
    except BaseException:
        write_failure()


def verify_source_file():
    global export_bytes, saved_bytes, source_stats
    try:
        assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
        source_stats = {
            "scenes": len(bpy.data.scenes),
            "objects": len(bpy.data.objects),
            "meshes": len(bpy.data.meshes),
        }
        assert source_stats["scenes"] > 0
        assert source_stats["objects"] > 0

        saved_path = os.path.join(output_dir, "blender-5.2-splash-ios.blend")
        assert bpy.ops.wm.save_as_mainfile(
            filepath=saved_path,
            check_existing=False,
            compress=True,
        ) == {"FINISHED"}
        saved_bytes = os.path.getsize(saved_path)
        assert saved_bytes > 0

        export_scene = bpy.data.scenes.new("BlenderIOSExportQA")
        bpy.context.window.scene = export_scene
        bpy.ops.mesh.primitive_cube_add()
        export_bytes = {
            extension: export_and_reimport(operator_name, extension)
            for operator_name, extension in (("obj", "obj"), ("ply", "ply"), ("stl", "stl"))
        }

        assert bpy.ops.wm.open_mainfile(
            filepath=saved_path,
            load_ui=False,
            use_scripts=False,
        ) == {"FINISHED"}
        bpy.app.timers.register(verify_saved_file, first_interval=3.0)
    except BaseException:
        write_failure()


def open_source_file():
    try:
        os.makedirs(output_dir, exist_ok=True)
        assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
        input_realpath = os.path.realpath(input_path)
        documents_realpath = os.path.realpath(documents_dir)
        assert os.path.commonpath((input_realpath, documents_realpath)) == documents_realpath
        assert os.path.getsize(input_path) > 0
        assert bpy.ops.wm.open_mainfile(
            filepath=input_path,
            load_ui=False,
            use_scripts=False,
        ) == {"FINISHED"}
        bpy.app.timers.register(verify_source_file, first_interval=3.0)
    except BaseException:
        write_failure()


bpy.app.timers.register(open_source_file, first_interval=3.0)
