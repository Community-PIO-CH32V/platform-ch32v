from os.path import isdir, isfile, join, dirname, realpath, isabs
from string import Template
from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()
mcu_l = board.get("build.mcu", "").lower()
# for a MCU name (e.g. "ch32v307") we need the series (e.g. "ch32v30x")
chip_series: str = board.get("build.spl_series", "")
# import default build settings
env.SConscript("_bare.py")

FRAMEWORK_DIR = platform.get_package_dir("framework-wch-noneos-sdk")
assert isdir(FRAMEWORK_DIR)

# helper vars
has_system_code = not chip_series.startswith("ch5")
has_debug_code = not chip_series.startswith("ch5")

def get_flag_value(flag_name:str, default_val:bool):
    flag_val = board.get("build.%s" % flag_name, default_val)
    flag_val = str(flag_val).lower() in ("1", "yes", "true")
    return flag_val

# the linker script also uses $ on it, so we can't use that as the
# variable identifier for the substitution engine.
class CustomTemplate(Template):
	delimiter = "#"

def get_linker_script(mcu: str, core: str) -> str:
    default_ldscript = join(env.subst("$BUILD_DIR"), "Link.ld")

    # for now, when building for ch56x, ch57x, ch58x, use the original linker scripts..
    if mcu.lower().startswith("ch5"):
        if mcu.lower().startswith("ch585") or mcu.lower().startswith("ch584"):
            return join(FRAMEWORK_DIR, "platformio", "ldscripts", "Link_CH585") + ".ld"
        return join(FRAMEWORK_DIR, "platformio", "ldscripts", "Link_" + board.get("build.series", "")[0:-1].upper() + "x") + ".ld"
    # again special stuff for H41x series, they share some FLASH and RAM and have seperate linker scripts
    # e.g., Link_CH32H417_v3f.ld or Link_CH32H417_v5f.ld
    if mcu.lower().startswith("ch32h41"):
        return join(FRAMEWORK_DIR, "platformio", "ldscripts", "Link_CH32H417_" + core.lower()) + ".ld"
    ram = board.get("upload.maximum_ram_size", 0)
    flash = board.get("upload.maximum_size", 0)
    flash_start = int(board.get("upload.offset_address", "0x00000000"), 0)
    # linker scripts use 256 bytes or 512 of stack only for v00x series, otherwise
    # always 2K.
    stack_size = 2048
    if ram <= 2048: # ch32v003
        stack_size = 256
    elif ram <= 8192: # some ch32v00x
        stack_size = 512
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
        "CH32V30x_D8C": "startup_ch32v30x_D8C.S",
        "CH32X035": "startup_ch32x035.S",
        "CH32X033": "startup_ch32x035.S",
        "CH32L103": "startup_ch32l103.S",
    }
    startup_file = None
    for k, v in class_to_startup.items():
        if any([f"-D{k}" == flag for flag in extra_flags]):
            startup_file = v
    if startup_file is None:
        chip_name = str(board.get("build.mcu", "")).lower()
        if chip_name.startswith("ch32v003"):
            return "startup_ch32v00x.S"
        elif chip_name.startswith("ch32v00") or chip_name.startswith("ch32m007"):
            return "startup_ch32v00Xx.S"
        elif chip_name.startswith("ch32v1"):
            return "startup_ch32v10x.S"
        elif chip_name.startswith("ch5") or chip_name.startswith("ch6"):
            return "startup_" + board.get("build.series").lower()[0:len("ch5xx")] + ".S"
        # for H41x series we have to also check whether to use the v3f or v5f startup file (startup_ch32h417_v3f.S vs startup_ch32h417_v5f.S)
        elif chip_name.startswith("ch32h41"):
            cpu_core = str(board.get("build.cpu_core", "v3f")).lower()
            if cpu_core == "v3f":
                return "startup_ch32h417_v3f.S"
            else:
                return "startup_ch32h417_v5f.S"
    if startup_file is None:
        print("Failed to find startup file for board " + str(board))
        env.Exit(-1)
    return startup_file

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
        LDSCRIPT_PATH=get_linker_script(board.get("build.mcu"), board.get("build.cpu_core", "v3f")))

libs = []

env.BuildSources(
    join("$BUILD_DIR", "FrameworkNoneOSCore"),
    join(FRAMEWORK_DIR, "Core", chip_series)
)

startup_filename = board.get("build.startup", None)
if startup_filename :
    # evaluate possible variables in the path
    startup_filename = env.subst(startup_filename)
    # if not absolute path, assume relative to project dir.
    if not isabs(startup_filename):
        startup_filename = join(env.subst("$PROJECT_DIR"), startup_filename)
    startup_filename = realpath(startup_filename)
    env.Append(CPPPATH=[dirname(startup_filename)])
    print("Using custom startup file: %s" % startup_filename)
    if not isfile(startup_filename):
        print("Provided startup file not found: %s" % startup_filename)
        env.Exit(-1)
    env.BuildSources(
        join("$BUILD_DIR", "ProjectStartup"),
        dirname(startup_filename),
        "-<*> +<%s>" % startup_filename
    )
elif get_flag_value("use_builtin_startup_file", True):
    env.Append(CPPPATH=[join(FRAMEWORK_DIR, "Startup")])
    env.BuildSources(
        join("$BUILD_DIR", "FrameworkNoneOSStartup"),
        join(FRAMEWORK_DIR, "Startup"),
        "-<*> +<%s>" % get_startup_filename(board)
    )

# for clock init etc.
if get_flag_value("use_builtin_system_code", True) and has_system_code:
    # actually the H41x insists on being special again. depending on the core,
    # its in ch32h417/v3f or ch32h417/v5f (relative to System folder).
    system_folder = chip_series
    if chip_series.startswith("ch32h41"):
        core = str(board.get("build.cpu_core", "v3f")).lower()
        system_folder = join("ch32h417", core.lower())
    env.Append(CPPPATH=[join(FRAMEWORK_DIR, "System", system_folder)])
    env.BuildSources(
        join("$BUILD_DIR", "FrameworkNoneOSSSystem"),
        join(FRAMEWORK_DIR, "System", system_folder)
    )

# By default, include the Debug.h/.c code.
# practically every example needs it. Can be turned of in the platformio.ini.
if get_flag_value("use_builtin_debug_code", True) and has_debug_code:
    env.Append(CPPPATH=[join(FRAMEWORK_DIR, "Debug", chip_series)])
    env.BuildSources(
        join("$BUILD_DIR", "FrameworkNoneOSDebug"),
        join(FRAMEWORK_DIR, "Debug", chip_series)
    )

# Auto-compile in empty _init() and _fini() functions for C++ support 
if get_flag_value("cpp_support", True):
    env.Append(CPPDEFINES=["__PIO_CPP_SUPPORT__"])
    env.BuildSources(
        join("$BUILD_DIR", "FrameworkInitFini"),
        join(FRAMEWORK_DIR, "CPP_Support")
    )

libs.append(env.BuildLibrary(
    join("$BUILD_DIR", "FrameworkNoneOSVariant"),
    join(FRAMEWORK_DIR, "Peripheral", chip_series, "src")
))

# mandatory for compilation
if chip_series.startswith("ch57") or chip_series.startswith("ch58") or chip_series.startswith("ch59"):
    env.Append(LIBPATH=[join(FRAMEWORK_DIR, "Peripheral", chip_series, "src")])
    if chip_series.startswith("ch57") and not chip_series.startswith("ch572") and not chip_series.startswith("ch570"):
        libs += ["ISP573"] # actually for 571 and 573 
    elif chip_series.startswith("ch572") or chip_series.startswith("ch570"):
        libs += ["ISP572"]  # for 570 and 572
    elif chip_series.startswith("ch58") and not chip_series.startswith("ch585") and not chip_series.startswith("ch584"):
        libs += ["ISP583"]
    elif chip_series.startswith("ch585") or chip_series.startswith("ch584"):
        libs += ["ISP585"]
    else:
        libs += ["ISP592"]

env.Append(LIBS=libs)