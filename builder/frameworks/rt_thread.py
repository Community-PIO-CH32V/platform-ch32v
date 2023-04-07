from os.path import isdir, isfile, join, dirname, realpath
from os import sep
from string import Template
from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()
chip_series: str = board.get("build.series", "")[0:-1].lower() + "x"

if chip_series.startswith("ch5"):
    # we need to make use of that special startup file which redirects all interrupts speciall
    board.update("build.use_builtin_startup_file", "no")

# import NoneOS SDK settings
env.SConscript("noneos_sdk.py")

FRAMEWORK_DIR = platform.get_package_dir("framework-wch-rtthread")
assert isdir(FRAMEWORK_DIR)
# e.g., rtthread_ch32v30x
rtthread_subseries = f"rtthread_{chip_series}"

env.Append(
    CPPPATH=[
        join(FRAMEWORK_DIR, rtthread_subseries, "include"),
        join(FRAMEWORK_DIR, rtthread_subseries, "include", "libc"),
        join(FRAMEWORK_DIR, rtthread_subseries, "src"),
        join(FRAMEWORK_DIR, rtthread_subseries),
        join(FRAMEWORK_DIR, rtthread_subseries, "components", "drivers", "include"),
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
if chip_series.startswith("ch5"):
    env.Append(CPPPATH=[
        # exists for ch5xx
        join(FRAMEWORK_DIR, rtthread_subseries, "libcpu", "WCH", "Qingke_V4A"),
        join(FRAMEWORK_DIR, rtthread_subseries, "components", "drivers", "ipc"),
        join(FRAMEWORK_DIR, rtthread_subseries, "bsp"),
    ])
else:
    env.Append(CPPPATH=[
        join(FRAMEWORK_DIR, rtthread_subseries, "drivers"),
        join(FRAMEWORK_DIR, rtthread_subseries, "libcpu", "risc-v"),
        join(FRAMEWORK_DIR, rtthread_subseries, "libcpu", "risc-v", "common"),
        join(FRAMEWORK_DIR, rtthread_subseries, "components", "drivers", "misc"),
        join(FRAMEWORK_DIR, rtthread_subseries, "components", "drivers", "serial"),
    ])

env.BuildSources(
    join("$BUILD_DIR", "FrameworkRTThreadCore"),
    join(FRAMEWORK_DIR, rtthread_subseries)
)