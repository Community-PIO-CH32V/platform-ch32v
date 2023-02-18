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

if upload_protocol in debug_tools:
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
            "-c", "load_image {$SOURCE} %s elf" % board_config.get(
                "upload").get("image_offset", "0x0"),
            "-c" "reset",
            #"-c", "resume %s" % board_config.get("upload").get("image_offset", "0x0"),
            "-c", "shutdown"
        ]
    )
    env.Replace(
        UPLOADER="openocd",
        UPLOADERFLAGS=openocd_args,
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS",
    )
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

# custom upload tool
elif upload_protocol == "custom":
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

else:
    sys.stderr.write("Warning! Unknown upload protocol %s\n" % upload_protocol)

env.AddPlatformTarget("upload", upload_target, upload_actions, "Upload")


#
# Setup default targets
#

Default([target_buildprog, target_size])
