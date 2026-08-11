import argparse
import json
import pathlib
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


def validate_runtime(app_dir, command_runner=run_command, *, allow_xctest_support=False):
    app_dir = pathlib.Path(app_dir)
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
