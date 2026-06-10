from SCons.Errors import UserError
from SCons.Script import Environment
import re

# setup clocks
def validate_and_define_sysclk(env: Environment):
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
    spl_series = str(board_config.get("build.spl_series"))
    clock_source = str(board_config.get("build.clock_source"))
    f_cpu_str = str(board_config.get("build.f_cpu", "0"))

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
    elif spl_series.startswith("ch32v4"):
        SYSCLOCK_PLL_MACROS = {
            60_000_000: "SYSCLK_120MHz_HCLK_60MHz",
            120_000_000: "SYSCLK_240MHz_HCLK_120MHz",
            175_000_000: "SYSCLK_350MHz_HCLK_175MHz",
            200_000_000: "SYSCLK_400MHz_HCLK_200MHz",
        }
        if clock_source not in ("hsi+pll", "hse+pll"):
            raise UserError(f"Invalid clock source {clock_source} for {spl_series}. Must be 'hsi+pll' or 'hse+pll'")
        if f_cpu not in SYSCLOCK_PLL_MACROS:
            raise UserError(f"Invalid frequency {f_cpu} Hz for {spl_series}. Allowed: {', '.join(str(f) for f in SYSCLOCK_PLL_MACROS.keys())} Hz")
        macro_name = SYSCLOCK_PLL_MACROS[f_cpu] + ("_HSI" if clock_source == "hsi+pll" else "_HSE")
        defines.append((macro_name, f_cpu))
        applied_macro = macro_name
        applied_freq = f_cpu
    elif spl_series.startswith("ch32h41"):
        # the V3F sets up the PLL for both itself and the V5F.
        # configuring SYSCLK mainly and the dividers.
        # the V5F system code only reads the configured frequency.
        # get the board_build.cpu_core to see if we are the v3f if it exists
        cpu_core = str(board_config.get("build.cpu_core", "v3f"))
        if cpu_core != "v3f":
            print(f"Skipping clock macro configuration for CPU core {cpu_core}.")
            return
        # interpret f_cpu as sysclock.
        SYSCLOCK_PLL_MACROS = {
            400_000_000: "SYSCLK_400M_CoreCLK_V5F_400M_V3F_100M",
            480_000_000: "SYSCLK_480M_CoreCLK_V5F_240M_V3F_120M",
            # 480 MHz sysclock can also run V5F at 480MHz and V3F at 120MHz, but "with a temperature not exceeding 70 °C and good heat dissipation"
            # ignore that for now. (SYSCLK_480M_CoreCLK_V5F_480M_V3F_120M_HSE)
        }
        if clock_source not in ("hsi+pll", "hse+pll"):
            raise UserError(f"Invalid clock source {clock_source} for {spl_series}. Must be 'hsi+pll' or 'hse+pll'")
        if f_cpu not in SYSCLOCK_PLL_MACROS:
            raise UserError(f"Invalid frequency {f_cpu} Hz for {spl_series}. Allowed: {', '.join(str(f) for f in SYSCLOCK_PLL_MACROS.keys())} Hz")
        macro_name = SYSCLOCK_PLL_MACROS[f_cpu] + ("_HSI" if clock_source == "hsi+pll" else "_HSE")
        defines.append((macro_name, f_cpu))
        applied_macro = macro_name
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
            # some SDK files have misspellings, e.g. "48MHZ_HSI" and "8MHz_HSI" in ch32v003.
            # support both by uppercasing the macro name.
            defines.append((macro_name.upper(), f_cpu))
            applied_macro = f"{macro_name}={f_cpu}"
            applied_freq = f_cpu

    env.Append(CPPDEFINES=defines)

    print("Clock configuration:")
    print(f"  Source: {clock_source}")
    if applied_freq:
        print(f"  Frequency: {applied_freq} Hz")
    print(f"  Macro: {applied_macro}")
