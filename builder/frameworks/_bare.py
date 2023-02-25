import os

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

data_limit = 0 if str(board.get("build.mcu", "")).lower().startswith("ch32v0") else 8

env.Append(
    ASFLAGS=[
        "-march=%s" % board.get("build.march"),
        "-mabi=%s" % board.get("build.mabi"),
    ],
    ASPPFLAGS=[
        "-x", "assembler-with-cpp",
    ],

    CFLAGS=[
        "-std=gnu99"
    ],

    CCFLAGS=[
        "-Os",
        "-g",
        "-Wall",
        "-msmall-data-limit=%d" % data_limit,
        "-msave-restore",
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