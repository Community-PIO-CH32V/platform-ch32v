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

FRAMEWORK_DIR = platform.get_package_dir("framework-wch-rtthread")
assert isdir(FRAMEWORK_DIR)
# e.g., rtthread_ch32v30x
rtthread_subseries = f"rtthread_{chip_series}"

env.Append(
    CPPPATH=[
        join(FRAMEWORK_DIR, rtthread_subseries, "drivers"),
        join(FRAMEWORK_DIR, rtthread_subseries, "include"),
        join(FRAMEWORK_DIR, rtthread_subseries, "include", "libc"),
        join(FRAMEWORK_DIR, rtthread_subseries, "libcpu", "risc-v"),
        join(FRAMEWORK_DIR, rtthread_subseries, "libcpu", "risc-v", "common"),
        join(FRAMEWORK_DIR, rtthread_subseries, "src"),
        join(FRAMEWORK_DIR, rtthread_subseries),
        join(FRAMEWORK_DIR, rtthread_subseries, "components", "drivers", "include"),
        join(FRAMEWORK_DIR, rtthread_subseries, "components", "drivers", "misc"),
        join(FRAMEWORK_DIR, rtthread_subseries, "components", "drivers", "serial"),
        join(FRAMEWORK_DIR, rtthread_subseries, "components", "finsh"),
        # ch32v_it.h is mandatory for RT-Thread to build, this will likely be included
        # in the user's directory.
        "$PROJECT_SRC_DIR"
    ],
    CPPDEFINES=[
        # the startup.S file needs very nifty different code if Harmony LiteOS is running
        # affects mstatus (Machine Status) registers
        # otherwise tasks just won't execute.
        "__PIO_BUILD_RT_THREAD__"
    ]
)

env.BuildSources(
    join("$BUILD_DIR", "FrameworkRTThreadCore"),
    join(FRAMEWORK_DIR, rtthread_subseries)
)