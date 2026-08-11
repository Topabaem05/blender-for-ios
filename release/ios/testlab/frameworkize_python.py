import argparse
import json
import pathlib
import plistlib


def frameworkize(app_dir, module_roots, *, bundle_identifier, platform, minimum_os):
    app_dir = pathlib.Path(app_dir).resolve()
    if not app_dir.is_dir():
        raise ValueError(f"missing app bundle: {app_dir}")

    frameworks_dir = app_dir / "Frameworks"
    frameworks_dir.mkdir(exist_ok=True)
    converted = []
    for module_root in module_roots:
        module_root = pathlib.Path(module_root).resolve()
        if not module_root.is_dir():
            raise ValueError(f"missing Python module root: {module_root}")
        try:
            module_root.relative_to(app_dir)
        except ValueError as error:
            raise ValueError(f"Python module root is outside app bundle: {module_root}") from error

        for extension in sorted(module_root.rglob("*.so")):
            relative_module = extension.relative_to(module_root).as_posix()
            module_name = relative_module.split(".", 1)[0].replace("/", ".")
            if not module_name:
                raise ValueError(f"cannot derive module name from: {extension}")

            framework = frameworks_dir / f"{module_name}.framework"
            framework.mkdir(exist_ok=True)
            binary = framework / module_name
            extension.replace(binary)

            marker = extension.with_suffix(".fwork")
            marker.write_text(f"{binary.relative_to(app_dir).as_posix()}\n")
            (framework / f"{module_name}.origin").write_text(
                f"{marker.relative_to(app_dir).as_posix()}\n"
            )
            info = {
                "CFBundleDevelopmentRegion": "en",
                "CFBundleExecutable": module_name,
                "CFBundleIdentifier": f"{bundle_identifier}.{module_name}".replace("_", "-"),
                "CFBundleInfoDictionaryVersion": "6.0",
                "CFBundlePackageType": "FMWK",
                "CFBundleShortVersionString": "1.0",
                "CFBundleSupportedPlatforms": [platform],
                "CFBundleVersion": "1",
                "MinimumOSVersion": minimum_os,
            }
            with (framework / "Info.plist").open("wb") as plist_file:
                plistlib.dump(info, plist_file)
            converted.append(module_name)
    return {"converted": converted}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("app_dir", type=pathlib.Path)
    parser.add_argument("module_roots", nargs="+", type=pathlib.Path)
    parser.add_argument("--bundle-identifier", required=True)
    parser.add_argument("--platform", choices=("iPhoneOS", "iPhoneSimulator"), required=True)
    parser.add_argument("--minimum-os", required=True)
    arguments = parser.parse_args()
    try:
        result = frameworkize(
            arguments.app_dir,
            arguments.module_roots,
            bundle_identifier=arguments.bundle_identifier,
            platform=arguments.platform,
            minimum_os=arguments.minimum_os,
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
