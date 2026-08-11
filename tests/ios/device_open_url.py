import json
import os
import time
import traceback

import bpy
from bpy.app.handlers import persistent


documents_dir = os.path.expanduser("~/Documents")
output_dir = os.path.join(documents_dir, "BlenderIOSQA")
fixture_path = os.path.join(documents_dir, "open-url-fixture.blend")
mode = os.environ["BLENDER_IOS_OPEN_URL_MODE"]
run_id = os.environ.get("BLENDER_IOS_QA_RUN_ID", "manual")
marker = "blender-ios-open-url"
report_path = os.path.join(output_dir, "open-url-" + mode + "-report.json")
ready_report_path = os.path.join(output_dir, "open-url-observe-ready.json")
deadline = time.monotonic() + 60.0
completed = False


def write_report(report, path=report_path):
    os.makedirs(output_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as report_file:
        json.dump(report, report_file, indent=2)


def write_failure():
    write_report(
        {
            "status": "failed",
            "mode": mode,
            "run_id": run_id,
            "traceback": traceback.format_exc(),
        }
    )


def create_fixture():
    try:
        bpy.context.scene["ios_open_url_fixture"] = marker
        assert bpy.ops.wm.save_as_mainfile(
            filepath=fixture_path,
            check_existing=False,
            compress=True,
        ) == {"FINISHED"}
        write_report(
            {
                "status": "passed",
                "mode": mode,
                "run_id": run_id,
                "fixture_bytes": os.path.getsize(fixture_path),
            }
        )
    except BaseException:
        write_failure()


def observe_open_url():
    global completed
    if completed:
        return None
    try:
        opened = os.path.basename(bpy.data.filepath) == os.path.basename(fixture_path)
        marked = any(scene.get("ios_open_url_fixture") == marker for scene in bpy.data.scenes)
        if opened and marked:
            screenshot_path = os.path.join(output_dir, "open-url-screen.png")
            assert bpy.ops.screen.screenshot(filepath=screenshot_path) == {"FINISHED"}
            write_report(
                {
                    "status": "passed",
                    "mode": mode,
                    "run_id": run_id,
                    "opened_filename": os.path.basename(bpy.data.filepath),
                    "screenshot_bytes": os.path.getsize(screenshot_path),
                    "autoexec_enabled": bpy.context.preferences.filepaths.use_scripts_auto_execute,
                }
            )
            completed = True
            return None
        if time.monotonic() < deadline:
            return 1.0
        raise AssertionError("openURL payload was not loaded before the deadline")
    except BaseException:
        write_failure()
        completed = True
        return None


@persistent
def observe_after_load(_unused):
    if not completed:
        bpy.app.timers.register(observe_open_url, first_interval=1.0)


if mode == "fixture":
    bpy.app.timers.register(create_fixture, first_interval=3.0)
elif mode == "observe":
    write_report({"status": "ready", "mode": mode, "run_id": run_id}, ready_report_path)
    bpy.app.handlers.load_post.append(observe_after_load)
    bpy.app.timers.register(observe_open_url, first_interval=1.0)
else:
    raise ValueError("unsupported BLENDER_IOS_OPEN_URL_MODE")
