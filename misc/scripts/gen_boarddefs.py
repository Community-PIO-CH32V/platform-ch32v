#!/usr/bin/env python3
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import json

@dataclass
class WCHChipSeries:
    name: str # e.g. QingKe V4B
    arch: str # e.g. rv32imacxw
    abi: str # e.g. ilp32
    svd_file: str # e.g. CH32V20xxx.svd
    spl_series: str
    supported_frameworks: List[str] # assumed support for **every** chip in the series.

# frameworks (nonos-sdk always assumed supported)
ALL_ADDITIONAL_FRAMEWORKS = ["freertos", "harmony-liteos", "rt-thread", "tencent-os", "ch32v003fun"]
# known chip seriess
CH32V003 = WCHChipSeries("QingKe V2A", "rv32ecxw", "ilp32e", "CH32V003xx.svd", "ch32v00x", ["ch32v003fun"])
CH32V00X_M007 = WCHChipSeries("QingKe V2A-M0", "rv32ec_zmmul_xw", "ilp32e", "CH32V00Xxx.svd", "ch32v00Xx", ["ch32v003fun"])
CH32V103 = WCHChipSeries("QingKe V3A", "rv32imac", "ilp32", "CH32V103xx.svd", "ch32v10x", ALL_ADDITIONAL_FRAMEWORKS[:])
CH32V203 = WCHChipSeries("QingKe V4B", "rv32imacxw", "ilp32", "CH32V203xx.svd", "ch32v20x", ALL_ADDITIONAL_FRAMEWORKS[:])
# TODO CH32V205 series missing 
CH32V208 = WCHChipSeries("QingKe V4C", "rv32imacxw", "ilp32", "CH32V208xx.svd", "ch32v20x", ALL_ADDITIONAL_FRAMEWORKS[:])
CH32V303 = WCHChipSeries("QingKe V4C", "rv32imacxw", "ilp32", "CH32V303xx.svd", "ch32v30x", ALL_ADDITIONAL_FRAMEWORKS[:])
CH32V305 = WCHChipSeries("QingKe V4C", "rv32imacxw", "ilp32", "CH32V305xx.svd", "ch32v30x", ALL_ADDITIONAL_FRAMEWORKS[:])
CH32V307 = WCHChipSeries("QingKe V4C", "rv32imacxw", "ilp32", "CH32V307xx.svd", "ch32v30x", ALL_ADDITIONAL_FRAMEWORKS[:])
CH32V317 = WCHChipSeries("QingKe V4C", "rv32imacxw", "ilp32", "CH32V317xx.svd", "ch32v30x", ALL_ADDITIONAL_FRAMEWORKS[:])
CH32X035 = WCHChipSeries("QingKe V4B", "rv32imacxw", "ilp32", "CH32X035xx.svd", "ch32x035", ALL_ADDITIONAL_FRAMEWORKS[:])
CH32L103 = WCHChipSeries("QingKe V4B", "rv32imacxw", "ilp32", "CH32L103xx.svd", "ch32l10x", ALL_ADDITIONAL_FRAMEWORKS[:])
CH32H417 = WCHChipSeries("QingKe V3F + V5F", "rv32imac_zba_zbb_zbc_zbs_xw", "ilp32", "CH32H417xx.svd", "ch32h417", ["ch32v003fun"])
# actually CH565, CH569
CH56X = WCHChipSeries("CH56x Series", "rv32imac", "ilp32", "CH56Xxx.svd", "ch56x", ["ch32v003fun"])
# no actual board definition for this yet
CH564 = WCHChipSeries("CH564", "rv32imc_zba_zbb_zbc_zbs_xw", "ilp32", "CH564.svd", "ch564", [])
# actually CH571/CH573
CH57X = WCHChipSeries("CH57x Series", "rv32imac", "ilp32", "CH57Xxx.svd", "ch57x", ["ch32v003fun"])
CH570_CH572 = WCHChipSeries("CH570/CH572 Series", "rv32imc_zba_zbb_zbc_zbs_xw", "ilp32", "CH572.svd", "ch572", ["ch32v003fun"])
# actually CH582
CH58X = WCHChipSeries("CH58x Series", "rv32imac", "ilp32", "CH58Xxx.svd", "ch58x", ["freertos", "rt-thread", "ch32v003fun"])
# CH581M is seperate from this mess too, ughh 
CH585_CH584 = WCHChipSeries("CH585 Series", "rv32imc_zba_zbb_zbc_zbs_xw", "ilp32", "CH585.svd", "ch585", ["freertos", "rt-thread", "harmony-liteos", "ch32v003fun"])
# actually CH591/CH592
CH59X = WCHChipSeries("CH59x Series", "rv32imac", "ilp32", "CH59Xxx.svd", "ch59x", ["freertos", "rt-thread", "ch32v003fun"])
CH641 = WCHChipSeries("CH641 Series", "rv32ec_zmmul_xw", "ilp32e", "CH641.svd", "ch641", [])
CH643 = WCHChipSeries("CH643 Series", "rv32imacxw", "ilp32", "CH643.svd", "ch643", [])

@dataclass
class ChipInfo:
    name: str
    flash_kb: int
    sram_kb: int
    freq_mhz: int
    package: str
    chip_type: WCHChipSeries

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
        # others don't have any
        return None

    def get_riscv_arch_and_abi(self) -> Tuple[str, str]:
        return self.chip_type.arch, self.chip_type.abi

    def chip_without_package(self) -> str:
        return self.name[:-2]

    def spl_series(self) -> str:
        return self.chip_type.spl_series

    def exact_series(self) -> str:
        # TODO. only noneos_sdk uses this for getting the linker script and startup file, as well as the codegen code.
        # maybe we can rationalize this away.
        if self.name.lower().startswith("ch585") or self.name.lower().startswith("ch584"):
            return "ch585"
        if self.name.lower().startswith("ch570") or self.name.lower().startswith("ch572"):
            return "ch572"
        # ch57x, ch58x, ch59x
        if self.name.lower().startswith("ch5"):
            return self.name[0:len("ch58")].upper() + "X"
        # Hack: Even ch32x033 is recognized as x035 series.
        # This simplifies folder handling for frameworks like
        # FreeRTOS.
        if self.name.lower().startswith("ch32x03"):
            return "ch32x035"
        # Hack: A ch32v317 uses the same SDK as the ch32v307.
        if self.name.lower().startswith("ch32v317"):
            return "ch32v307"
        return self.name[0:len("ch32vxxx")]
    
    def get_svd_file(self) -> str:
        return self.chip_type.svd_file

chip_db: List[ChipInfo] = [
    # CH56x (configurable SRAM size, data flash)
    ChipInfo("CH569W", 448+32, 16+32, 120, "QFN68", CH56X),
    ChipInfo("CH565W", 448+32, 16+32, 120, "QFN68", CH56X),
    ChipInfo("CH565M", 448+32, 16+32, 120, "QFN40", CH56X),
    # CH57x
    ChipInfo("CH573X", 448+32, 16+2, 20, "QFN32", CH57X),
    ChipInfo("CH573F", 448+32, 16+2, 20, "QFN28", CH57X),
    ChipInfo("CH573Q", 192+32, 16+2, 20, "LQFP32", CH57X),
    ChipInfo("CH571F", 192+32, 16+2, 20, "QFN28", CH57X),
    ChipInfo("CH571D", 192+32, 16+2, 20, "QFN20", CH57X),
    ChipInfo("CH571K", 192+32, 16+2, 20, "ESSOP10", CH57X),
    ChipInfo("CH572D", 240+8, 12, 100, "QFN20", CH570_CH572),
    ChipInfo("CH572Q", 240+8, 12, 100, "DFN10X3", CH570_CH572),
    ChipInfo("CH572R", 240+8, 12, 100, "TSSOP16", CH570_CH572),
    ChipInfo("CH570D", 240+8, 12, 100, "QFN20", CH570_CH572),
    ChipInfo("CH570Q", 240+8, 12, 100, "DFN10X3", CH570_CH572),
    ChipInfo("CH570E", 240+8, 12, 100, "SOP8", CH570_CH572),
    # CH58x (has +32K data flash)
    ChipInfo("CH583M", 448+32, 32, 20, "QFN48", CH58X),
    ChipInfo("CH582M", 448+32, 32, 20, "QFN48", CH58X),
    ChipInfo("CH582F", 448+32, 32, 20, "QFN28", CH58X),
    ChipInfo("CH581F", 192+32, 32, 20, "QFN28", CH58X),
    # CH585 and CH584 (32K data flash, 24K bootloader, 448k codeflash)
    ChipInfo("CH585M", 448+32, 128, 78, "QFN48", CH585_CH584),
    ChipInfo("CH585F", 448+32, 128, 78, "QFN32", CH585_CH584),
    ChipInfo("CH585C", 448+32, 128, 78, "QFN26C3", CH585_CH584),
    ChipInfo("CH585D", 448+32, 128, 78, "QFN20", CH585_CH584),
    ChipInfo("CH584M", 448+32, 128, 78, "QFN48", CH585_CH584),
    ChipInfo("CH584F", 448+32, 128, 78, "QFN32", CH585_CH584),

    # CH59x (has +32K data flash, +24K bootloader)
    ChipInfo("CH592X", 448+24+32, 24+2, 60, "QFN32", CH59X),
    ChipInfo("CH592F", 448+24+32, 24+2, 60, "QFN28", CH59X),
    ChipInfo("CH591F", 192+24+32, 24+2, 60, "QFN28", CH59X),
    ChipInfo("CH591D", 192+24+32, 24+2, 60, "QFN20", CH59X),
    ChipInfo("CH591R", 192+24+32, 24+2, 60, "TSSOP16", CH59X),
    # CH641
    ChipInfo("CH641F", 16, 2, 48, "QFN28", CH641),
    ChipInfo("CH641D", 16, 2, 48, "QFN20", CH641),
    ChipInfo("CH641X", 16, 2, 48, "QFN20", CH641),
    ChipInfo("CH641P", 16, 2, 48, "QFN16", CH641),
    # CH643
    ChipInfo("CH643W", 62, 20, 48, "QFN80", CH643),
    ChipInfo("CH643Q", 62, 20, 48, "LQFP64", CH643),
    ChipInfo("CH643L", 62, 20, 48, "LQFP48", CH643),
    ChipInfo("CH643U", 62, 20, 48, "QSOP28", CH643),
    # "CH32V00X" actually V002, V004, V005, V006, V007
    ChipInfo("CH32V002J4M6", 16, 4, 48, "SOP8", CH32V00X_M007),
    ChipInfo("CH32V002D4U6", 16, 4, 48, "QFN12", CH32V00X_M007),
    ChipInfo("CH32V002A4M6", 16, 4, 48, "SOP16", CH32V00X_M007),
    ChipInfo("CH32V002F4U6", 16, 4, 48, "QFN20", CH32V00X_M007),
    ChipInfo("CH32V002F4P6", 16, 4, 48, "TSSOP20", CH32V00X_M007),
    # CH32V003
    ChipInfo("CH32V003F4P6", 16, 2, 48, "TSSOP20", CH32V003),
    ChipInfo("CH32V003F4U6", 16, 2, 48, "QFN20", CH32V003),
    ChipInfo("CH32V003A4M6", 16, 2, 48, "SOP16", CH32V003),
    ChipInfo("CH32V003J4M6", 16, 2, 48, "SOP8", CH32V003),
    # CH32V004
    ChipInfo("CH32V004F6P1", 32, 6, 48, "TSSOP20", CH32V00X_M007),
    ChipInfo("CH32V004F6U1", 32, 6, 48, "QFN20", CH32V00X_M007),
    # CH32V005
    ChipInfo("CH32V005D6U6", 32, 6, 48, "QFN12", CH32V00X_M007),
    ChipInfo("CH32V005F6P6", 32, 6, 48, "TSSOP20", CH32V00X_M007),
    ChipInfo("CH32V005F6U6", 32, 6, 48, "QFN20", CH32V00X_M007),
    ChipInfo("CH32V005E6R6", 32, 6, 48, "QFN20", CH32V00X_M007),
    # CH32V006
    ChipInfo("CH32V006F8P6", 62, 8, 48, "TSSOP20", CH32V00X_M007),
    ChipInfo("CH32V006F8U6", 62, 8, 48, "QFN20", CH32V00X_M007),
    ChipInfo("CH32V006F4P6", 16, 4, 48, "QFN20", CH32V00X_M007),
    ChipInfo("CH32V006E8R6", 62, 8, 48, "QSOP24", CH32V00X_M007),
    ChipInfo("CH32V006K8U6", 62, 8, 48, "QFN32", CH32V00X_M007),
    # CH32V007
    ChipInfo("CH32V007E8R6", 62, 8, 48, "QSOP24", CH32V00X_M007),
    ChipInfo("CH32V007K8U6", 62, 8, 48, "QFN32", CH32V00X_M007),
    # CH32M007
    ChipInfo("CH32M007E8R6", 65, 8, 48, "QSOP24", CH32V00X_M007),
    ChipInfo("CH32M007E8U6", 65, 8, 48, "QFN26C3", CH32V00X_M007),
    ChipInfo("CH32M007G8R6", 65, 8, 48, "QSOP28", CH32V00X_M007),
    # CH32V103
    ChipInfo("CH32V103C6T6", 32, 10, 72, "LQFP48", CH32V103),
    ChipInfo("CH32V103C8U6", 64, 20, 72, "QFN48", CH32V103),
    ChipInfo("CH32V103C8T6", 64, 20, 72, "LQFP48", CH32V103),
    ChipInfo("CH32V103R8T6", 64, 20, 72, "LQFP64M", CH32V103),
    # CH32V203
    # Note. These seem to actually all have 224K of flash, just the first 32, 64 or 128K being fast 
    ChipInfo("CH32V203F6T6", 32, 10, 144, "TSSOP20", CH32V203),
    ChipInfo("CH32V203F8P6", 64, 20, 144, "TSSOP20", CH32V203),
    ChipInfo("CH32V203F8U6", 64, 20, 144, "QFN20X3", CH32V203),
    ChipInfo("CH32V203G6U6", 32, 10, 144, "QFN28X4", CH32V203),
    ChipInfo("CH32V203G8R6", 64, 20, 144, "QSOP28", CH32V203),
    ChipInfo("CH32V203K6T6", 32, 10, 144, "LQFP32", CH32V203),
    ChipInfo("CH32V203K8T6", 64, 20, 144, "LQFP32", CH32V203),
    ChipInfo("CH32V203C6T6", 32, 10, 144, "LQFP48", CH32V203),
    ChipInfo("CH32V203C8T6", 64, 20, 144, "LQFP48", CH32V203),
    ChipInfo("CH32V203C8U6", 64, 20, 144, "QFN48X7", CH32V203),
    ChipInfo("CH32V203RBT6", 128, 64, 144, "LQFP64M", CH32V203),
    # CH32V208
    ChipInfo("CH32V208GBU6", 128, 64, 144, "QFN28X4", CH32V208),
    ChipInfo("CH32V208CBU6", 128, 64, 144, "QFN48X5", CH32V208),
    ChipInfo("CH32V208RBT6", 128, 64, 144, "LQFP64M", CH32V208),
    ChipInfo("CH32V208WBU6", 128, 64, 144, "QFN68X8", CH32V208),
    # CH32V30x
    ChipInfo("CH32V303CBT6", 128, 32, 144, "LQFP58", CH32V303),
    ChipInfo("CH32V303RBT6", 128, 32, 144, "LQFP64M", CH32V303),
    ChipInfo("CH32V303RCT6", 256, 64, 144, "LQFP64M", CH32V303),
    ChipInfo("CH32V303VCT6", 256, 64, 144, "LQFP100", CH32V303),
    ChipInfo("CH32V305FBP6", 128, 32, 144, "TSSOP20", CH32V305),
    ChipInfo("CH32V305GBU6", 128, 32, 144, "QFN28", CH32V305),
    ChipInfo("CH32V305CCT6", 256, 64, 144, "LQFP48", CH32V305),
    ChipInfo("CH32V305RBT6", 128, 32, 144, "LQFP64M", CH32V305),
    ChipInfo("CH32V307RCT6", 256, 64, 144, "LQFP64M", CH32V307),
    ChipInfo("CH32V307WCU6", 256, 64, 144, "QFN64X8", CH32V307),
    ChipInfo("CH32V307VCT6", 256, 64, 144, "LQFP100", CH32V307),
    # CH32V317
    ChipInfo("CH32V317TCU6", 256, 64, 144, "QFN36C4", CH32V317),
    ChipInfo("CH32V317WCU6", 256, 64, 144, "QFN68", CH32V317),
    ChipInfo("CH32V317VCT6", 256, 64, 144, "LQFP100", CH32V317),
    # CH32X035/3
    ChipInfo("CH32X035R8T6", 62, 20, 48, "LQFP64M", CH32X035),
    ChipInfo("CH32X035C8T6", 62, 20, 48, "LQFP48", CH32X035),
    ChipInfo("CH32X035G8U6", 62, 20, 48, "QFN28", CH32X035),
    ChipInfo("CH32X035G8R6", 62, 20, 48, "QSOP28", CH32X035),
    ChipInfo("CH32X035F8U6", 62, 20, 48, "QFN20", CH32X035),
    ChipInfo("CH32X035F7P6", 62, 20, 48, "TSSOP20", CH32X035),
    ChipInfo("CH32X033F8P6", 62, 20, 48, "TSSOP20", CH32X035),
    # CH32L10x
    ChipInfo("CH32L103F8P6", 64, 20, 96, "TSSOP20", CH32L103),
    ChipInfo("CH32L103F8U6", 64, 20, 96, "QFN20", CH32L103),
    ChipInfo("CH32L103G8R6", 64, 20, 96, "QSOP28", CH32L103),
    ChipInfo("CH32L103K8U6", 64, 20, 96, "QFN32", CH32L103),
    ChipInfo("CH32L103C8T6", 64, 20, 96, "LQFP48", CH32L103),
    # CH32H417 (960K nonzero-wait-state flash), 960 SRAM, 400 MHz V5F, 150 MHz on V3F  
    ChipInfo("CH32H417QEU6", 960, 128, 400, "QFN128", CH32H417),
    ChipInfo("CH32H417MEU6", 960, 128, 400, "QFN88", CH32H417),
    ChipInfo("CH32H417WEU6", 960, 128, 400, "QFN68", CH32H417),
    ChipInfo("CH32H417REU6", 960, 128, 400, "QFN60X6", CH32H417),
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
    KnownBoard("UIAPduino_Pro_Micro_CH32V003_v1dot4", "UIAPduino Pro Micro CH32V003 v1.4", get_chip("CH32V003F4P6"),
            "https://www.uiap.jp/uiapduino/pro-micro/ch32v003/v1dot4", "UIAP, Umeta & Ikki Automotive Parts", {
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
    KNOWN_DUALCORE_NAMES = ["ch32h41"]
    is_dual_core = any([info.name.lower().startswith(known_name) for known_name in KNOWN_DUALCORE_NAMES])
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
            "openocd_config": "wch-dual-core.cfg" if is_dual_core else "wch-riscv.cfg",
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
    # add in supported frameworks
    for frameworks in info.chip_type.supported_frameworks:
        if frameworks not in base_json["frameworks"]:
            base_json["frameworks"].append(frameworks)
    # special case some framework support and overrides
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
        if info.chip_type == CH32V00X_M007:
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
        # for H41x boards we have to do something special: generate 1 definition per core.
        # that is, one _V3F (master) and one _V5F (slave) config.
        # additionally, a macro has to be set (Core_V3F or Core_V5F) for the noneos-sdk code (and all frameworks.)
        # and indicate via board_build.cpu_core which core is being targeted. (v3f or v5f)
        is_h41x = info.name.lower().startswith("ch32h41")
        if is_h41x:
            # V3F version
            output_path_v3f = base_path / f"generic{info.name.upper()}_V3F.json"
            # patch in cpu_core info
            patch_dict = {"build.cpu_core": "v3f"}
            name_v3f = f"Generic {info.name.upper()} (V3F Master)"
            create_board_json(info, name_v3f, output_path_v3f, patch_dict, addtl_extra_flags=["-DCore_V3F"])
            # V5F version
            output_path_v5f = base_path / f"generic{info.name.upper()}_V5F.json"
            patch_dict = {"build.cpu_core": "v5f"}
            name_v5f = f"Generic {info.name.upper()} (V5F Slave)"
            create_board_json(info, name_v5f, output_path_v5f, patch_dict, addtl_extra_flags=["-DCore_V5F"])
            # on top of that, for projects using a single ELF for both the V3F and V5F, provide the generic board def
            create_board_json(info, name, output_path)
        else:
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
