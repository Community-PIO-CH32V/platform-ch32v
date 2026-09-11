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
chip_name = str(board_config.get("build.mcu", "")).lower()

# Depending on whether we're using GCC8 or GCC12, the compiler executable's names need to be adapted.
# Attempt proper detection by looking at the package version.
is_gcc_12 = platform.get_package_version("toolchain-riscv").split(".")[1].startswith("12")
compiler_triple = "riscv-wch-elf" if is_gcc_12 else "riscv-none-embed"
env.Replace(
    AR="%s-gcc-ar" % compiler_triple,
    AS="%s-as" % compiler_triple,
    CC="%s-gcc" % compiler_triple,
    GDB="%s-gdb" % compiler_triple,
    CXX="%s-g++" % compiler_triple,
    OBJDUMP="%s-objdump" % compiler_triple,
    OBJCOPY="%s-objcopy" % compiler_triple,
    RANLIB="%s-ranlib" % compiler_triple,
    SIZETOOL="%s-size" % compiler_triple,
    ARFLAGS=["rc"],
    SIZEPROGREGEXP=r"^(?:\.text|\.data|\.rodata|\.text.align|\.init|\.loadcodelalign|\.highcode|\.loadcode|\.vector)\s+(\d+).*",
    SIZEDATAREGEXP=r"^(?:\.data|\.bss|\.noinit|\.loadcode|\.highcode|\.stack)\s+(\d+).*",
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

frameworks = env.get("PIOFRAMEWORK", [])
if "zephyr" in frameworks:
    env.SConscript(
        os.path.join(platform.get_package_dir(
            "framework-zephyr"), "scripts", "platformio", "platformio-build-pre.py"),
        exports={"env": env}
    )
    # correct display of RAM and Flash statistics
    env.Replace(
        SIZEPROGREGEXP=r"^(?:text|rom_start|reset|exceptions|initlevel|device_area|sw_isr_table|_static_thread_data_area|datas|rodata|device_states|\.last_section|k_\S+)\s+(\d+).*",
        SIZEDATAREGEXP=r"^(?:datas|bss|noinit|stack|device_states|k_\S+)\s+(\d+).*",
    )

target_elf = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_elf = os.path.join("$BUILD_DIR", "${PROGNAME}.elf")
    target_bin = os.path.join("$BUILD_DIR", "${PROGNAME}.bin")
else:
    target_elf = env.BuildProgram()
    # Build disassembly listing (additionally intermixed with code)
    for opt, name in [("", ""), ("-S", ".debug")]:
        env.AddPostAction(
            "$BUILD_DIR/${PROGNAME}.elf",
            env.VerboseAction(" ".join([
                    "$OBJDUMP",
                    opt,
                    "-M", # disassemble compressed instructions correctly
                    "xw",
                    "-d",
                    '"%s"' % "$BUILD_DIR/${PROGNAME}.elf",
                    ">",
                    '"%s"' % ("$BUILD_DIR/${PROGNAME}" + name + ".lst")
            ]), "Building $BUILD_DIR/${PROGNAME}" + name + ".lst")
        )
    target_bin = env.ElfToBin(os.path.join("$BUILD_DIR", "${PROGNAME}"), target_elf)
    if "zephyr" in frameworks and "mcuboot-image" in COMMAND_LINE_TARGETS:
        target_bin = env.MCUbootImage(
            os.path.join("$BUILD_DIR", "${PROGNAME}.mcuboot.bin"), target_bin)
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
    # target address can be a hex value of a symbolic name like "flash", "bootloader", "eeprom", "ram", "options"
    flash_start = board_config.get("upload.offset_address", "flash")
    env.Replace(
        UPLOADER="minichlink",
        UPLOADERFLAGS="", # write binary
        UPLOADERPOSTFLAGS="%s -b" % str(flash_start), # address, (re)boot from halt
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS -w $SOURCE $UPLOADERPOSTFLAGS",
    )
    upload_target = target_bin
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]
elif upload_protocol == "wlink":
    env.Replace(
        UPLOADER="wlink",
        UPLOADERFLAGS="",
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS flash $SOURCE",
    )
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]
# Over the air, via the sketch's own ArduinoOTA. Cores that support it ship
# tools/espota.py and build a *_ota.bin next to the firmware; on the CH32H41x
# the two differ, because the full binary carries a boot stub that an OTA image
# must not.
#
#     upload_protocol = espota
#     upload_port = 192.168.1.50      ; or ch32h4-a1b2c3.local
#     upload_flags = --auth=secret    ; if the sketch sets a password
#
# THE SKETCH ON THE BOARD IS PART OF THE UPLOAD PATH: it has to be running and
# calling ArduinoOTA.handle(). One that hangs or faults takes the network port
# with it, and the next upload goes over the probe.
elif upload_protocol == "espota":
    framework_dir = ""
    for pkg in ("framework-arduinoch32h4", "framework-arduinoch32v"):
        try:
            framework_dir = platform.get_package_dir(pkg) or ""
        except Exception:
            framework_dir = ""
        if framework_dir and os.path.isfile(
                os.path.join(framework_dir, "tools", "espota.py")):
            break
        framework_dir = ""
    if not framework_dir:
        sys.stderr.write(
            "Error: upload_protocol = espota needs a core that ships "
            "tools/espota.py, and this one does not.\n")
        env.Exit(1)

    if not env.subst("$UPLOAD_PORT"):
        sys.stderr.write(
            "Error: upload_protocol = espota needs upload_port set to the "
            "board's address or its <name>.local name.\n")
        env.Exit(1)

    # The OTA image, not the full binary -- but the .bin stays the SCons
    # target, because the OTA image is written as a side effect of building it
    # and SCons has no rule that would produce it on its own.
    #
    # Resolved when the upload runs rather than now, so that a core which needs
    # no split (its whole image is the sketch) falls back to the full binary.
    def _ota_upload(source, target, env):
        ota = env.subst(os.path.join("$BUILD_DIR", "${PROGNAME}_ota.bin"))
        if not os.path.isfile(ota):
            ota = env.subst(os.path.join("$BUILD_DIR", "${PROGNAME}.bin"))
        return env.Execute(env.VerboseAction(
            '$UPLOADER $UPLOADERFLAGS -f "%s"' % ota, "Uploading %s" % ota))

    env.Replace(
        UPLOADER='"$PYTHONEXE" "%s"' % os.path.join(
            framework_dir, "tools", "espota.py"),
        UPLOADERFLAGS=["-i", "$UPLOAD_PORT"] + env.get("UPLOAD_FLAGS", []),
    )
    upload_target = target_bin
    upload_actions = [_ota_upload]
# custom upload tool
elif upload_protocol == "custom":
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

else:
    sys.stderr.write("Warning! Unknown upload protocol %s\n" % upload_protocol)

env.AddPlatformTarget("upload", upload_target, upload_actions, "Upload")

#
# Target: Disable / Enable / Check Code Read Protection, Erase
#
def generate_minichlink_action(args: List[str], action_name:str, upload_protocol_is_minichlink: bool):
    minichlink_path = os.path.join(
        platform.get_package_dir("tool-minichlink") or "",
        "minichlink"
    )
    cmd = ["\"%s\"" % minichlink_path]
    # we don't want uploader flags pertaining to other uploaders like wch-linke.
    if upload_protocol_is_minichlink:
        cmd.append("$UPLOADERFLAGS")
    cmd.extend(args)
    # print("Returning action: " + str(cmd))
    return env.VerboseAction(" ".join(cmd), action_name)

def generate_wlink_action(args: List[str], action_name:str):
    wchisp_path = os.path.join(
        platform.get_package_dir("tool-wlink") or "",
        "wlink"
    )
    cmd = ["\"%s\"" % wchisp_path]
    cmd.extend(args)
    return env.VerboseAction(" ".join(cmd), action_name)

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
    default_args: List[str] = debug_tools.get(upload_protocol).get("server").get("arguments", [])
    # small fixup with shell escaping. Quote args that have spaces in them.
    for (i, arg) in enumerate(default_args.copy()):
        if " " in arg and not arg.startswith('"'):
            default_args[i] = '"%s"' % arg
    cmd.extend(default_args)
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
if access_via_openocd and upload_protocol != "minichlink":
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
# make minichlink SDI printf monitor show up even when it's not the selected upload protocol
is_minichlink = upload_protocol == "minichlink"
if upload_protocol == "minichlink" or "ch32v003fun" in frameworks or len(frameworks) == 0:
    env.AddPlatformTarget(
        "sdi_printf_monitor", None, generate_minichlink_action([
            "-T"
        ], "Starting SDI Printf Monitor", is_minichlink),
        "Monitor SDI Printf (ch32fun)"
    )
if upload_protocol == "minichlink":
    env.AddPlatformTarget(
        "enable_flash_protection", None, generate_minichlink_action([
            "-P"
        ], "Enabling Flash Protection", is_minichlink),
        "Enable Flash Protection"
    )
    env.AddPlatformTarget(
        "disable_flash_protection", None, generate_minichlink_action([
            "-p"
        ], "Disabling Flash Protection", is_minichlink),
        "Disable Flash Protection"
    )

# Enable WLink options if tool installed or protocol selected.
if upload_protocol == "wlink" or platform.get_package_dir("tool-wlink") != "":
    env.AddPlatformTarget(
        "sdi_printf", None, generate_wlink_action([
            "sdi-print enable"
        ], "Enabling SDI Printf"),
        "Enable SDI Printf (NoneSDK)"
    )
    env.AddPlatformTarget(
        "disable_sdi_printf", None, generate_wlink_action([
            "sdi-print disable"
        ], "Disabling SDI Printf"),
        "Disable SDI Printf (NoneSDK)"
    )

#
# Setup default targets
#

#
# Targets: filesystem image (buildfs / uploadfs)
#
# Only for cores that reserve a filesystem partition and say where it is. The
# ch32h4 Arduino core publishes CH32H4_FS_START and CH32H4_FS_SIZE from its own
# build script, which derives them from the same constants the linker script
# uses -- so there is exactly one definition of where the partition lives, and
# an image can never be written over the sketch because two files disagreed.
#
# A size of zero means the sketch did not ask for a filesystem, and the targets
# say so rather than silently building a zero-length image.

fs_size = int(env.get("CH32H4_FS_SIZE", 0) or 0)
fs_start = int(env.get("CH32H4_FS_START", 0) or 0)

if fs_size > 0 and fs_start > 0:
    # mklittlefs comes from earlephilhower's package, the same one
    # platform-raspberrypi uses. Two reasons rather than the registry's
    # platformio/tool-mklittlefs: that one is the 2021 ESP8266 build, and this
    # one ships for every host PlatformIO runs on -- windows x86/amd64/arm64,
    # macOS intel and Apple silicon, and linux x86_64/i686/aarch64/armv6l and
    # armv7l. The "rp2040" in the name is where it was packaged, not what it
    # can write; a LittleFS image is defined by the geometry arguments below.
    #
    # Resolved to a path, NOT invoked as a bare name. Relying on PATH works
    # only on a machine that happens to have one installed, and silently picks
    # up whichever version that is -- and the version decides the on-disk
    # format.
    mkfs_dir = platform.get_package_dir("tool-mklittlefs-rp2040-earlephilhower") or ""
    mkfs_tool = os.path.join(mkfs_dir, "mklittlefs")

    env.Replace(
        MKFSTOOL=mkfs_tool,
        # Geometry has to match what the core configures LittleFS with, or the
        # image mounts as corrupt: 8 KB erase blocks and a 256-byte program
        # page, which is this part's flash page-program size.
        FSBLOCKSIZE=int(env.get("CH32H4_FS_BLOCK_SIZE", 8192)),
        FSPAGESIZE=int(env.get("CH32H4_FS_PAGE_SIZE", 256)),
    )

    def _mkfs_action(target, source, env):
        """Everything that should fail with a sentence, not a traceback."""
        if not mkfs_dir:
            sys.stderr.write(
                "Error: tool-mklittlefs-rp2040-earlephilhower is not "
                "installed, so no filesystem image can be built. It is "
                "fetched on demand for the buildfs and uploadfs targets; if "
                "you reached this another way, install it with 'pio pkg "
                "install -t earlephilhower/"
                "tool-mklittlefs-rp2040-earlephilhower'.\n")
            env.Exit(1)
        data_dir = env.subst("$PROJECT_DATA_DIR")
        if not os.path.isdir(data_dir):
            sys.stderr.write(
                "Error: no data directory at %s. Put the files you want in the"
                " filesystem there.\n" % data_dir)
            env.Exit(1)
        return None

    target_fs_image = os.path.join("$BUILD_DIR", "littlefs.bin")

    fs_image = env.Command(
        target_fs_image,
        "$PROJECT_DATA_DIR",
        [
            env.VerboseAction(_mkfs_action, None),
            env.VerboseAction(
                '"$MKFSTOOL" -c "$SOURCE" -b $FSBLOCKSIZE -p $FSPAGESIZE'
                ' -s %d "$TARGET"' % fs_size,
                "Building filesystem image $TARGET"),
        ],
    )
    AlwaysBuild(fs_image)

    env.AddPlatformTarget(
        "buildfs", fs_image, None, "Build Filesystem Image",
        "Build a LittleFS image from the data/ directory")

    # Flashed at the partition's own address, NOT at the start of flash. The
    # sketch is not touched.
    #
    # WLINK EXPLICITLY, not $UPLOADER. Two reasons, and the first one alone is
    # fatal: on this board $UPLOADER is openocd, which does not take "flash
    # --address" and fails with "unknown option -- address". And even with the
    # right syntax openocd cannot program the upper flash, which is precisely
    # where a filesystem partition lives -- 0x080CC000 for a 128 KB one. wlink
    # is the tool that can write it, which is why the hardware harness uses it
    # for everything.
    wlink = os.path.join(platform.get_package_dir("tool-wlink") or "", "wlink")

    env.AddPlatformTarget(
        "uploadfs", fs_image,
        [env.VerboseAction(
            '"%s" flash --address 0x%08X "$SOURCE"' % (wlink, fs_start),
            "Uploading filesystem image to 0x%08X" % fs_start)],
        "Upload Filesystem Image",
        "Write the LittleFS image into the flash partition")


Default([target_buildprog, target_size])
