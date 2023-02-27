from os.path import isdir, isfile, join, dirname, realpath
from os import sep
from string import Template
from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()
chip_series = board.get("build.mcu")[0:len("ch32vxx")] + "x"

# import NoneOS SDK settings
env.SConscript("noneos_sdk.py")

FRAMEWORK_DIR = platform.get_package_dir("framework-wch-harmony-liteos")
assert isdir(FRAMEWORK_DIR)
# e.g., LiteOS_ch32v30x
liteos_subseries = f"LiteOS_{chip_series}"

env.Append(
    CPPPATH=[
        join(FRAMEWORK_DIR, liteos_subseries, "components", "backtrace"),
        join(FRAMEWORK_DIR, liteos_subseries, "components", "cpup"),
        join(FRAMEWORK_DIR, liteos_subseries, "components", "power"),
        join(FRAMEWORK_DIR, liteos_subseries, "kernel", "arch", "include"),
        join(FRAMEWORK_DIR, liteos_subseries, "kernel", "arch", "risc-v", "V4A", "gcc"),
        join(FRAMEWORK_DIR, liteos_subseries, "kernel", "include"),
        join(FRAMEWORK_DIR, liteos_subseries, "kernel", "src"),
        join(FRAMEWORK_DIR, liteos_subseries, "kernel", "src", "mm"),
        join(FRAMEWORK_DIR, liteos_subseries, "utils", "internal"),
        join(FRAMEWORK_DIR, liteos_subseries, "utils"),
        join(FRAMEWORK_DIR, liteos_subseries, "third_party", "bounds_checking_function", "include"),
        join(FRAMEWORK_DIR, liteos_subseries, "third_party", "bounds_checking_function", "src"),
        # user will likely have the target_config.h located in the main source directory, so include it for the build too
        "$PROJECT_SRC_DIR"
    ],
    CPPDEFINES=[
        # the startup.S file needs very nifty different code if Harmony LiteOS is running
        # affects mstatus (Machine Status) registers
        # otherwise tasks just won't execute.
        "__PIO_BUILD_HARMONY_LITEOS__"
    ]
)

# Just like the IDE, we do not build certain folders
folder_exclude_list = [
    "components/cppsupport",
    "components/exchook",
    "components/fs",
    "components/net",
    "third_party/cmsis",
    "kal",
    "testsuits"
]
filter_expr = "+<*>"
for excl in folder_exclude_list:
    filter_expr += f" -<{excl}>"

env.BuildSources(
    join("$BUILD_DIR", "FrameworkHarmonyLiteOSCore"),
    join(FRAMEWORK_DIR, liteos_subseries),
    filter_expr
)