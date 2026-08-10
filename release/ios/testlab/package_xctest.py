import argparse
import pathlib
import plistlib
import zipfile


def validate_products(products_dir):
    debug_dir = products_dir / "Debug-iphoneos"
    if not debug_dir.is_dir():
        raise ValueError("missing Debug-iphoneos directory")

    xctestrun_files = sorted(products_dir.glob("*.xctestrun"))
    if len(xctestrun_files) != 1:
        raise ValueError("expected exactly one .xctestrun file")
    xctestrun = xctestrun_files[0]
    if not xctestrun.name.endswith("_iphoneos16.6-arm64.xctestrun"):
        raise ValueError(".xctestrun filename must end with _iphoneos16.6-arm64.xctestrun")

    root_entries = {entry.name for entry in products_dir.iterdir()}
    expected_entries = {debug_dir.name, xctestrun.name}
    if root_entries != expected_entries:
        raise ValueError("Products root must contain only Debug-iphoneos and the device .xctestrun")

    info_plist = debug_dir / "Blender.app" / "Info.plist"
    if not info_plist.is_file():
        raise ValueError("missing Blender.app/Info.plist")
    with info_plist.open("rb") as plist_file:
        app_info = plistlib.load(plist_file)
    if app_info.get("MinimumOSVersion") != "16.6":
        raise ValueError("Blender.app MinimumOSVersion must be 16.6")
    device_family = app_info.get("UIDeviceFamily")
    if (
        not isinstance(device_family, list)
        or len(device_family) != 2
        or not all(type(value) is int for value in device_family)
        or set(device_family) != {1, 2}
    ):
        raise ValueError("Blender.app UIDeviceFamily must contain integer values 1 and 2")

    test_bundle = debug_dir / "Blender.app" / "PlugIns" / "BlenderFTLTests.xctest"
    if not test_bundle.is_dir():
        raise ValueError("missing hosted BlenderFTLTests.xctest")
    if not (test_bundle / "Info.plist").is_file():
        raise ValueError("missing hosted BlenderFTLTests.xctest/Info.plist")
    if not (test_bundle / "BlenderFTLTests").is_file():
        raise ValueError("missing hosted BlenderFTLTests executable")
    return debug_dir, xctestrun


def package(products_dir, output_zip):
    debug_dir, xctestrun = validate_products(products_dir)
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for source_path in sorted(debug_dir.rglob("*")):
            if source_path.is_file():
                archive.write(source_path, source_path.relative_to(products_dir))
        archive.write(xctestrun, xctestrun.relative_to(products_dir))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("products_dir", type=pathlib.Path)
    parser.add_argument("output_zip", type=pathlib.Path)
    arguments = parser.parse_args()

    try:
        package(arguments.products_dir, arguments.output_zip)
    except (OSError, ValueError, plistlib.InvalidFileException) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
