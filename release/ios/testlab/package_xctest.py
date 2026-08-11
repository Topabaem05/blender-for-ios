import argparse
import os
import pathlib
import plistlib
import re
import stat
import zipfile


GIT_LFS_POINTER_HEADER = b"version https://git-lfs.github.com/spec/v1"
DEVICE_XCTESTRUN_NAME = re.compile(r".+_iphoneos[0-9]+(?:\.[0-9]+)*-arm64\.xctestrun\Z")


def contains_file(directory):
    return directory.is_dir() and any(path.is_file() for path in directory.rglob("*"))


def validate_products(products_dir):
    debug_dir = products_dir / "Debug-iphoneos"
    if not debug_dir.is_dir():
        raise ValueError("missing Debug-iphoneos directory")

    xctestrun_files = sorted(products_dir.glob("*.xctestrun"))
    if len(xctestrun_files) != 1:
        raise ValueError("expected exactly one .xctestrun file")
    xctestrun = xctestrun_files[0]
    if not DEVICE_XCTESTRUN_NAME.fullmatch(xctestrun.name):
        raise ValueError(".xctestrun filename must identify an arm64 iphoneos SDK build")

    root_entries = {entry.name for entry in products_dir.iterdir()}
    expected_entries = {debug_dir.name, xctestrun.name}
    if root_entries != expected_entries:
        raise ValueError("Products root must contain only Debug-iphoneos and the device .xctestrun")

    app_dir = debug_dir / "Blender.app"
    info_plist = app_dir / "Info.plist"
    if not info_plist.is_file():
        raise ValueError("missing Blender.app/Info.plist")
    with info_plist.open("rb") as plist_file:
        app_info = plistlib.load(plist_file)
    if app_info.get("MinimumOSVersion") != "16.6":
        raise ValueError("Blender.app MinimumOSVersion must be 16.6")
    version = app_info.get("CFBundleShortVersionString")
    version_match = re.fullmatch(r"([0-9]+)\.([0-9]+)(?:\.[0-9]+)?", version or "")
    if version_match is None:
        raise ValueError("Blender.app CFBundleShortVersionString must identify Blender assets")
    device_family = app_info.get("UIDeviceFamily")
    if (
        not isinstance(device_family, list)
        or len(device_family) != 2
        or not all(type(value) is int for value in device_family)
        or set(device_family) != {1, 2}
    ):
        raise ValueError("Blender.app UIDeviceFamily must contain integer values 1 and 2")

    asset_version = ".".join(version_match.groups())
    required_asset_directories = (
        app_dir / "Assets" / asset_version / "scripts",
        app_dir / "Assets" / asset_version / "python",
        app_dir / "Assets" / "lib",
    )
    if not all(contains_file(directory) for directory in required_asset_directories):
        raise ValueError("Blender.app is missing scripts, Python, or runtime library assets")

    for product_file in app_dir.rglob("*"):
        if product_file.is_file():
            with product_file.open("rb") as handle:
                if handle.read(len(GIT_LFS_POINTER_HEADER)) == GIT_LFS_POINTER_HEADER:
                    relative_path = product_file.relative_to(app_dir)
                    raise ValueError(f"Blender.app contains Git LFS pointer: {relative_path}")

    test_bundle = debug_dir / "Blender.app" / "PlugIns" / "BlenderFTLTests.xctest"
    if not test_bundle.is_dir():
        raise ValueError("missing hosted BlenderFTLTests.xctest")
    if not (test_bundle / "Info.plist").is_file():
        raise ValueError("missing hosted BlenderFTLTests.xctest/Info.plist")
    if not (test_bundle / "BlenderFTLTests").is_file():
        raise ValueError("missing hosted BlenderFTLTests executable")

    with xctestrun.open("rb") as plist_file:
        xctestrun_data = plistlib.load(plist_file)
    targets = {
        name: configuration
        for name, configuration in xctestrun_data.items()
        if not name.startswith("__")
    }
    if "BlenderFTLTests" not in targets or not isinstance(targets["BlenderFTLTests"], dict):
        raise ValueError(".xctestrun must contain the hosted BlenderFTLTests target")
    if targets["BlenderFTLTests"].get("TestBundlePath") != (
        "__TESTHOST__/PlugIns/BlenderFTLTests.xctest"
    ):
        raise ValueError("BlenderFTLTests must be hosted inside Blender.app")
    return debug_dir, xctestrun, xctestrun_data


def write_product_path(archive, source_path, archive_path):
    if source_path.is_symlink():
        link_info = zipfile.ZipInfo(archive_path.as_posix())
        link_info.create_system = 3
        link_info.compress_type = zipfile.ZIP_DEFLATED
        link_info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(link_info, os.readlink(source_path))
    elif source_path.is_file():
        archive.write(source_path, archive_path)


def package(products_dir, output_zip):
    debug_dir, xctestrun, xctestrun_data = validate_products(products_dir)
    for name in list(xctestrun_data):
        if not name.startswith("__") and name != "BlenderFTLTests":
            del xctestrun_data[name]
    packaged_app = "__TESTROOT__/Debug-iphoneos/Blender.app"
    target = xctestrun_data["BlenderFTLTests"]
    target["TestHostPath"] = packaged_app
    target["DependentProductPaths"] = [
        packaged_app,
        packaged_app + "/PlugIns/BlenderFTLTests.xctest",
    ]
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for source_path in sorted(debug_dir.rglob("*")):
            write_product_path(archive, source_path, source_path.relative_to(products_dir))
        archive.writestr(xctestrun.relative_to(products_dir).as_posix(), plistlib.dumps(xctestrun_data))


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
