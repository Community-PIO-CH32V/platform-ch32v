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

def get_linker_script(mcu):
    default_ldscript = join(env.subst("$BUILD_DIR"), "Link.ld")

    ram = board.get("upload.maximum_ram_size", 0)
    flash = board.get("upload.maximum_size", 0)
    flash_start = int(board.get("upload.offset_address", "0x00000000"), 0)
    stack_size = 2048 # default value for now
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
    # todo generalize this
    return "startup_ch32v30x_D8C.S"

if get_flag_value("use_lto", False):
    env.Append(LINKFLAGS=["-flto"], CCFLAGS=["-flto"])

env.Append(
    CPPPATH=[
        join(FRAMEWORK_DIR, "Core"),
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
    join(FRAMEWORK_DIR, "Core")
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
if get_flag_value("use_builtin_debug_code", False):
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