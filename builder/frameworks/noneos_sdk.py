from os.path import isdir, isfile, join, dirname, realpath
from string import Template
from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()
# convert MCU name (e.g. "ch32v307") to series (e.g. "ch32v30x")
chip_series = board.get("build.mcu")[0:len("ch32vxx")] + "x"
# import default build settings
env.SConscript("_bare.py")

FRAMEWORK_DIR = platform.get_package_dir("framework-wch-noneos-sdk")
assert isdir(FRAMEWORK_DIR)

def get_flag_value(flag_name:str, default_val:bool):
    flag_val = board.get("build.%s" % flag_name, default_val)
    flag_val = str(flag_val).lower() in ("1", "yes", "true")
    return flag_val

# the linker script also uses $ on it, so we can't use that as the
# variable identifier for the substitution engine.
class CustomTemplate(Template):
	delimiter = "#"

def get_linker_script(mcu: str):
    default_ldscript = join(env.subst("$BUILD_DIR"), "Link.ld")

    ram = board.get("upload.maximum_ram_size", 0)
    flash = board.get("upload.maximum_size", 0)
    flash_start = int(board.get("upload.offset_address", "0x00000000"), 0)
    # linker scripts use 256 bytes of stack only for v003 series, otherwise
    # always 2K.
    stack_size = 256 if mcu.startswith("ch32v003") else 2048
    # custom stack size wanted?
    if board.get("build.stack_size", "") != "":
        stack_size = int(board.get("build.stack_size"))
    template_file = join(FRAMEWORK_DIR, "platformio",
                         "ldscripts", "Link.tpl")
    content = ""
    with open(template_file) as fp:
        data = CustomTemplate(fp.read())
        content = data.substitute(
            stack=hex(0x20000000 + ram), # 0x20000000 - start address for RAM
            ram=str(int(ram/1024)) + "K",
            flash=str(int(flash/1024)) + "K",
            flash_start=hex(flash_start),
            stack_size=stack_size
        )

    with open(default_ldscript, "w") as fp:
        fp.write(content)

    return default_ldscript

def get_startup_filename(board):
    # the gen_boarddefs.py already put the classification macro
    # into the extra_flags. Read them again and map them onto the startup files.
    extra_flags = str(board.get("build.extra_flags", "")).split(" ")
    class_to_startup = {
        "CH32V20x_D6": "startup_ch32v20x_D6.S",
        "CH32V20x_D8": "startup_ch32v20x_D8.S",
        "CH32V20x_D8W": "startup_ch32v20x_D8W.S",
        "CH32V30x_D8": "startup_ch32v30x_D8.S",
        "CH32V30x_D8C": "startup_ch32v30x_D8C.S"
    }
    startup_file = None
    for k, v in class_to_startup.items():
        if any([f"-D{k}" == flag for flag in extra_flags]):
            startup_file = v
    if startup_file is None:
        chip_name = str(board.get("build.mcu", "")).lower()
        if chip_name.startswith("ch32v0"):
            return "startup_ch32v00x.S"
        elif chip_name.startswith("ch32v1"):
            return "startup_ch32v10x.S"
    if startup_file is None:
        print("Failed to find startup file for board " + str(board))
        env.Exit(-1)
    return startup_file

if get_flag_value("use_lto", False):
    env.Append(LINKFLAGS=["-flto"], CCFLAGS=["-flto"])

env.Append(
    CPPPATH=[
        join(FRAMEWORK_DIR, "Core", chip_series),
        join(FRAMEWORK_DIR, "Peripheral", chip_series, "inc"),
        join(FRAMEWORK_DIR, "Peripheral", chip_series, "src")
        # Paths for startup and system are addeed later if wanted
    ]
)

if not board.get("build.ldscript", ""):
    env.Replace(
        LDSCRIPT_PATH=get_linker_script(board.get("build.mcu")))

libs = []

env.BuildSources(
    join("$BUILD_DIR", "FrameworkNoneOSCore"),
    join(FRAMEWORK_DIR, "Core", chip_series)
)

if get_flag_value("use_builtin_startup_file", True):
    env.Append(CPPPATH=[join(FRAMEWORK_DIR, "Startup")])
    startup_file_filter = "-<*> +<%s>" % get_startup_filename(board)
    env.BuildSources(
        join("$BUILD_DIR", "FrameworkNoneOSStartup"),
        join(
            FRAMEWORK_DIR, "Startup"
        ),
        startup_file_filter
    )

# for clock init etc.
if get_flag_value("use_builtin_system_code", True):
    env.Append(CPPPATH=[join(FRAMEWORK_DIR, "System", chip_series)])
    env.BuildSources(
        join("$BUILD_DIR", "FrameworkNoneOSSSystem"),
        join(FRAMEWORK_DIR, "System", chip_series)
    )

# Do not include Debug.c/.h by default, bloats up firmware if unneeded
# Weirdly enough, the SDK code for V103 expects the debug.h file to be present
# in the build for Delay_US shennanigans.
include_debug_code_by_default = True if chip_series == "ch32v10x" else False
if get_flag_value("use_builtin_debug_code", include_debug_code_by_default):
    env.Append(CPPPATH=[join(FRAMEWORK_DIR, "Debug", chip_series)])
    env.BuildSources(
        join("$BUILD_DIR", "FrameworkNoneOSDebug"),
        join(FRAMEWORK_DIR, "Debug", chip_series)
    )

libs.append(env.BuildLibrary(
    join("$BUILD_DIR", "FrameworkNoneOSVariant"),
    join(FRAMEWORK_DIR, "Peripheral", chip_series, "src")
))

env.Append(LIBS=libs)