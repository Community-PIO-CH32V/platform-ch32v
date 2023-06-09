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

import sys
import os
from typing import List

from SCons.Script import (
    ARGUMENTS,
    COMMAND_LINE_TARGETS,
    AlwaysBuild,
    Builder,
    Default,
    DefaultEnvironment,
)

env = DefaultEnvironment()
platform = env.PioPlatform()
board_config = env.BoardConfig()

env.Replace(
    AR="riscv-none-embed-gcc-ar",
    AS="riscv-none-embed-as",
    CC="riscv-none-embed-gcc",
    GDB="riscv-none-embed-gdb",
    CXX="riscv-none-embed-g++",
    OBJCOPY="riscv-none-embed-objcopy",
    RANLIB="riscv-none-embed-ranlib",
    SIZETOOL="riscv-none-embed-size",
    ARFLAGS=["rc"],
    SIZEPROGREGEXP=r"^(?:\.text|\.data|\.rodata|\.text.align|\.init|\.vector)\s+(\d+).*",
    SIZEDATAREGEXP=r"^(?:\.data|\.bss|\.noinit|\.stack)\s+(\d+).*",
    SIZECHECKCMD="$SIZETOOL -A -d $SOURCES",
    SIZEPRINTCMD="$SIZETOOL --format=berkeley $SOURCES",
    PROGSUFFIX=".elf",
)

# Allow user to override via pre:script
if env.get("PROGNAME", "program") == "program":
    env.Replace(PROGNAME="firmware")

env.Append(
    BUILDERS=dict(
        ElfToHex=Builder(
            action=env.VerboseAction(
                " ".join(["$OBJCOPY", "-O", "ihex", "$SOURCES", "$TARGET"]),
                "Building $TARGET",
            ),
            suffix=".hex",
        ),
        ElfToBin=Builder(
            action=env.VerboseAction(
                " ".join(["$OBJCOPY", "-O", "binary", "$SOURCES", "$TARGET"]),
                "Building $TARGET",
            ),
            suffix=".bin",
        )
    )
)

if not env.get("PIOFRAMEWORK"):
    env.SConscript("frameworks/_bare.py", exports="env")

#
# Target: Build executable and linkable firmware
#

target_elf = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_elf = os.path.join("$BUILD_DIR", "${PROGNAME}.elf")
    target_bin = os.path.join("$BUILD_DIR", "${PROGNAME}.bin")
else:
    target_elf = env.BuildProgram()
    target_bin = env.ElfToBin(os.path.join("$BUILD_DIR", "${PROGNAME}"), target_elf)
    env.Depends(target_bin, "checkprogsize")

AlwaysBuild(env.Alias("nobuild", target_bin))
target_buildprog = env.Alias("buildprog", target_bin, target_bin)


#
# Target: Print binary size
#

target_size = env.AddPlatformTarget(
    "size",
    target_elf,
    env.VerboseAction("$SIZEPRINTCMD", "Calculating size $SOURCE"),
    "Program Size",
    "Calculate program size",
)

#
# Target: Upload by default .bin file
#

upload_protocol = env.subst("$UPLOAD_PROTOCOL")
debug_tools = board_config.get("debug.tools", {})
upload_actions = []
upload_target = target_elf

if upload_protocol in debug_tools and upload_protocol != "minichlink":
    openocd_args = [
        "-c",
        "debug_level %d" % (2 if int(ARGUMENTS.get("PIOVERBOSE", 0)) else 1),
    ]
    openocd_args.extend(
        debug_tools.get(upload_protocol).get("server").get("arguments", [])
    )
    openocd_args.extend(
        [
            "-c", "init",
            "-c", "halt",
            "-c", "program {$SOURCE} verify reset",
            "-c", "shutdown"
        ]
    )
    env.Replace(
        UPLOADER="openocd",
        UPLOADERFLAGS=openocd_args,
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS",
    )
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

# WCHISP
elif upload_protocol == "isp":
    env.Replace(
        UPLOADER="wchisp",
        UPLOADERFLAGS="",
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS flash $SOURCE",
    )
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]
elif upload_protocol == "minichlink":
    flash_start = board_config.get("upload.offset_address", "0x08000000")
    env.Replace(
        UPLOADER="minichlink",
        UPLOADERFLAGS="-w", # write binary
        UPLOADERPOSTFLAGS="%s -b" % str(flash_start), # address, (re)boot from halt
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS $SOURCE $UPLOADERPOSTFLAGS",
    )
    upload_target = target_bin
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]
# custom upload tool
elif upload_protocol == "custom":
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

else:
    sys.stderr.write("Warning! Unknown upload protocol %s\n" % upload_protocol)

env.AddPlatformTarget("upload", upload_target, upload_actions, "Upload")

#
# Target: Disable / Enable / Check Code Read Protection, Erase
#
def generate_wchisp_action(args: List[str], action_name:str):
    wchisp_path = os.path.join(
        platform.get_package_dir("tool-wchisp") or "",
        "wchisp"
    )
    cmd = ["\"%s\"" % wchisp_path]
    cmd.extend(args)
    return env.VerboseAction(" ".join(cmd), action_name)

def generate_openocd_action(args: List[str], action_name:str):
    # OpenOCD commands only supported through debugging adapters,
    # naturally.
    # Stuff like erasing / disabling code protection can still be done via
    # USB DFU / Serial bootloader tools, but we haven't integrated these yet.
    if not upload_protocol in debug_tools:
        print("Currently these actions require a debugging probe (e.g., WCH-Link(E)).")
        return None
    openocd_path = os.path.join(
        platform.get_package_dir("tool-openocd-riscv-wch") or "",
        "bin",
        "openocd"
    )

    cmd = [
        "\"%s\"" % openocd_path
    ]
    cmd.extend(debug_tools.get(upload_protocol).get("server").get("arguments", []))
    cmd.extend([
        "-c",
        "\"debug_level %d\"" % (3 if int(ARGUMENTS.get("PIOVERBOSE", 0)) else 2),
        "-c", "\"gdb_port disabled\"",
        "-c", "\"tcl_port disabled\"",
        "-c", "\"telnet_port disabled\"",
        "-c", "init",
        "-c", "halt"
    ])
    cmd.extend(args)
    cmd.extend([
        "-c", "shutdown"
    ])
    return env.VerboseAction(" ".join(cmd), action_name)

access_via_openocd = upload_protocol in debug_tools
if access_via_openocd:
    env.AddPlatformTarget(
        "disable_flash_protection", None, generate_openocd_action([
            "-c", "\"flash probe 0\"",
            "-c", "\"flash protect 0 0 last off\"",
        ], "Disabling Flash Protection"),
        "Disable Flash Protection"
    )

    env.AddPlatformTarget(
        "enable_flash_protection", None, generate_openocd_action([
            "-c", "\"flash probe 0\"",
            "-c", "\"flash protect 0 0 last on\"",
        ], "Enabling Flash Protection"),
        "Enable Flash Protection"
    )

    env.AddPlatformTarget(
        "check_flash_protection", None, generate_openocd_action([
            "-c", "\"flash probe 0\"",
            "-c", "\"flash protect_check 0\"",
        ], "Checking Flash Protection"),
        "Check Flash Protection"
    )

    env.AddPlatformTarget(
        "erase", None, generate_openocd_action([
            "-c", "\"flash probe 0\"",
            "-c", "\"flash erase_sector 0 0 last\"",
        ], "Erasing Flash"),
        "Erase Flash"
    )
elif upload_protocol == "isp":
    env.AddPlatformTarget(
        "info", None, generate_wchisp_action([
            "info"
        ], "Getting Device Info"),
        "Device Info (ISP)"
    )
    env.AddPlatformTarget(
        "disable_flash_protection", None, generate_wchisp_action([
            "config unprotect"
        ], "Disabling Flash Protection"),
        "Disable Flash Protection (ISP)"
    )
    env.AddPlatformTarget(
        "reset_cfg", None, generate_wchisp_action([
            "config reset"
        ], "Resetting Configuration Registers"),
        "Reset Configuration Registers (ISP)"
    )
    env.AddPlatformTarget(
        "erase", None, generate_wchisp_action([
            "erase"
        ], "Erasing Device"),
        "Erase (ISP)"
    )
    env.AddPlatformTarget(
        "reset", None, generate_wchisp_action([
            "reset"
        ], "Restting Device"),
        "Reset (ISP)"
    )

#
# Setup default targets
#

Default([target_buildprog, target_size])
