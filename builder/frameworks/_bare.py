import os
import sys

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

mcu = str(board.get("build.mcu", "")).lower()
data_limit = 0 if mcu.startswith("ch32v0") else 8

machine_arch = str(board.get("build.march"))
# Mac is a special boy who needs special treatment...
IS_MAC =  sys.platform.startswith("darwin")
is_gcc_12 = platform.get_package_version("toolchain-riscv").split(".")[1].startswith("12")
if IS_MAC and is_gcc_12:
    machine_arch += "+zicsr"

env.Append(
    ASFLAGS=[
        "-march=%s" % machine_arch,
        "-mabi=%s" % board.get("build.mabi"),
    ],
    ASPPFLAGS=[
        "-x", "assembler-with-cpp",
    ],

    CFLAGS=[
        "-std=gnu99"
    ],

    CXXFLAGS=[
        # compiler goes up to gnu++2a but is EXPERIMENTAL
        "-std=gnu++17",
        # standard embedded flags to reduce firmware size
        "-fno-threadsafe-statics",
        "-fno-rtti",
        "-fno-exceptions",
        "-fno-use-cxa-atexit"
    ],

    CCFLAGS=[
        "-Os",
        "-g",
        "-Wall",
        "-msmall-data-limit=%d" % data_limit,
        "-mno-save-restore" if mcu.startswith("ch5") else "-msave-restore",
        "-fmessage-length=0",
        "-fsigned-char",
        "-ffunction-sections",
        "-fdata-sections",
        "-fno-common",
        "-Wunused",
        "-Wuninitialized",
        "-Wno-comment",
        "-march=%s" % machine_arch,
        "-mabi=%s" % board.get("build.mabi"),
    ],

    LIBS=[
        "m" # math library linked by default
    ],

    LINKFLAGS=[
        "-Os",
        "-march=%s" % machine_arch,
        "-mabi=%s" % board.get("build.mabi"),
        "-ffunction-sections",
        "-fdata-sections",
        "-Wl,-gc-sections",
        "--specs=nano.specs",
        "--specs=nosys.specs",
        "-nostartfiles",
        '-Wl,-Map="%s"' % os.path.join(
            "$BUILD_DIR", os.path.basename(env.subst("${PROJECT_DIR}.map"))),
    ]
)
# copy general C/C++ flags to assembler with cpp flags too, except
# would-be-duplicate last two elements
env["ASPPFLAGS"].extend(env["CCFLAGS"][:-2]) 