# NOT REFACTORED.

import typing
import sys
import platform


class Platform:
    @staticmethod
    def get_runtime() -> typing.Dict:
        runtime_name = "Python"
        runtime_version = sys.version_info
        runtime_version = f"{runtime_version[0]}.{runtime_version[1]}.{runtime_version[2]}-{runtime_version[3]}-{runtime_version[4]}"
        runtime_build = platform.python_build()
        runtime_build = f"{runtime_build[0]}.{runtime_build[1]}"
        return {
            "name": runtime_name,
            "version": runtime_version,
            "build": runtime_build,
            "compiler": platform.python_compiler(),
            "branch": platform.python_branch(),
            "implementation": platform.python_implementation(),
            "revision": platform.python_revision(),
        }

    @staticmethod
    def get_platform() -> typing.Dict:
        return {
            "os": platform.system(),
            "release": platform.release(),
            "node": platform.node(),
            "version": platform.version(),
            "arch": platform.architecture()[0],
            "processor": platform.processor(),
            "machine": platform.machine(),
            "platform": platform.platform(terse=False),
        }

    @staticmethod
    def get_platform_dependant_tags() -> typing.Dict:
        system_os = platform.system()
        if platform.python_implementation() == "Jython" or system_os == "Java":
            # Java.
            java = {
                "os.java.ver": platform.java_ver() if platform.java_ver() else {},
            }
            return java
        if platform.system() == "Windows":
            # Windows.
            windows = {
                "os.win32.ver": platform.win32_ver(),
                "os.win32.edition": platform.win32_edition(),
                "os.win32.is_iot": platform.win32_is_iot(),
            }
            return windows
        if system_os == "MacOS":  # TODO.
            # MacOS.
            macos = {"os.mac.ver": platform.mac_ver()}
            return macos
        if False:  # TODO.
            unix = {"os.unix.libc_ver": platform.libc_ver()}
            return unix
        if False:  # TODO.
            linux = {
                "os.linux.freedesktop_os_release": platform.freedesktop_os_release()
            }
            return linux

        # Not found any platform dependant tags.
        return {}
