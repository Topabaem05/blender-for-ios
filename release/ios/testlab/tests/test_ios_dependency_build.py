import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).parents[4]
OPTIONS_CMAKE = SOURCE_ROOT / "build_files" / "build_environment" / "cmake" / "options.cmake"


class IOSDependencyBuildTests(unittest.TestCase):
    def test_apple_cross_cmake_root_path_is_forwarded(self):
        source = OPTIONS_CMAKE.read_text(encoding="utf-8")

        self.assertNotIn("set(DCMAKE_FIND_ROOT_PATH", source)
        self.assertIn(
            "set(CMAKE_FIND_ROOT_PATH\n"
            "        ${CMAKE_FIND_ROOT_PATH}\n"
            "        ${LIBDIR})",
            source,
        )
        self.assertIn(
            "-DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE:STRING=${CMAKE_FIND_ROOT_PATH_MODE_PACKAGE}",
            source,
        )


if __name__ == "__main__":
    unittest.main()
