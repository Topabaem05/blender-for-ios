import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "run_simulator_probe.py"


def load_probe_module():
    spec = importlib.util.spec_from_file_location("simulator_probe", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SimulatorProbeTests(unittest.TestCase):
    def test_run_probe_stages_launches_and_collects_matching_report(self):
        # Given: a booted simulator data container and a fake simctl runner.
        simulator_probe = load_probe_module()
        commands = []
        environments = []

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            container = temp_path / "Data"
            probe = temp_path / "device_smoke.py"
            probe.write_text("print('probe')\n", encoding="utf-8")

            def run(command, environment):
                commands.append(command)
                environments.append(environment)
                if command[2] == "get_app_container":
                    return f"{container}\n"
                report = container / "Documents" / "BlenderIOSQA" / "report.json"
                report.parent.mkdir(parents=True, exist_ok=True)
                report.write_text(
                    json.dumps(
                        {
                            "status": "passed",
                            "run_id": "run-42",
                            "screenshot_bytes": 7,
                            "results": {"render": {"render_bytes": 5}},
                        }
                    ),
                    encoding="utf-8",
                )
                return "launch-id\n"

            request = simulator_probe.ProbeRequest(
                simulator_id="simulator-42",
                bundle_identifier="org.example.blender",
                probe_path=probe,
                run_id="run-42",
                report_name="report.json",
                timeout_seconds=1.0,
                poll_interval_seconds=0.1,
            )
            runtime = simulator_probe.ProbeRuntime(
                command_runner=run,
                monotonic=lambda: 0.0,
                sleeper=lambda _seconds: self.fail(
                    "matching report should be immediate"
                ),
            )

            # When: the reusable host-side probe runner launches the app.
            result = simulator_probe.run_probe(request, runtime)

            # Then: it uses argv-only simctl calls and verifies report identity and artifacts.
            self.assertEqual(
                commands[0],
                [
                    "xcrun",
                    "simctl",
                    "get_app_container",
                    "simulator-42",
                    "org.example.blender",
                    "data",
                ],
            )
            self.assertEqual(
                commands[1][:7],
                [
                    "xcrun",
                    "simctl",
                    "launch",
                    "--terminate-running-process",
                    "simulator-42",
                    "org.example.blender",
                    "--python-expr",
                ],
            )
            self.assertEqual(
                environments[1]["SIMCTL_CHILD_BLENDER_IOS_QA_RUN_ID"],
                "run-42",
            )
            self.assertEqual(result.artifact_bytes, 12)
            self.assertEqual(result.report["run_id"], "run-42")
            self.assertEqual(
                result.staged_probe.read_text(encoding="utf-8"), "print('probe')\n"
            )

    def test_run_probe_waits_for_ready_report_before_terminal_report(self):
        # Given: a lifecycle probe that first writes a ready report.
        simulator_probe = load_probe_module()
        sleep_calls = []

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            container = temp_path / "Data"
            probe = temp_path / "device_lifecycle.py"
            probe.write_text("print('lifecycle')\n", encoding="utf-8")
            report = container / "Documents" / "BlenderIOSQA" / "lifecycle-report.json"

            def run(command, _environment):
                if command[2] == "get_app_container":
                    return str(container)
                report.parent.mkdir(parents=True, exist_ok=True)
                report.write_text(
                    json.dumps({"status": "ready", "run_id": "resume-7"}),
                    encoding="utf-8",
                )
                return "launch-id"

            def sleep(seconds):
                sleep_calls.append(seconds)
                report.write_text(
                    json.dumps(
                        {
                            "status": "passed",
                            "run_id": "resume-7",
                            "screenshot_bytes": 9,
                        }
                    ),
                    encoding="utf-8",
                )

            request = simulator_probe.ProbeRequest(
                simulator_id="simulator-7",
                bundle_identifier="org.example.blender",
                probe_path=probe,
                run_id="resume-7",
                report_name="lifecycle-report.json",
                timeout_seconds=1.0,
                poll_interval_seconds=0.25,
            )
            runtime = simulator_probe.ProbeRuntime(
                command_runner=run,
                monotonic=lambda: 0.0,
                sleeper=sleep,
            )

            # When: the report moves from ready to passed.
            result = simulator_probe.run_probe(request, runtime)

            # Then: polling continues until the terminal report is present.
            self.assertEqual(sleep_calls, [0.25])
            self.assertEqual(result.artifact_bytes, 9)

    def test_run_probe_rejects_stale_run_id(self):
        # Given: a report path containing a prior run's result.
        simulator_probe = load_probe_module()
        elapsed = [0.0]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            container = temp_path / "Data"
            probe = temp_path / "device_render_engines.py"
            probe.write_text("print('render')\n", encoding="utf-8")

            def run(command, _environment):
                if command[2] == "get_app_container":
                    return str(container)
                report = (
                    container
                    / "Documents"
                    / "BlenderIOSQA"
                    / "render-engines-report.json"
                )
                report.parent.mkdir(parents=True, exist_ok=True)
                report.write_text(
                    json.dumps(
                        {"status": "passed", "run_id": "older", "screenshot_bytes": 8}
                    ),
                    encoding="utf-8",
                )
                return "launch-id"

            request = simulator_probe.ProbeRequest(
                simulator_id="simulator-9",
                bundle_identifier="org.example.blender",
                probe_path=probe,
                run_id="current",
                report_name="render-engines-report.json",
                timeout_seconds=1.0,
                poll_interval_seconds=0.1,
            )
            runtime = simulator_probe.ProbeRuntime(
                command_runner=run,
                monotonic=lambda: elapsed[0],
                sleeper=lambda seconds: elapsed.__setitem__(
                    0, elapsed[0] + seconds
                ),
            )

            # When: the harness reads the named report after launching.
            with self.assertRaisesRegex(simulator_probe.ProbeError, "timed out"):
                simulator_probe.run_probe(request, runtime)

            # Then: it does not treat the stale run as a passing result.

    def test_run_probe_waits_when_exiting_process_rewrites_stale_report(self):
        simulator_probe = load_probe_module()
        elapsed = [0.0]
        sleep_calls = []

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            container = temp_path / "Data"
            probe = temp_path / "device_documents.py"
            probe.write_text("print('documents')\n", encoding="utf-8")
            report = container / "Documents" / "BlenderIOSQA" / "documents-report.json"

            def run(command, _environment):
                if command[2] == "get_app_container":
                    return str(container)
                report.parent.mkdir(parents=True, exist_ok=True)
                report.write_text(
                    json.dumps(
                        {
                            "status": "passed",
                            "run_id": "previous",
                            "screenshot_bytes": 5,
                        }
                    ),
                    encoding="utf-8",
                )
                return "launch-id"

            def sleep(seconds):
                sleep_calls.append(seconds)
                elapsed[0] += seconds
                report.write_text(
                    json.dumps(
                        {
                            "status": "passed",
                            "run_id": "current",
                            "screenshot_bytes": 9,
                        }
                    ),
                    encoding="utf-8",
                )

            request = simulator_probe.ProbeRequest(
                simulator_id="simulator-documents",
                bundle_identifier="org.example.blender",
                probe_path=probe,
                run_id="current",
                report_name="documents-report.json",
                timeout_seconds=1.0,
                poll_interval_seconds=0.1,
            )
            runtime = simulator_probe.ProbeRuntime(
                command_runner=run,
                monotonic=lambda: elapsed[0],
                sleeper=sleep,
            )

            result = simulator_probe.run_probe(request, runtime)

            self.assertEqual(sleep_calls, [0.1])
            self.assertEqual(result.report["run_id"], "current")
            self.assertEqual(result.artifact_bytes, 9)

    def test_run_probe_removes_same_run_report_before_launch(self):
        # Given: a named report from an earlier run that reused the current run ID.
        simulator_probe = load_probe_module()
        elapsed = [0.0]
        report_at_launch = []

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            container = temp_path / "Data"
            qa_dir = container / "Documents" / "BlenderIOSQA"
            report = qa_dir / "report.json"
            report.parent.mkdir(parents=True)
            report.write_text(
                json.dumps(
                    {"status": "passed", "run_id": "reused", "screenshot_bytes": 5}
                ),
                encoding="utf-8",
            )
            sibling = qa_dir / "keep.txt"
            sibling.write_text("preserve", encoding="utf-8")
            probe = temp_path / "device_smoke.py"
            probe.write_text("print('probe')\n", encoding="utf-8")

            def run(command, _environment):
                if command[2] == "get_app_container":
                    return str(container)
                report_at_launch.append(report.exists())
                return "launch-id"

            request = simulator_probe.ProbeRequest(
                simulator_id="simulator-freshness",
                bundle_identifier="org.example.blender",
                probe_path=probe,
                run_id="reused",
                report_name="report.json",
                timeout_seconds=0.5,
                poll_interval_seconds=0.25,
            )
            runtime = simulator_probe.ProbeRuntime(
                command_runner=run,
                monotonic=lambda: elapsed[0],
                sleeper=lambda seconds: elapsed.__setitem__(0, elapsed[0] + seconds),
            )

            # When: a new launch starts with that exact report name and reused run ID.
            with self.assertRaisesRegex(simulator_probe.ProbeError, "timed out"):
                simulator_probe.run_probe(request, runtime)

            # Then: the old report cannot satisfy the new launch and siblings are untouched.
            self.assertEqual(report_at_launch, [False])
            self.assertFalse(report.exists())
            self.assertEqual(sibling.read_text(encoding="utf-8"), "preserve")

    def test_cli_uses_simctl_without_a_real_simulator(self):
        # Given: a fake xcrun executable and a temporary simulator app container.
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fake_bin = temp_path / "bin"
            fake_bin.mkdir()
            container = temp_path / "Data"
            probe = temp_path / "device_python_addons.py"
            probe.write_text("print('addons')\n", encoding="utf-8")
            xcrun = fake_bin / "xcrun"
            xcrun.write_text(
                "#!/bin/sh\n"
                'if [ "$2" = get_app_container ]; then\n'
                "  printf '%s\\n' \"$FAKE_APP_CONTAINER\"\n"
                "  exit 0\n"
                "fi\n"
                'mkdir -p "$FAKE_APP_CONTAINER/Documents/BlenderIOSQA"\n'
                'printf \'{\\"status\\":\\"passed\\",\\"run_id\\":\\"%s\\",\\"screenshot_bytes\\":11}\' \\\n'
                '  "$SIMCTL_CHILD_BLENDER_IOS_QA_RUN_ID" > \\\n'
                '  "$FAKE_APP_CONTAINER/Documents/BlenderIOSQA/python-addons-report.json"\n',
                encoding="utf-8",
            )
            xcrun.chmod(0o755)
            environment = os.environ | {
                "PATH": str(fake_bin) + os.pathsep + os.environ["PATH"],
                "FAKE_APP_CONTAINER": str(container),
            }

            # When: the CLI launches the supplied app bundle and probe identifiers.
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--simulator-id",
                    "simulator-cli",
                    "--bundle-identifier",
                    "org.example.blender",
                    "--probe",
                    str(probe),
                    "--run-id",
                    "cli-11",
                    "--report-name",
                    "python-addons-report.json",
                ],
                capture_output=True,
                text=True,
                env=environment,
            )

            # Then: the JSON output contains the validated report outcome.
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(output["artifact_bytes"], 11)
            self.assertEqual(output["report"]["run_id"], "cli-11")


if __name__ == "__main__":
    unittest.main()
