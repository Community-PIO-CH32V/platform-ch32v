import os
from SCons.Script import DefaultEnvironment
from common_clk_config import validate_and_define_sysclk

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

mcu = str(board.get("build.mcu", "")).lower()
data_limit = 0 if mcu.startswith("ch32v0") else 8

machine_arch = str(board.get("build.march"))

# the MAC x64 toolchain only has GCC8, not GCC12. Thus, we need to strip some
# unsupported extensions. "xw" end "rv32ec" "rv32imc" are supported, the reset not.
remap_arch = {
    "rv32ec_zmmul_xw": "rv32ecxw",
    "rv32imc_zba_zbb_zbc_zbs_xw": "rv32imcxw"
}
is_gcc_12 = platform.get_package_version("toolchain-riscv").split(".")[1].startswith("12")
if not is_gcc_12 and machine_arch in remap_arch:
    machine_arch = remap_arch[machine_arch]

if mcu.startswith("ch5") or mcu.startswith("ch32h41"):
    # building h417 ch32fun firmwares need this, somehow?
    # regular none-sdk firwmares do not. weird.
    safe_restore_flag = "-mno-save-restore"
else:
    safe_restore_flag = "-msave-restore"

def get_flag_value(flag_name:str, default_val:bool):
    flag_val = board.get("build.%s" % flag_name, default_val)
    flag_val = str(flag_val).lower() in ("1", "yes", "true")
    return flag_val

lto_flag = ""
if get_flag_value("use_lto", False):
    lto_flag = "-flto"

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
        safe_restore_flag,
        "-fmessage-length=0",
        "-fsigned-char",
        "-ffunction-sections",
        "-fdata-sections",
        "-fno-common",
        "-Wunused",
        "-Wuninitialized",
        "-Wno-comment",
        lto_flag,
        "-march=%s" % machine_arch,
        "-mabi=%s" % board.get("build.mabi"),
    ],

    LIBS=[
        "m" # math library linked by default
    ],

    LINKFLAGS=[
        "-Os",
        "-g",
        "-march=%s" % machine_arch,
        "-mabi=%s" % board.get("build.mabi"),
        "-ffunction-sections",
        "-fdata-sections",
        "-Wl,-gc-sections",
        "--specs=nano.specs",
        "--specs=nosys.specs",
        "-nostartfiles",
        lto_flag,
    ]
)

# Automatically create map file, unless user already creates a map file at a different place
# using their own build_flags.
if not any("-Wl,-Map" in f for f in env.get("LINKFLAGS", [])):
    env.Append(LINKFLAGS=[
        "-Wl,-Map=%s" % os.path.relpath(
            env.subst(os.path.join("$BUILD_DIR", "${PROGNAME}.map")),
            env.subst("$PROJECT_DIR")
        )
    ])

# copy general C/C++ flags to assembler with cpp flags too, except
# would-be-duplicate last two elements
env["ASPPFLAGS"].extend(env["CCFLAGS"][:-2]) 

# add sysclock defines
validate_and_define_sysclk(env)
