# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
from platformio.public import PlatformBase
from platformio import util

IS_WINDOWS = sys.platform.startswith("win")

class Ch32vPlatform(PlatformBase):
    # ToDo: There's not toolchain for Linux ARM yet.
    riscv_toolchain = {
        # Windows
        "windows_amd64": "https://github.com/Community-PIO-CH32V/toolchain-riscv-windows.git",
        "windows_x86": "https://github.com/Community-PIO-CH32V/toolchain-riscv-windows.git",
        # No Windows ARM64 or ARM32 builds.
        # Linux
        "linux_x86_64": "https://github.com/Community-PIO-CH32V/toolchain-riscv-linux.git",
        #"linux_i686": "",
        #"linux_aarch64": "",
        #"linux_armv7l": "",
        #"linux_armv6l": "",
        # Mac (Intel and ARM are separate)
        "darwin_x86_64": "https://github.com/Community-PIO-CH32V/toolchain-riscv-mac.git",
        "darwin_arm64": "https://github.com/Community-PIO-CH32V/toolchain-riscv-mac.git"
    }
    minichlink_tool = {
        # Windows
        "windows_amd64": "https://github.com/Community-PIO-CH32V/tool-minichlink.git#windows",
        "windows_x86": "https://github.com/Community-PIO-CH32V/tool-minichlink.git#windows",
        # No Windows ARM64 or ARM32 builds.
        # Linux
        "linux_x86_64": "https://github.com/Community-PIO-CH32V/tool-minichlink.git#linux",
        #"linux_i686": "",
        #"linux_aarch64": "",
        #"linux_armv7l": "",
        #"linux_armv6l": "",
        # Mac (Intel and ARM are separate)
        "darwin_x86_64": "https://github.com/Community-PIO-CH32V/tool-minichlink.git#mac",
        "darwin_arm64": "https://github.com/Community-PIO-CH32V/tool-minichlink.git#mac_arm64"
    }
    wlink_tool = {
        # Windows
        "windows_amd64": "https://github.com/Community-PIO-CH32V/tool-wlink.git#windows",
        "windows_x86": "https://github.com/Community-PIO-CH32V/tool-wlink.git#windows",
        # No Windows ARM64 or ARM32 builds.
        # Linux
        "linux_x86_64": "https://github.com/Community-PIO-CH32V/tool-wlink.git#linux",
        #"linux_i686": "",
        #"linux_aarch64": "",
        #"linux_armv7l": "",
        #"linux_armv6l": "",
        # Mac (Intel and ARM are separate)
        "darwin_x86_64": "https://github.com/Community-PIO-CH32V/tool-wlink.git#mac_x64",
        "darwin_arm64": "https://github.com/Community-PIO-CH32V/tool-wlink.git#mac_arm64"
    }

    def get_boards(self, id_=None):
        result = super().get_boards(id_)
        if not result:
            return result
        if id_:
            return self._add_default_debug_tools(result)
        else:
            for key in result:
                result[key] = self._add_default_debug_tools(result[key])
        return result

    def configure_default_packages(self, variables, targets):
        sys_type = util.get_systype()
        # until toolchain is not yet approved in PIO registry: redirect packages at will here
        # (temporary)
        frameworks = variables.get("pioframework", [])
        gcc_branch = "#gcc12"
        # TODO make this user selectible
        # some users may have build errors with GCC12.
        FORCE_DOWNGRADE_TO_GCC8 = False
        # Temporary fix for "No GCC12 toolchain for MacOS x86_64". Email pending.
        if FORCE_DOWNGRADE_TO_GCC8 or sys_type == "darwin_x86_64":
            gcc_branch = ""
        self.packages["toolchain-riscv"]["version"] = Ch32vPlatform.riscv_toolchain[sys_type] + gcc_branch
        if not variables.get("board"):
            return super().configure_default_packages(variables, targets)
        # The FreeRTOS, Harmony LiteOS and RT-Thread package needs the 
        # NoneSDK as a base package
        if any([framework in frameworks for framework in ("freertos", "harmony-liteos", "rt-thread", "tencent-os")]):
            self.packages["framework-wch-noneos-sdk"]["optional"] = False
        # upload via USB bootloader wanted? (called "isp" in our platform)
        # then activate package
        board = variables.get("board")
        board_config = self.board_config(board)
        default_protocol = board_config.get("upload.protocol") or ""
        if variables.get("upload_protocol", default_protocol) == "isp":
            self.packages["tool-wchisp"]["optional"] = False
        if variables.get("upload_protocol", default_protocol) == "minichlink" or  "ch32v003fun" in frameworks or len(frameworks) == 0:
            self.packages["tool-minichlink"]["optional"] = False
            self.packages["tool-minichlink"]["version"] = Ch32vPlatform.minichlink_tool[sys_type]
        #elif variables.get("upload_protocol", default_protocol) == "wlink":
        # Always update the link to the tool-wlink tool, because for all uploads we want to have the "Enable SDI Print" available
        self.packages["tool-wlink"]["optional"] = False        
        self.packages["tool-wlink"]["version"] = Ch32vPlatform.wlink_tool[sys_type]
        build_core = variables.get("board_build.core", board_config.get("build.core", "arduino"))
        if "arduino" in frameworks:
            if build_core == "ch32v003":
                self.frameworks["arduino"]["package"] = "framework-arduinoch32v003"
            elif build_core == "ch32v":
                self.frameworks["arduino"]["package"] = "framework-arduinoch32v"
            elif build_core == "openwch":
               self.frameworks["arduino"]["package"] = "framework-arduino-openwch-ch32"
        if "zephyr" in frameworks:
            for p in self.packages:
                if p in ("tool-cmake", "tool-dtc", "tool-ninja"):
                    self.packages[p]["optional"] = False
            if not IS_WINDOWS:
                self.packages["tool-gperf"]["optional"] = False
        return super().configure_default_packages(variables, targets)

    def _add_default_debug_tools(self, board):
        debug = board.manifest.get("debug", {})
        if "tools" not in debug:
            debug["tools"] = {}

        tools = (
            "wch-link",
            "minichlink",
        )
        openocd_reset_cmds = [
            "define pio_reset_halt_target",
            "   load",
            "   monitor reset halt",
            "end",
            "define pio_reset_run_target",
            "   load",
            "   monitor reset",
            "end",
        ]
        minichlink_reset_cmds = [
            "define pio_reset_halt_target",
            "end",
            "define pio_reset_run_target",
            "end",
        ]
        init_cmds = [
            "set mem inaccessible-by-default off",
            "set arch riscv:rv32",
            # compatible with only WCH's gdb version, decodes code generated with "xw" correctly
            "set disassembler-options xw",
            "set remotetimeout unlimited",
            "target extended-remote $DEBUG_PORT",
            "$INIT_BREAK",
            "$LOAD_CMDS",
        ]
        for tool in tools:
            if tool in debug["tools"]:
                continue
            if tool == "wch-link":
                server_args = [
                    "-s",
                    os.path.join(
                        self.get_package_dir("tool-openocd-riscv-wch") or "",
                        "bin"
                    ),
                    "-s",
                    os.path.join(
                        self.get_package_dir("tool-openocd-riscv-wch") or "",
                        "scripts"
                    )
                ]
                if debug.get("openocd_config", ""):
                    server_args.extend(["-f", debug.get("openocd_config")])
                else:
                    assert debug.get("openocd_target"), (
                        "Missing target configuration for %s" % board.id
                    )
                    # All tools are FTDI based
                    server_args.extend(
                        [
                            "-f",
                            "interface/ftdi/%s.cfg" % tool,
                            "-f",
                            "target/%s.cfg" % debug.get("openocd_target"),
                        ]
                    )
                # Ugly countermeasure. Usually this is "gdb_port pipe" but GCC12 has a bug
                # that prevents it from starting OpenOCD in pipe mode. Hence, we have to revert
                # to reserving a port number for the GDB communication. But we can still disable
                # all other ports.
                # GCC8 would not need this.
                server_args.extend([
                    "-c", "gdb_port 3333; tcl_port disabled; telnet_port disabled"
                ])
                debug["tools"][tool] = {
                    "init_cmds": openocd_reset_cmds + init_cmds,
                    "server": {
                        "package": "tool-openocd-riscv-wch",
                        "executable": "bin/openocd",
                        "arguments": server_args,
                    },
                    # reference opened port
                    "port": "localhost:3333"
                }
            elif tool == "minichlink":
                debug["tools"][tool] = {
                    "server": {
                        "package": "tool-minichlink",
                        "executable": "minichlink",
                        "arguments": [
                            "-b", # Reboot out of Halt
                            "-a", # Reboot into Halt
                            "-G"  # "Terminal + GDB"
                        ]
                    },
                    # The minichlink GDB server does not support the "load" command
                    # So, we have to tell PIO to preflash the binary using the regular upload command
                    "load_cmds": "preload",
                    "init_cmds": minichlink_reset_cmds + init_cmds,
                    "port": "localhost:2000", # default port of that tool
                    "read_pattern": "GDBServer Running",
                }
            debug["tools"][tool]["onboard"] = tool in debug.get("onboard_tools", [])
            debug["tools"][tool]["default"] = tool in debug.get("default_tools", [])
        board.manifest["debug"] = debug
        return board

    def configure_debug_session(self, debug_config):
        if debug_config.speed:
            if "openocd" in (debug_config.server or {}).get("executable", ""):
                debug_config.server["arguments"].extend(
                    ["-c", "adapter speed %s" % debug_config.speed]
                )
