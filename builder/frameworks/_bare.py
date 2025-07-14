import os
from SCons.Script import DefaultEnvironment
from SCons.Errors import UserError
import sys
import re

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

mcu = str(board.get("build.mcu", "")).lower()
data_limit = 0 if mcu.startswith("ch32v0") else 8

machine_arch = str(board.get("build.march"))

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
        "-mno-save-restore" if mcu.startswith("ch5") else "-msave-restore",
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
        '-Wl,-Map="%s"' % os.path.join(
            "$BUILD_DIR", os.path.basename(env.subst("${PROJECT_DIR}.map")))
    ])

# copy general C/C++ flags to assembler with cpp flags too, except
# would-be-duplicate last two elements
env["ASPPFLAGS"].extend(env["CCFLAGS"][:-2]) 

# setup clocks
def validate_and_define_sysclk(env):
    VALID_PLL_FREQS = {
        "ch32v00x": {
            "hsi+pll": [8_000_000, 24_000_000, 48_000_000],
            "hse+pll": [8_000_000, 24_000_000, 48_000_000],
        },
        "ch32v00Xx": {
            "hsi+pll": [8_000_000, 24_000_000, 48_000_000],
            "hse+pll": [8_000_000, 24_000_000, 48_000_000],
        },
        "ch32v10x": {
            "hsi+pll": [48_000_000, 56_000_000, 72_000_000],
            "hse+pll": [48_000_000, 56_000_000, 72_000_000],
        },
        "ch32v20x": {
            "hsi+pll": [48_000_000, 56_000_000, 72_000_000, 96_000_000, 120_000_000, 144_000_000],
            "hse+pll": [48_000_000, 56_000_000, 72_000_000, 96_000_000, 120_000_000, 144_000_000],
        },
        "ch32v30x": {
            "hsi+pll": [48_000_000, 56_000_000, 72_000_000, 96_000_000, 120_000_000, 144_000_000],
            "hse+pll": [48_000_000, 56_000_000, 72_000_000, 96_000_000, 120_000_000, 144_000_000],
        },
        "ch32x035": {
            "hsi+pll": [8_000_000, 12_000_000, 16_000_000, 24_000_000, 48_000_000],
            "hse+pll": [],
        },
        "ch32l10x": {
            "hsi+pll": [48_000_000, 56_000_000, 72_000_000, 96_000_000],
            "hse+pll": [48_000_000, 56_000_000, 72_000_000, 96_000_000],
        },
        "ch641": {
            "hsi+pll": [8_000_000, 24_000_000, 48_000_000],
            "hse+pll": []
        },
        "ch643": {
            "hsi+pll": [8_000_000, 12_000_000, 16_000_000, 24_000_000, 48_000_000],
            "hse+pll": []
        },
    }
    CH56_FREQS_MHZ = {15, 30, 60, 80, 96, 120}

    ALLOWED_SOURCES = {"hsi", "hse", "hsi+pll", "hse+pll", "hsilp"}

    board_config = env.BoardConfig()
    spl_series = board_config.get("build.spl_series")
    clock_source = board_config.get("build.clock_source")
    f_cpu_str = board_config.get("build.f_cpu", "0")

    match = re.match(r"\d+", f_cpu_str)
    if not match:
        raise UserError(f"Invalid f_cpu value: {f_cpu_str}")
    f_cpu = int(match.group(0))

    if clock_source not in ALLOWED_SOURCES:
        raise UserError(f"Invalid clock source: {clock_source}. Must be one of: {', '.join(sorted(ALLOWED_SOURCES))}")

    defines = []
    applied_macro, applied_freq = None, None

    if spl_series.startswith("ch56"):
        # CH56x chips: define FREQ_SYS macro with frequency in Hz
        freq_mhz = f_cpu // 1_000_000
        if freq_mhz not in CH56_FREQS_MHZ:
            raise UserError(
                f"Invalid frequency {freq_mhz} MHz for {spl_series}. Allowed: {', '.join(str(f) for f in sorted(CH56_FREQS_MHZ))} MHz"
            )
        defines.append(("FREQ_SYS", f_cpu))
        applied_macro = f"FREQ_SYS={f_cpu}"
        applied_freq = f_cpu
    # CH57x, CH58x, CH59x series use an explicit call with a constant, no FREQ_SYS macro
    elif spl_series.startswith("ch5"):
        print(f"Skipping clock macro configuration for series {spl_series}.")
        return
    else:
        if clock_source == "hsi":
            applied_macro = "SYSCLK_FREQ_HSI=HSI_VALUE"
            defines.append(("SYSCLK_FREQ_HSI", "HSI_VALUE"))
        elif clock_source == "hse":
            applied_macro = "SYSCLK_FREQ_HSE=HSE_VALUE"
            defines.append(("SYSCLK_FREQ_HSE", "HSE_VALUE"))
        elif clock_source == "hsilp":
            applied_macro = "SYSCLK_FREQ_HSI_LP=HSI_LP_VALUE"
            defines.append(("SYSCLK_FREQ_HSI_LP", "HSI_LP_VALUE"))
        elif clock_source in ("hsi+pll", "hse+pll"):
            if spl_series not in VALID_PLL_FREQS:
                raise UserError(f"Unknown SPL series '{spl_series}' for PLL frequency validation")

            valid_freqs = VALID_PLL_FREQS[spl_series][clock_source]
            if f_cpu not in valid_freqs:
                raise UserError(
                    f"Invalid frequency {f_cpu} Hz for {clock_source} on {spl_series}. "
                    f"Allowed: {', '.join(str(f) for f in valid_freqs)}"
                )

            macro_name = f"SYSCLK_FREQ_{f_cpu // 1_000_000}MHz_{'HSI' if clock_source.startswith('hsi') else 'HSE'}"
            defines.append((macro_name, f_cpu))
            applied_macro = f"{macro_name}={f_cpu}"
            applied_freq = f_cpu

    env.Append(CPPDEFINES=defines)

    print("Clock configuration:")
    print(f"  Source: {clock_source}")
    if applied_freq:
        print(f"  Frequency: {applied_freq} Hz")
    print(f"  Macro: {applied_macro}")

validate_and_define_sysclk(env)
