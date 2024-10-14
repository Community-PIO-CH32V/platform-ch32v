from os.path import join
import sys
from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()
mcu = env.BoardConfig().get("build.mcu")
chip_name = str(board.get("build.mcu", "")).lower()

# import default build settings
env.SConscript("_bare.py")

# .. but change some settings
if "-std=gnu99" in env["CFLAGS"]:
    env["CFLAGS"].remove("-std=gnu99")

# get framework directory
FRAMEWORK_DIR = platform.get_package_dir("framework-ch32v003fun")

# Add include paths and defines
env.Append(
    CPPPATH=[
        join(FRAMEWORK_DIR, "ch32v003fun"),
        join(FRAMEWORK_DIR, "extralibs"),
        # user will likely have the funconfig.h located in the main source directory, so include it for the build too
        "$PROJECT_SRC_DIR"
    ],
    CPPDEFINES=[
        # not yet used for anything, just identification
        "__PIO_BUILD_CH32V003FUN__"
    ],
    CFLAGS=[
        "-std=gnu11"
    ],
    CCFLAGS=[
        "-flto",
        "-static-libgcc",
        # Problem: When we disable the stdlib and don't link in any libc, we break compilation with the MounRiver RISC-V compiler.
        # "undefined reference to `__riscv_save_0'""
        # The compiler seems to always generate these symbols even though we might not want it to use the builtin stdlib.
        # We fix that up by including the compiler's libgcc anyways afterwards.
        "-nostdlib"
    ],
    LINKFLAGS=[
        "-flto",
        "-static-libgcc",
        "-nostdlib"
    ]
)

# same logic as in makefile: For ch32v003, use given libgcc
if chip_name.startswith("ch32v003"):
    env.Append(LIBS=[File(join(FRAMEWORK_DIR, "misc", "libgcc.a"))])
else:
    env.Append(LIBS=["gcc"]) # use compiler's builtin one

# Returns TARGET_MCU, MCU_PACKAGE and TARGET_MCU_LD values
# In the same way that the Makefile would do.
def get_ld_defines(chip_name: str):
    target_mcu: str = ""
    mcu_package: int = 0
    target_mcu_ld: int = 0
    if chip_name.startswith("ch32v003"):
        target_mcu = "CH32V003"
        target_mcu_ld = 0
    else:
        mcu_package = 1
        if chip_name.startswith("ch32v10"):
            target_mcu = chip_name.upper()[0:len("ch32v10x")]
            if "r8" in chip_name:
                mcu_package = 1
            elif "c8" in chip_name:
                mcu_package = 1
            elif "c6" in chip_name:
                mcu_package = 2
            target_mcu_ld = 1
        elif chip_name.startswith("ch32x03"):
            target_mcu = chip_name.upper()[0:len("ch32x035")]
            if "f8" in chip_name:
                mcu_package = 1
            elif "r8" in chip_name:
                mcu_package = 1
            elif "k8" in chip_name:
                mcu_package = 1
            elif "c8" in chip_name:
                mcu_package = 1
            elif "g8" in chip_name:
                mcu_package = 1
            elif "g6" in chip_name:
                mcu_package = 1
            elif "f7" in chip_name:
                mcu_package = 1
            target_mcu_ld = 4
        elif chip_name.startswith("ch32v20"):
            target_mcu = chip_name.upper()[0:len("ch32v20x")]
            if "f8" in chip_name:
                mcu_package = 1
            elif "g8" in chip_name:
                mcu_package = 1
            elif "k8" in chip_name:
                mcu_package = 1
            elif "c8" in chip_name:
                mcu_package = 1
            elif "f6" in chip_name:
                mcu_package = 2
            elif "k6" in chip_name:
                mcu_package = 2
            elif "c6" in chip_name:
                mcu_package = 2
            elif "rb" in chip_name:
                mcu_package = 3
            elif "gb" in chip_name:
                mcu_package = 3
            elif "cb" in chip_name:
                mcu_package = 3
            elif "wb" in chip_name:
                mcu_package = 3
            target_mcu_ld = 2
        elif chip_name.startswith("ch32v30"):
            target_mcu = chip_name.upper()[0:len("ch32v30x")]
            if "rc" in chip_name:
                mcu_package = 1
            elif "vc" in chip_name:
                mcu_package = 1
            elif "wc" in chip_name:
                mcu_package = 1
            elif "cb" in chip_name:
                mcu_package = 2
            elif "fb" in chip_name:
                mcu_package = 2
            elif "rb" in chip_name:
                mcu_package = 2
            target_mcu_ld = 3
        else:
            sys.stdout.write("Unkonwn MCU %s\n" % chip_name)
            env.Exit(-1)
    return (target_mcu, mcu_package, target_mcu_ld)

# retrieve needed macro values
target_mcu, mcu_package, target_mcu_ld = get_ld_defines(chip_name)

# Add "" to the build path to fix spaces
BUILD_DIR_FIX:str = '\"$BUILD_DIR\"'

# Let the LD script be generated right before the .elf is built
env.AddPreAction(
    "${BUILD_DIR_FIX}/${PROGNAME}.elf",
    env.VerboseAction(" ".join([
        "$CC",
        "-E",
        "-P",
        "-x",
        "c",
        "-DTARGET_MCU=%s" % target_mcu,
        "-DMCU_PACKAGE=%d" % mcu_package,
        "-DTARGET_MCU_LD=%d" % target_mcu_ld,
        join(FRAMEWORK_DIR, "ch32v003fun", "ch32v003fun.ld"),
        ">",
        join("${BUILD_DIR_FIX}", "ldscript.ld")
    ]), "Building %s" % join("${BUILD_DIR_FIX}", "ldscript.ld"))
)

# Already put in the right path for the to-be-generated file
env.Replace(LDSCRIPT_PATH=join("${BUILD_DIR_FIX}", "ldscript.ld"))

# build actual ch32v003fun source file
env.BuildSources(
    join("${BUILD_DIR_FIX}", "FrameworkCh32v003fun"),
    join(FRAMEWORK_DIR, "ch32v003fun")
)
