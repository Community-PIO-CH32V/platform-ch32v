from os.path import isdir, isfile, join, dirname, realpath
from string import Template
from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()
chip_series = board.get("build.mcu")[0:len("ch32vxx")] + "x"

# import NoneOS SDK settings
env.SConscript("noneos_sdk.py")

FRAMEWORK_DIR = platform.get_package_dir("framework-wch-freertos")
assert isdir(FRAMEWORK_DIR)
# e.g., FreeRTOS_ch32v30x
freertos_subseries = f"FreeRTOS_{chip_series}"

env.Append(
    CPPPATH=[
        join(FRAMEWORK_DIR, freertos_subseries, "include"),
        join(FRAMEWORK_DIR, freertos_subseries, "portable", "Common"),
        join(FRAMEWORK_DIR, freertos_subseries, "portable", "GCC", "RISC-V"),
        join(FRAMEWORK_DIR, freertos_subseries, "portable", "GCC", "RISC-V", "chip_specific_extensions", "RV32I_PFIC_no_extensions"),
        join(FRAMEWORK_DIR, freertos_subseries, "portable", "MemMang"),
        join(FRAMEWORK_DIR, freertos_subseries),
        # user will likely have the FreeRTOSConfig.h located in the main source directory, so include it for the build too
        "$PROJECT_SRC_DIR"
    ],
    CPPDEFINES=[
        # the startup.S file needs very nifty different code if FreeRTOS is running
        # affects mstatus (Machine Status) registers
        # otherwise tasks just won't execute.
        "__PIO_BUILD_FREERTOS__"
    ]
)

env.BuildSources(
    join("$BUILD_DIR", "FrameworkFreeRTOSCore"),
    join(FRAMEWORK_DIR, freertos_subseries),
    # Just like the IDE, we do not build MPU Wrappers
    "+<*> -<%s>" % join("portable", "Common", "mpu_wrappers.c")
)