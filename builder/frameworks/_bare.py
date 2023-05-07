import os
import sys

from SCons.Script import DefaultEnvironment

IS_MAC = sys.platform.startswith("darwin")

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

mcu = str(board.get("build.mcu", "")).lower()
data_limit = 0 if mcu.startswith("ch32v0") else 8

machine_arch = board.get("build.march")
# "fix" Mac toolchain being incapable of linking against libgcc
# by downgrading instructions to EC (without extensions for some instructions)
print("Is mac: " + str(IS_MAC) + " and arch is " + str(machine_arch))
if IS_MAC and machine_arch == "rv32ecxw":
    machine_arch = "rv32ec"

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
        "-march=%s" % board.get("build.march"),
        "-mabi=%s" % board.get("build.mabi"),
    ],

    LIBS=[
        "m" # math library linked by default
    ],

    LINKFLAGS=[
        "-Os",
        "-march=%s" % board.get("build.march"),
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