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

FRAMEWORK_DIR = platform.get_package_dir("framework-wch-tencentos")
assert isdir(FRAMEWORK_DIR)
# e.g., TencentOS_Tiny_ch32v30x
tencent_subseries = f"TencentOS_Tiny_{chip_series}"

env.Append(
    CPPPATH=[
        join(FRAMEWORK_DIR, tencent_subseries, "arch", "risc-v", "common", "include"),
        join(FRAMEWORK_DIR, tencent_subseries, "arch", "risc-v", "common"),
        join(FRAMEWORK_DIR, tencent_subseries, "arch", "risc-v", "rv32", "gcc"),
        join(FRAMEWORK_DIR, tencent_subseries, "kernel", "core", "include"),
        join(FRAMEWORK_DIR, tencent_subseries, "kernel", "core"),
        join(FRAMEWORK_DIR, tencent_subseries, "kernel", "hal", "include"),
        join(FRAMEWORK_DIR, tencent_subseries, "kernel", "hal"),
        join(FRAMEWORK_DIR, tencent_subseries, "kernel", "pm", "include"),
        join(FRAMEWORK_DIR, tencent_subseries, "kernel", "pm"),
        join(FRAMEWORK_DIR, tencent_subseries, "TOS_CONFIG"),
        # ch32v_it.h is mandatory for TencentOS to build, this will likely be included
        # in the user's directory.
        "$PROJECT_SRC_DIR"
    ],
    CPPDEFINES=[
        # the startup.S file needs very nifty different code if Harmony LiteOS is running
        # affects mstatus (Machine Status) registers
        # otherwise tasks just won't execute.
        "__PIO_BUILD_TENCENT_OS__"
    ]
)

env.BuildSources(
    join("$BUILD_DIR", "FrameworkTencentCore"),
    join(FRAMEWORK_DIR, tencent_subseries)
)