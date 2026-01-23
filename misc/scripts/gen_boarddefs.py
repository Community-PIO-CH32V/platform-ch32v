#!/usr/bin/env python3
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import json

@dataclass
class ChipInfo:
    name: str
    flash_kb: int
    sram_kb: int
    freq_mhz: int
    package: str

    def get_classification_macro(self) -> Optional[str]:
        # I don't have a good answer for that except
        # copying the data from the reference manual
        # (CH32FV2x_V3xRM-1.pdf p.4)
        dev_classes = {
            "CH32F20x_D6": ["CH32F203K8", "CH32F203C6", "CH32F203C8"],
            "CH32F20x_D8": ["CH32F203CB", "CH32F203RC", "CH32F203VC", "CH32F203RB"],
            "CH32F20x_D8C": ["CH32F205RB", "CH32F207VC"],
            "CH32F20x_D8W": ["CH32F208RB", "CH32F208WB"],
            "CH32V20x_D6": ["CH32V203F6", "CH32V203G6", "CH32V203K6", "CH32V203F8", "CH32V203G8", "CH32V203K8", "CH32V203C6", "CH32V203C8"],
            "CH32V20x_D8": ["CH32V203RB"],
            "CH32V20x_D8W": ["CH32V208GB", "CH32V208CB", "CH32V208RB", "CH32V208WB"],
            "CH32V30x_D8": ["CH32V303CB", "CH32V303RB", "CH32V303RC", "CH32V303VC"],
            "CH32V30x_D8C": ["CH32V305", "CH32V307", "CH32V317"],
            "CH32V007_M007": ["CH32V007", "CH32M007"],
        }
        for dev_class, devs in dev_classes.items():
            if any([self.name.upper().startswith(chip) for chip in devs]):
                return dev_class
        # the V103 and V003 series intentionally has no classification macro
        # same as ch58x
        name_upper = self.name.upper()
        if any([name_upper.startswith("CH32V103"),
                name_upper.startswith("CH32V00"),
                name_upper.startswith("CH56"),
                name_upper.startswith("CH57"),
                name_upper.startswith("CH58"),
                name_upper.startswith("CH59"),
                name_upper.startswith("CH64"),
                name_upper.startswith("CH32X03"),
                name_upper.startswith("CH32L10")
                ]):
            return None
        print("ERROR: UNKNOWN CHIP / NO CLASSIFICATION KNOWN FOR " + self.name)
        exit(-1)

    def get_riscv_arch_and_abi(self) -> Tuple[str, str]:
        # ch32v30x is capable of rv32imafcxw
        # but SDK uses rv32imacxw (no floating point)
        # ch32v208 and ch32l103 is rv32imacxw (QingKe V4C)
        # other ch32v20x is rv32imacxw (QingKe V4B)
        # ch32v10x only rv32imac (RISC-V3A)
        # ch32v00x only rv32ecxw (RISC-V2A)
        name_lower = self.name.lower() 
        # applies to ch32v307 and ch32v317
        if name_lower.startswith("ch32v3"):
            return ("rv32imacxw", "ilp32")
        elif name_lower.startswith("ch32v2"):
            return ("rv32imacxw", "ilp32")
        elif name_lower.startswith("ch32v1"):
            return ("rv32imac", "ilp32")
        # applies only to ch32003
        elif name_lower.startswith("ch32v003") :
            return ("rv32ecxw", "ilp32e")
        # applies to ch32v002, 004, 005, 007, 007, M007
        elif name_lower.startswith("ch32v0") or name_lower.startswith("ch32m0") or name_lower.startswith("ch641"):
            return ("rv32ec_zmmul_xw", "ilp32e")
        elif name_lower.startswith("ch643"):
            return ("rv32imacxw", "ilp32")
        # applies to ch56x, ch57x, ch58x
        elif name_lower.startswith("ch5") and (name_lower.startswith("ch585") or name_lower.startswith("ch584")):
            return ("rv32imc_zba_zbb_zbc_zbs_xw", "ilp32")
        elif name_lower.startswith("ch5") and not name_lower.startswith("ch570") and not name_lower.startswith("ch572"):
            return ("rv32imac", "ilp32")
        elif name_lower.startswith("ch5") and (name_lower.startswith("ch570") or name_lower.startswith("ch572")):
            return ("rv32imc_zba_zbb_zbc_zbs_xw", "ilp32")
        elif name_lower.startswith("ch32x03"):
            return ("rv32imacxw", "ilp32")
        elif name_lower.startswith("ch32l1"):
            return ("rv32imacxw", "ilp32")
        else:
            print("ERROR: UNKNOWN CHIP ABI/ARCH FOR " + self.name)
            exit(-1)
            return ("unknown", "unknown")

    def chip_without_package(self) -> str:
        return self.name[:-2]

    def spl_series(self) -> str:
        name_lower = self.name.lower() 
        if name_lower.startswith("ch32v3"):
            return "ch32v30x"
        elif name_lower.startswith("ch32v2"):
            return "ch32v20x"
        elif name_lower.startswith("ch32v1"):
            return "ch32v10x"
        # applies only to ch32003
        elif name_lower.startswith("ch32v003") :
            return "ch32v00x"
        # applies to ch32v002, 004, 005, 007, 007, M007
        # Arduino core also calls this "CH32VM00X"
        elif name_lower.startswith("ch32v0") or name_lower.startswith("ch32m0"):
            return "ch32v00Xx"
        elif name_lower.startswith("ch641"):
            return "ch641"
        elif name_lower.startswith("ch643"):
            return "ch643"
        # applies to ch56x, ch57x, ch58x
        elif name_lower.startswith("ch56"):
            return "ch56x"
        elif name_lower.startswith("ch57") and not name_lower.startswith("ch570") and not name_lower.startswith("ch572"):
            return "ch57x"
        elif name_lower.startswith("ch57") and (name_lower.startswith("ch570") or name_lower.startswith("ch572")):
            return "ch572"
        elif name_lower.startswith("ch58") and not name_lower.startswith("ch585") and not name_lower.startswith("ch584"):
            return "ch58x"
        elif name_lower.startswith("ch58") and (name_lower.startswith("ch585") or name_lower.startswith("ch584")):
            return "ch585"
        elif name_lower.startswith("ch59"):
            return "ch59x"
        # both x035 and x033 deliberately
        elif name_lower.startswith("ch32x03"):
            return "ch32x035"
        elif name_lower.startswith("ch32l1"):
            return "ch32l10x"
        else:
            print("ERROR: UNKNOWN SPL FOLDER FOR " + self.name)
            exit(-1)
            return "unknown"

    def exact_series(self) -> str:
        if self.name.lower().startswith("ch58") and (self.name.lower().startswith("ch585") or self.name.lower().startswith("ch584")):
            return "ch585"
        if self.name.lower().startswith("ch5") and not self.name.lower().startswith("ch570") and not self.name.lower().startswith("ch572"):
            return self.name[0:len("ch58")].upper() + "X"
        # Hack: Even ch32x033 is recognized as x035 series.
        # This simplifies folder handling for frameworks like
        # FreeRTOS.
        if self.name.lower().startswith("ch32x03"):
            return "ch32x035"
        # Hack: A ch32v317 uses the same SDK as the ch32v307.
        if self.name.lower().startswith("ch32v317"):
            return "ch32v307"
        if self.name.lower().startswith("ch57") and (self.name.lower().startswith("ch570") or self.name.lower().startswith("ch572")):
            return "ch572"
        return self.name[0:len("ch32vxxx")]
    
    def get_svd_file(self) -> str:
        if self.name.lower().startswith("ch32v317"):
            return "CH32V317xx.svd"
        if self.name.lower().startswith("ch32v00") and not self.name.lower().startswith("ch32v003"):
            return "CH32V00Xxx.svd"
        if self.name.lower().startswith("ch5") or self.name.lower().startswith("ch6"):
            return self.name.upper()[0:len("chxxx")] + ".svd"
        return self.exact_series().upper() + "xx.svd"

chip_db: List[ChipInfo] = [
    # CH56x (configurable SRAM size, data flash)
    ChipInfo("CH569W", 448+32, 16+32, 120, "QFN68"),
    ChipInfo("CH565W", 448+32, 16+32, 120, "QFN68"),
    ChipInfo("CH565M", 448+32, 16+32, 120, "QFN40"),
    # CH57x
    ChipInfo("CH573X", 448+32, 16+2, 20, "QFN32"),
    ChipInfo("CH573F", 448+32, 16+2, 20, "QFN28"),
    ChipInfo("CH573Q", 192+32, 16+2, 20, "LQFP32"),
    ChipInfo("CH571F", 192+32, 16+2, 20, "QFN28"),
    ChipInfo("CH571D", 192+32, 16+2, 20, "QFN20"),
    ChipInfo("CH571K", 192+32, 16+2, 20, "ESSOP10"),
    ChipInfo("CH572D", 240+8, 12, 100, "QFN20"),
    ChipInfo("CH572Q", 240+8, 12, 100, "DFN10X3"),
    ChipInfo("CH572R", 240+8, 12, 100, "TSSOP16"),
    ChipInfo("CH570D", 240+8, 12, 100, "QFN20"),
    ChipInfo("CH570Q", 240+8, 12, 100, "DFN10X3"),
    ChipInfo("CH570E", 240+8, 12, 100, "SOP8"),
    # CH58x (has +32K data flash)
    ChipInfo("CH583M", 448+32, 32, 20, "QFN48"),
    ChipInfo("CH582M", 448+32, 32, 20, "QFN48"),
    ChipInfo("CH582F", 448+32, 32, 20, "QFN28"),
    ChipInfo("CH581F", 192+32, 32, 20, "QFN28"),
    # CH585 and CH584 (32K data flash, 24K bootloader, 448k codeflash)
    ChipInfo("CH585M", 448+32, 128, 78, "QFN48"),
    ChipInfo("CH585F", 448+32, 128, 78, "QFN32"),
    ChipInfo("CH585C", 448+32, 128, 78, "QFN26C3"),
    ChipInfo("CH585D", 448+32, 128, 78, "QFN20"),
    ChipInfo("CH584M", 448+32, 128, 78, "QFN48"),
    ChipInfo("CH584F", 448+32, 128, 78, "QFN32"),

    # CH59x (has +32K data flash, +24K bootloader)
    ChipInfo("CH592X", 448+24+32, 24+2, 60, "QFN32"),
    ChipInfo("CH592F", 448+24+32, 24+2, 60, "QFN28"),
    ChipInfo("CH591F", 192+24+32, 24+2, 60, "QFN28"),
    ChipInfo("CH591D", 192+24+32, 24+2, 60, "QFN20"),
    ChipInfo("CH591R", 192+24+32, 24+2, 60, "TSSOP16"),
    # CH641
    ChipInfo("CH641F", 16, 2, 48, "QFN28"),
    ChipInfo("CH641D", 16, 2, 48, "QFN20"),
    ChipInfo("CH641X", 16, 2, 48, "QFN20"),
    ChipInfo("CH641P", 16, 2, 48, "QFN16"),
    # CH643
    ChipInfo("CH643W", 62, 20, 48, "QFN80"),
    ChipInfo("CH643Q", 62, 20, 48, "LQFP64"),
    ChipInfo("CH643L", 62, 20, 48, "LQFP48"),
    ChipInfo("CH643U", 62, 20, 48, "QSOP28"),
    # "CH32V00X" actually V002, V004, V005, V006, V007
    ChipInfo("CH32V002J4M6", 16, 4, 48, "SOP8"),
    ChipInfo("CH32V002D4U6", 16, 4, 48, "QFN12"),
    ChipInfo("CH32V002A4M6", 16, 4, 48, "SOP16"),
    ChipInfo("CH32V002F4U6", 16, 4, 48, "QFN20"),
    ChipInfo("CH32V002F4P6", 16, 4, 48, "TSSOP20"),
    # CH32V003
    ChipInfo("CH32V003F4P6", 16, 2, 48, "TSSOP20"),
    ChipInfo("CH32V003F4U6", 16, 2, 48, "QFN20"),
    ChipInfo("CH32V003A4M6", 16, 2, 48, "SOP16"),
    ChipInfo("CH32V003J4M6", 16, 2, 48, "SOP8"),
    # CH32V004
    ChipInfo("CH32V004F6P1", 32, 6, 48, "TSSOP20"),
    ChipInfo("CH32V004F6U1", 32, 6, 48, "QFN20"),
    # CH32V005
    ChipInfo("CH32V005D6U6", 32, 6, 48, "QFN12"),
    ChipInfo("CH32V005F6P6", 32, 6, 48, "TSSOP20"),
    ChipInfo("CH32V005F6U6", 32, 6, 48, "QFN20"),
    ChipInfo("CH32V005E6R6", 32, 6, 48, "QFN20"),
    # CH32V006
    ChipInfo("CH32V006F8P6", 62, 8, 48, "TSSOP20"),
    ChipInfo("CH32V006F8U6", 62, 8, 48, "QFN20"),
    ChipInfo("CH32V006F4P6", 16, 4, 48, "QFN20"),
    ChipInfo("CH32V006E8R6", 62, 8, 48, "QSOP24"),
    ChipInfo("CH32V006K8U6", 62, 8, 48, "QFN32"),
    # CH32V007
    ChipInfo("CH32V007E8R6", 62, 8, 48, "QSOP24"),
    ChipInfo("CH32V007K8U6", 62, 8, 48, "QFN32"),
    # CH32M007
    ChipInfo("CH32M007E8R6", 65, 8, 48, "QSOP24"),
    ChipInfo("CH32M007E8U6", 65, 8, 48, "QFN26C3"),
    ChipInfo("CH32M007G8R6", 65, 8, 48, "QSOP28"),
    # CH32V103
    ChipInfo("CH32V103C6T6", 32, 10, 72, "LQFP48"),
    ChipInfo("CH32V103C8U6", 64, 20, 72, "QFN48"),
    ChipInfo("CH32V103C8T6", 64, 20, 72, "LQFP48"),
    ChipInfo("CH32V103R8T6", 64, 20, 72, "LQFP64M"),
    # CH32V203
    # Note. These seem to actually all have 224K of flash, just the first 32, 64 or 128K being fast 
    ChipInfo("CH32V203F6T6", 32, 10, 144, "TSSOP20"),
    ChipInfo("CH32V203F8P6", 64, 20, 144, "TSSOP20"),
    ChipInfo("CH32V203F8U6", 64, 20, 144, "QFN20X3"),
    ChipInfo("CH32V203G6U6", 32, 10, 144, "QFN28X4"),
    ChipInfo("CH32V203G8R6", 64, 20, 144, "QSOP28"),
    ChipInfo("CH32V203K6T6", 32, 10, 144, "LQFP32"),
    ChipInfo("CH32V203K8T6", 64, 20, 144, "LQFP32"),
    ChipInfo("CH32V203C6T6", 32, 10, 144, "LQFP48"),
    ChipInfo("CH32V203C8T6", 64, 20, 144, "LQFP48"),
    ChipInfo("CH32V203C8U6", 64, 20, 144, "QFN48X7"),
    ChipInfo("CH32V203RBT6", 128, 64, 144, "LQFP64M"),
    # CH32V208
    ChipInfo("CH32V208GBU6", 128, 64, 144, "QFN28X4"),
    ChipInfo("CH32V208CBU6", 128, 64, 144, "QFN48X5"),
    ChipInfo("CH32V208RBT6", 128, 64, 144, "LQFP64M"),
    ChipInfo("CH32V208WBU6", 128, 64, 144, "QFN68X8"),
    # CH32V30x
    ChipInfo("CH32V303CBT6", 128, 32, 144, "LQFP58"),
    ChipInfo("CH32V303RBT6", 128, 32, 144, "LQFP64M"),
    ChipInfo("CH32V303RCT6", 256, 64, 144, "LQFP64M"),
    ChipInfo("CH32V303VCT6", 256, 64, 144, "LQFP100"),
    ChipInfo("CH32V305FBP6", 128, 32, 144, "TSSOP20"),
    ChipInfo("CH32V305GBU6", 128, 32, 144, "QFN28"),
    ChipInfo("CH32V305CCT6", 256, 64, 144, "LQFP48"),
    ChipInfo("CH32V305RBT6", 128, 32, 144, "LQFP64M"),
    ChipInfo("CH32V307RCT6", 256, 64, 144, "LQFP64M"),
    ChipInfo("CH32V307WCU6", 256, 64, 144, "QFN64X8"),
    ChipInfo("CH32V307VCT6", 256, 64, 144, "LQFP100"),
    # CH32V317
    ChipInfo("CH32V317TCU6", 256, 64, 144, "QFN36C4"),
    ChipInfo("CH32V317WCU6", 256, 64, 144, "QFN68"),
    ChipInfo("CH32V317VCT6", 256, 64, 144, "LQFP100"),
    # CH32X035/3
    ChipInfo("CH32X035R8T6", 62, 20, 48, "LQFP64M"),
    ChipInfo("CH32X035C8T6", 62, 20, 48, "LQFP48"),
    ChipInfo("CH32X035G8U6", 62, 20, 48, "QFN28"),
    ChipInfo("CH32X035G8R6", 62, 20, 48, "QSOP28"),
    ChipInfo("CH32X035F8U6", 62, 20, 48, "QFN20"),
    ChipInfo("CH32X035F7P6", 62, 20, 48, "TSSOP20"),
    ChipInfo("CH32X033F8P6", 62, 20, 48, "TSSOP20"),
    # CH32L10x
    ChipInfo("CH32L103F8P6", 64, 20, 96, "TSSOP20"),
    ChipInfo("CH32L103F8U6", 64, 20, 96, "QFN20"),
    ChipInfo("CH32L103G8R6", 64, 20, 96, "QSOP28"),
    ChipInfo("CH32L103K8U6", 64, 20, 96, "QFN32"),
    ChipInfo("CH32L103C8T6", 64, 20, 96, "LQFP48"),
]

def get_chip(name: str) -> Optional[ChipInfo]:
    for c in chip_db:
        if c.name.lower() == name.lower():
            return c
    return None

@dataclass
class KnownBoard:
    file_name: str
    board_name: str
    chip: ChipInfo
    url: str
    vendor: str
    add_info: Optional[Dict[str, Any]] = field(default_factory=dict)
    clock_source: str = "hsi+pll"
    extra_flags: list[str] = field(default_factory=list)

known_boards: List[KnownBoard] = [
    KnownBoard("ch32v003f4p6_evt_r0", "CH32V003F4P6-EVT-R0", get_chip("CH32V003F4P6"),
               "https://www.aliexpress.com/item/1005004895791296.html", "W.CH", {
                       "build.arduino": {
                            "openwch": {
                                "variant": "CH32V00x/CH32V003F4",
                                "variant_h": "variant_CH32V003F4.h"
                            }
                        }
                   }),
    KnownBoard("suzuno32rv", "BitTradeOne Suzuno32RV", get_chip("CH32V203C8T6"),
               "https://www.github.com/verylowfreq/board_suzuno32rv", "BitTradeUno", {
                       "build.arduino": {
                            "openwch": {
                                "variant": "CH32V20x/CH32V203C8",
                                "variant_h": "variant_CH32V203C8.h"
                            }
                        },
                        "upload.protocol": "isp"
                   }, clock_source="hse+pll"),
    KnownBoard("adafruit_qtpy_ch32v203", "Adafruit QT Py CH32V203", get_chip("CH32V203G6U6"),
               "https://www.adafruit.com/product/5996", "Adafruit", {
                       "build.arduino": { 
                            "openwch": { 
                                "variant": "CH32V20x/CH32V203G6_ADAFRUIT_QTPY", 
                                "variant_h": "variant_CH32V203G6_ADAFRUIT_QTPY.h"
                            }
                        },
                        "upload.protocol": "isp",
                        "upload.maximum_size": 224*1024 # actually 224K of flash, only first 32K zero-wait-state
                   }),
    KnownBoard("ch32v203c8t6_evt_r0", "CH32V203C8T6-EVT-R0", get_chip("CH32V203C8T6"),
               "https://www.aliexpress.com/item/1005004895791296.html", "W.CH", clock_source="hse+pll"),
    KnownBoard("ch32v307_evt", "CH32V307 EVT", get_chip("CH32V307VCT6"),
               "https://www.aliexpress.com/item/1005004511264952.html", "SCDZ", clock_source="hse+pll"),
    KnownBoard("ch32x035c8t6_evt_r0", "CH32X035C8T6-EVT-R0", get_chip("CH32X035C8T6"), 
               "https://www.aliexpress.com/item/1005005793197807.html", "W.CH"),
    KnownBoard("ch32x035f8u6_evt_r0", "CH32X035F8U6-EVT-R0", get_chip("CH32X035F8U6"), 
               "https://www.aliexpress.com/item/1005005793197807.html", "W.CH"),
    KnownBoard("ch32x035g8u6_evt_r0", "CH32X035G8U6-EVT-R0", get_chip("CH32X035G8U6"), 
               "https://www.aliexpress.com/item/1005005793197807.html", "W.CH"),
    KnownBoard("usb_pdmon_ch32x035g8u6", "USB PDMon", get_chip("CH32X035G8U6"), 
               "https://github.com/dragonlock2/kicadboards/tree/main/breakouts/usb_pdmon", "Matthew Tran"),
    KnownBoard("ch32l103c8t6_evt_r0", "CH32L103C8T6-EVT-R0", get_chip("CH32L103C8T6"), 
               "https://ja.aliexpress.com/item/1005006671545123.html", "W.CH", clock_source="hse+pll"),
]

# Describe known OpenWCH Arduino variants so that we can auto-add them
@dataclass
class OpenWCHVariant:
    mcu: str
    variant_folder: str
    variant_h: str
    extra_macros: Optional[str] = None
known_openwchcore_variants: List[OpenWCHVariant] = [
    OpenWCHVariant("ch32v003f4", "CH32V00x/CH32V003F4", "variant_CH32V003F4.h"),
    OpenWCHVariant("ch32v103r8t6", "CH32V10x/CH32V103R8T6", "variant_CH32V103R8T6.h", "-DCH32V10x_3V3"),
    OpenWCHVariant("ch32v203c6", "CH32V20x/CH32V203C6", "variant_CH32V203C6.h"),
    OpenWCHVariant("ch32v203c8", "CH32V20x/CH32V203C8", "variant_CH32V203C8.h"),
    OpenWCHVariant("ch32v203g6", "CH32V20x/CH32V203G6", "variant_CH32V203G6.h"),
    OpenWCHVariant("ch32v203g8", "CH32V20x/CH32V203G8", "variant_CH32V203G8.h"),
    OpenWCHVariant("ch32v203rb", "CH32V20x/CH32V203RB", "variant_CH32V203RB.h"),
    OpenWCHVariant("ch32v307vct6", "CH32V30x/CH32V307VCT6", "variant_CH32V307VCT6.h", "-DCH32V30x_C"),
    OpenWCHVariant("ch32x035g8u", "CH32X035/CH32X035G8U", "variant_CH32X035G8U.h"),
    OpenWCHVariant("ch32l103c8t6", "CH32L10x/CH32L103C8T6", "variant_CH32L103C8T6.h")
]

def add_openwch_arduino_info(base_json: dict[str, Any], patch_info: dict[str, Any], info:ChipInfo, board_name: str):
    chip_l = info.name.lower()
    matching_variants = list(filter(lambda candidate: chip_l.startswith(candidate.mcu), known_openwchcore_variants))
    if len(matching_variants) == 0:
        return 
    if len(matching_variants) > 1:
        print("Warning: Multiple matches for chip")
        return
    # only one match now
    matching_variant = matching_variants[0]
    if "arduino" not in base_json["frameworks"]:
        base_json["frameworks"].append("arduino")
    base_json["build"]["core"] = "openwch"
    if "build.arduino" in patch_info and "openwch" in patch_info["build.arduino"]:
        print("Info: Not overriding already set OpenWCH settings")
        return
    else:
        patch_info.update( {
            "build.arduino": { 
                "openwch": { 
                    "variant": matching_variant.variant_folder, 
                    "variant_h": matching_variant.variant_h
                }
            }   
        })
    if matching_variant.extra_macros is not None:
        base_json["build"]["extra_flags"] += matching_variant.extra_macros

def create_board_json(info: ChipInfo, board_name:str, output_path: str, patch_info: Optional[Dict[str, Any]] = None, addtl_extra_flags:List[str] = None, clock_soure: str = "hsi+pll"):
    # simplifies things later
    if patch_info is None:
        patch_info = dict()
    arch, abi = info.get_riscv_arch_and_abi()
    base_json = {
        "build": {
            "f_cpu": str(info.freq_mhz * 1000_000) + "L",
            "extra_flags": "",
            "hwids": [
                [
                    "0x1A86",
                    "0x8010"
                ]
            ],
            "mabi": abi,
            "march": arch,
            "mcu": info.name.lower(),
            "series": info.exact_series().lower(),
            "spl_series": info.spl_series(),
            "clock_source": clock_soure
        },
        "debug": {
            "onboard_tools": [
                "wch-link"
            ],
            "openocd_config": "wch-riscv.cfg",
            "svd_path": info.get_svd_file()
        },
        "frameworks": [
            "noneos-sdk"
        ],
        "name": board_name,
        "upload": {
            "maximum_ram_size": info.sram_kb * 1024,
            "maximum_size": info.flash_kb * 1024,
            "protocols": [
                "wch-link",
                "minichlink",
                "isp",
                "wlink"
            ],
            "protocol": "wch-link"
        },
        "url": f"http://www.wch-ic.com/products/{info.exact_series().upper()}.html",
        "vendor": "W.CH"
    }
    # every series but CH32V003 can do FreeRTOS (if RAM is big enough)
    # same with Harmony LiteOS, RT-Thread and TencentOS
    chip_l = info.name.lower()
    if not chip_l.startswith("ch32v00") and not chip_l.startswith("ch5") and not chip_l.startswith("ch6"):
        base_json["frameworks"].append("freertos")
        base_json["frameworks"].append("harmony-liteos")
        base_json["frameworks"].append("rt-thread")
        base_json["frameworks"].append("tencent-os")
    if chip_l.startswith("ch58"):
        base_json["frameworks"].append("freertos")
        base_json["frameworks"].append("rt-thread")
    if chip_l.startswith("ch585") or chip_l.startswith("ch584"):
        base_json["frameworks"].append("harmony-liteos")
    if chip_l.startswith("ch59"):
        base_json["frameworks"].append("freertos")
        base_json["frameworks"].append("rt-thread")
    if chip_l.startswith("ch32v003"):
        base_json["frameworks"].append("arduino")
        base_json["build"]["core"] = "ch32v003"
        base_json["build"]["variant"] = "CH32V003"
    if chip_l.startswith("ch32v307"):
        base_json["frameworks"].append("arduino")
        base_json["build"]["core"] = "ch32v"
        base_json["build"]["variant"] = "ch32v307_evt"
    if chip_l.startswith("ch32l103"):
        base_json["build"]["variant"] = "ch32l103_evt"
    if board_name == "USB PDMon":
        # experiment
        base_json["frameworks"].append("zephyr")
        base_json["build"]["zephyr"] = {"variant": "usb_pdmon"}
    if chip_l.startswith("ch32v") or chip_l.startswith("ch32x") or chip_l.startswith("ch5"):
        base_json["frameworks"].append("ch32v003fun")
    add_openwch_arduino_info(base_json, patch_info, info, board_name)

    # add some classification macros
    extra_flags = [
        f"-D{info.chip_without_package()}"
    ]
    if chip_l.startswith("ch5") or chip_l.startswith("ch6"):
        extra_flags += [
            f"-D{info.name[0:len('chxx')]}x{info.name[-1]}",
            f"-D{info.name[0:len('ch5')]}xx",
            f"-D{info.name[0:len('ch5x')]}X",
            f"-D{info.name[0:len('ch5x')]}x",
            f"-D{info.name[0:len('ch5xx')]}",
        ]
    else:
        extra_flags += [
            f"-D{info.name[0:len('ch32vxx')]}X",
            f"-D{info.name[0:len('ch32vxx')]}x",
            f"-D{info.name[0:len('ch32vxxx')]}",
        ]
        if (chip_l.startswith("ch32v00") and not chip_l.startswith("ch32v003")) or chip_l.startswith("ch32m007"):
            extra_flags += [
                f"-DCH32V00Xx",
            ]
    classification_macro = info.get_classification_macro()
    if classification_macro is not None:
        extra_flags += ["-D" + classification_macro]
    if addtl_extra_flags is not None:
        extra_flags.extend(addtl_extra_flags)
    # account for previous extra flags modifications
    if "extra_flags" in base_json["build"] and len(base_json["build"]["extra_flags"]) > 0:
        extra_flags.insert(0, base_json["build"]["extra_flags"])
    base_json["build"]["extra_flags"] = " ".join(extra_flags)
    if patch_info is not None and len(patch_info.keys()) > 0:
        for k, v in patch_info.items():
            # upmost level
            if k.count(".") == 0:
                base_json[k] = v
            # one deeper (e.g. build.extra_flags)
            if k.count(".") == 1:
                k1, k2 = k.split(".")
                base_json[k1][k2] = v
    as_str = json.dumps(base_json, indent=2, sort_keys=True)
    print("DEFINITION FOR %s:\n%s" % (board_name, as_str))
    try:
        Path(output_path).write_text(as_str, encoding='utf-8')
    except Exception as exc:
        print("Error writing board definition: %s" % repr(exc))


def main():
    # generate board JSON for all known chips directly into boards folder
    base_path = Path(__file__).parents[2].resolve() / "boards"
    # all generic chips first
    for info in chip_db:
        output_path = base_path / f"generic{info.name.upper()}.json"
        name = f"Generic {info.name.upper()}"
        create_board_json(info, name, output_path)
        #return
    # all known boards now
    for known_board in known_boards:
        output_path = base_path / f"{known_board.file_name}.json"
        patch_dict = {"url": known_board.url, "vendor": known_board.vendor}
        patch_dict.update(known_board.add_info)
        create_board_json(known_board.chip, known_board.board_name, output_path, patch_dict, addtl_extra_flags=known_board.extra_flags, clock_soure=known_board.clock_source)
    pass


if __name__ == '__main__':
    main()
