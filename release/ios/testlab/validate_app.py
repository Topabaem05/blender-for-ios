import argparse
import ast
import json
import pathlib
import plistlib
import subprocess


SYSTEM_DEPENDENCY_PREFIXES = ("/System/Library/", "/usr/lib/")
XCTEST_SUPPORT_NAMES = {
    "Testing.framework",
    "XCTAutomationSupport.framework",
    "XCTest.framework",
    "XCTestCore.framework",
    "XCTestSupport.framework",
    "XCUIAutomation.framework",
    "XCUnit.framework",
    "libXCTestBundleInject.dylib",
    "libXCTestSwiftSupport.dylib",
}
EXPECTED_PRIVACY_API_REASONS = {
    "NSPrivacyAccessedAPICategoryFileTimestamp": ["C617.1", "3B52.1"],
    "NSPrivacyAccessedAPICategorySystemBootTime": ["35F9.1"],
    "NSPrivacyAccessedAPICategoryDiskSpace": ["E174.1"],
}


def run_command(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(f"command failed: {command[0]}")
    return result.stdout


def is_loadable_macho(description):
    return "Mach-O" in description and any(
        marker in description
        for marker in ("executable", "dynamically linked shared library", "bundle")
    )


def dependencies(output):
    return [
        line.strip().split(" (", 1)[0]
        for line in output.splitlines()[1:]
        if line.strip()
    ]


def rpaths(output):
    lines = output.splitlines()
    found = []
    for index, line in enumerate(lines):
        if line.strip() != "cmd LC_RPATH":
            continue
        for candidate in lines[index + 1 : index + 6]:
            stripped = candidate.strip()
            if stripped.startswith("path "):
                found.append(stripped.split(" ", 2)[1])
                break
    return found


def expand_path(value, owner, executable):
    if value == "@loader_path":
        return owner.parent
    if value.startswith("@loader_path/"):
        return owner.parent / value[len("@loader_path/") :]
    if value == "@executable_path":
        return executable.parent
    if value.startswith("@executable_path/"):
        return executable.parent / value[len("@executable_path/") :]
    if value.startswith("@"):
        return None
    return pathlib.Path(value)


def dependency_exists(dependency, owner, executable, owner_rpaths, executable_rpaths):
    if dependency.startswith("@rpath/"):
        suffix = dependency[len("@rpath/") :]
        search_paths = [
            (value, owner) for value in owner_rpaths
        ] + [
            (value, executable) for value in executable_rpaths
        ]
        for value, relative_owner in search_paths:
            expanded = expand_path(value, relative_owner, executable)
            if expanded is not None and (expanded / suffix).exists():
                return True
        return False
    expanded = expand_path(dependency, owner, executable)
    return expanded is not None and expanded.exists()


def is_xctest_support(relative_path):
    return (
        len(relative_path.parts) >= 2
        and relative_path.parts[0] == "Frameworks"
        and relative_path.parts[1] in XCTEST_SUPPORT_NAMES
    )


def validate_python_runtime(app_dir):
    sysconfig_files = sorted(
        app_dir.glob("Assets/*/python/lib/python*/_sysconfigdata__*.py")
    )
    if not sysconfig_files:
        raise ValueError("Blender.app is missing Python sysconfig file")
    if len(sysconfig_files) != 1:
        raise ValueError("Blender.app must contain exactly one Python sysconfig file")

    source = sysconfig_files[0].read_text(encoding="utf-8")
    assignment = ast.parse(source).body[0]
    if not isinstance(assignment, ast.Assign) or not isinstance(assignment.value, ast.Dict):
        raise ValueError("Python sysconfig file has an unexpected format")
    config = ast.literal_eval(assignment.value)
    if config.get("MACHDEP") != "ios":
        raise ValueError("Python runtime is not configured for iOS")

    extension_suffix = config.get("EXT_SUFFIX")
    if not isinstance(extension_suffix, str) or not extension_suffix.endswith(".so"):
        raise ValueError("Python sysconfig does not define an extension suffix")
    marker_suffix = extension_suffix[:-3] + ".fwork"
    python_root = sysconfig_files[0].parent
    framework_targets = []
    for marker in python_root.rglob("*.fwork"):
        if not marker.name.endswith(marker_suffix):
            raise ValueError(
                f"Python framework marker has wrong suffix: {marker.relative_to(app_dir)}"
            )
        target_text = marker.read_text(encoding="utf-8").strip()
        target_relative = pathlib.Path(target_text)
        if (
            target_relative.is_absolute()
            or len(target_relative.parts) != 3
            or target_relative.parts[0] != "Frameworks"
            or not target_relative.parts[1].endswith(".framework")
        ):
            raise ValueError(
                f"Python framework marker has invalid target: {marker.relative_to(app_dir)}"
            )
        target = app_dir / target_relative
        if not target.is_file():
            raise ValueError(
                f"Python framework marker references missing framework executable: "
                f"{marker.relative_to(app_dir)}"
            )
        origin = target.parent / f"{target.name}.origin"
        if not origin.is_file():
            raise ValueError(
                f"Python framework marker is missing origin backlink: "
                f"{marker.relative_to(app_dir)}"
            )
        if origin.read_text(encoding="utf-8").strip() != marker.relative_to(app_dir).as_posix():
            raise ValueError(
                f"Python framework marker origin backlink mismatch: "
                f"{marker.relative_to(app_dir)}"
            )
        framework_targets.append(target)
    return framework_targets


def validate_privacy_manifest(path, label):
    if not path.is_file():
        raise ValueError(f"missing {label} privacy manifest")
    with path.open("rb") as manifest_file:
        manifest = plistlib.load(manifest_file)
    api_reasons = {
        item.get("NSPrivacyAccessedAPIType"): item.get("NSPrivacyAccessedAPITypeReasons")
        for item in manifest.get("NSPrivacyAccessedAPITypes", [])
    }
    if (
        manifest.get("NSPrivacyTracking") is not False
        or manifest.get("NSPrivacyTrackingDomains") != []
        or manifest.get("NSPrivacyCollectedDataTypes") != []
        or api_reasons != EXPECTED_PRIVACY_API_REASONS
    ):
        raise ValueError(f"invalid {label} privacy manifest")


def validate_privacy_manifests(app_dir):
    validate_privacy_manifest(app_dir / "PrivacyInfo.xcprivacy", "app")
    python_framework = app_dir / "Frameworks" / "Python.framework"
    if (python_framework / "Python").is_file():
        validate_privacy_manifest(
            python_framework / "PrivacyInfo.xcprivacy",
            "Python framework",
        )


def validate_compiled_resources(app_dir):
    info_path = app_dir / "Info.plist"
    if not info_path.is_file():
        raise ValueError("missing app Info.plist")
    with info_path.open("rb") as info_file:
        info = plistlib.load(info_file)

    if not (app_dir / "Assets.car").is_file():
        raise ValueError("missing compiled asset catalog")
    for key, label in (
        ("UILaunchStoryboardName", "launch"),
        ("UIMainStoryboardFile", "main"),
    ):
        name = info.get(key)
        if not isinstance(name, str) or not (app_dir / f"{name}.storyboardc").exists():
            raise ValueError(f"missing compiled {label} storyboard")


def validate_runtime(app_dir, command_runner=run_command, *, allow_xctest_support=False):
    app_dir = pathlib.Path(app_dir)
    validate_compiled_resources(app_dir)
    validate_privacy_manifests(app_dir)
    python_framework_targets = validate_python_runtime(app_dir)
    executable = app_dir / "Blender"
    if not executable.is_file():
        raise ValueError("missing Blender executable")

    loadable_machos = []
    for path in sorted(candidate for candidate in app_dir.rglob("*") if candidate.is_file()):
        if is_loadable_macho(command_runner(["file", "-b", str(path)])):
            loadable_machos.append(path)
    if not loadable_machos:
        raise ValueError("Blender.app contains no loadable Mach-O files")
    if executable not in loadable_machos:
        raise ValueError("Blender executable is not a loadable Mach-O file")

    executable_rpaths = rpaths(command_runner(["otool", "-l", str(executable)]))
    errors = []
    for target in python_framework_targets:
        if target not in loadable_machos:
            errors.append(
                f"Python framework executable is not a loadable Mach-O file: "
                f"{target.relative_to(app_dir)}"
            )
    for owner in loadable_machos:
        relative_owner = owner.relative_to(app_dir)
        if allow_xctest_support and is_xctest_support(relative_owner):
            continue
        if owner.suffix == ".so" and relative_owner.parts[0] != "Frameworks":
            errors.append(f"Python extension outside Frameworks: {relative_owner}")
        owner_rpaths = rpaths(command_runner(["otool", "-l", str(owner)]))
        for dependency in dependencies(command_runner(["otool", "-L", str(owner)])):
            if dependency.startswith(SYSTEM_DEPENDENCY_PREFIXES):
                continue
            if dependency.startswith("/"):
                errors.append(f"nonportable dependency in {relative_owner}: {dependency}")
            elif not dependency_exists(
                dependency,
                owner,
                executable,
                owner_rpaths,
                executable_rpaths,
            ):
                errors.append(f"unresolved dependency in {relative_owner}: {dependency}")
    if errors:
        raise ValueError("\n".join(errors))
    return {"loadable_machos": len(loadable_machos)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("app_dir", type=pathlib.Path)
    parser.add_argument("--allow-xctest-support", action="store_true")
    arguments = parser.parse_args()
    try:
        result = validate_runtime(
            arguments.app_dir,
            allow_xctest_support=arguments.allow_xctest_support,
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
