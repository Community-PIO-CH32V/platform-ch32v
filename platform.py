# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
from platformio.public import PlatformBase
from platformio import util

IS_WINDOWS = sys.platform.startswith("win")

class Ch32vPlatform(PlatformBase):
    # ToDo: There's not toolchain for Linux ARM yet.
    riscv_toolchain = {
        # Windows
        "windows_amd64": "https://github.com/Community-PIO-CH32V/toolchain-riscv-windows.git",
        "windows_x86": "https://github.com/Community-PIO-CH32V/toolchain-riscv-windows.git",
        # No Windows ARM64 or ARM32 builds.
        # Linux
        "linux_x86_64": "https://github.com/Community-PIO-CH32V/toolchain-riscv-linux.git",
        #"linux_i686": "",
        #"linux_aarch64": "",
        #"linux_armv7l": "",
        #"linux_armv6l": "",
        # Mac (Intel and ARM are separate)
        "darwin_x86_64": "https://github.com/Community-PIO-CH32V/toolchain-riscv-mac.git",
        "darwin_arm64": "https://github.com/Community-PIO-CH32V/toolchain-riscv-mac.git"
    }
    minichlink_tool = {
        # Windows
        "windows_amd64": "https://github.com/Community-PIO-CH32V/tool-minichlink.git#windows",
        "windows_x86": "https://github.com/Community-PIO-CH32V/tool-minichlink.git#windows",
        # No Windows ARM64 or ARM32 builds.
        # Linux
        "linux_x86_64": "https://github.com/Community-PIO-CH32V/tool-minichlink.git#linux",
        #"linux_i686": "",
        #"linux_aarch64": "",
        #"linux_armv7l": "",
        #"linux_armv6l": "",
        # Mac (Intel and ARM are separate)
        "darwin_x86_64": "https://github.com/Community-PIO-CH32V/tool-minichlink.git#mac",
        "darwin_arm64": "https://github.com/Community-PIO-CH32V/tool-minichlink.git#mac_arm64"
    }
    # PINNED TO A TAG, NOT A BRANCH -- and the version in the tag name is the
    # reason. PlatformIO installs a VCS package once and keys it by this exact
    # string, so a branch name never changes and an existing installation
    # keeps whatever binary it cloned. Everyone who had this platform before
    # would have stayed on wlink 0.1.1, which reports "Probe is not attached to
    # an MCU" on the CH32H41x and cannot program it at all. Changing the string
    # is what makes the next build fetch the new tool.
    #
    # A tag rather than a commit id: PlatformIO shallow-clones a branch or tag
    # (--depth 1 --branch <tag>) but does a FULL clone for a commit id, and
    # this repo's master branch carries every package tarball ever built --
    # about 15 MB of history to download for a 1 MB tool.
    #
    # Updating: push the new binaries to the OS branches, tag each one
    # 0.<minor>.<datecode>-<branch>, and bump the four lines below.
    wlink_tool = {
        # Windows. Both systypes get the x86 build: the x64 build of 0.1.2
        # fails with a driver error on Windows, and x86 works against the WCH
        # drivers as well.
        "windows_amd64": "https://github.com/Community-PIO-CH32V/tool-wlink.git#0.23.260911-windows",
        "windows_x86": "https://github.com/Community-PIO-CH32V/tool-wlink.git#0.23.260911-windows",
        # No Windows ARM64 or ARM32 builds.
        # Linux
        "linux_x86_64": "https://github.com/Community-PIO-CH32V/tool-wlink.git#0.23.260911-linux",
        #"linux_i686": "",
        #"linux_aarch64": "",
        #"linux_armv7l": "",
        #"linux_armv6l": "",
        # Mac (Intel and ARM are separate)
        "darwin_x86_64": "https://github.com/Community-PIO-CH32V/tool-wlink.git#0.23.260911-mac_x64",
        "darwin_arm64": "https://github.com/Community-PIO-CH32V/tool-wlink.git#0.23.260911-mac_arm64"
    }

    def get_boards(self, id_=None):
        result = super().get_boards(id_)
        if not result:
            return result
        if id_:
            return self._add_default_debug_tools(result)
        else:
            for key in result:
                result[key] = self._add_default_debug_tools(result[key])
        return result

    def configure_default_packages(self, variables, targets):
        sys_type = util.get_systype()
        # until toolchain is not yet approved in PIO registry: redirect packages at will here
        # (temporary)
        frameworks = variables.get("pioframework", [])
        gcc_branch = "#gcc12"
        # TODO make this user selectible
        # some users may have build errors with GCC12.
        FORCE_DOWNGRADE_TO_GCC8 = False
        # Temporary fix for "No GCC12 toolchain for MacOS x86_64". Email pending.
        if FORCE_DOWNGRADE_TO_GCC8 or sys_type == "darwin_x86_64":
            gcc_branch = ""
        self.packages["toolchain-riscv"]["version"] = Ch32vPlatform.riscv_toolchain[sys_type] + gcc_branch
        if not variables.get("board"):
            return super().configure_default_packages(variables, targets)
        # The FreeRTOS, Harmony LiteOS and RT-Thread package needs the 
        # NoneSDK as a base package
        if any([framework in frameworks for framework in ("freertos", "harmony-liteos", "rt-thread", "tencent-os")]):
            self.packages["framework-wch-noneos-sdk"]["optional"] = False
        # upload via USB bootloader wanted? (called "isp" in our platform)
        # then activate package
        board = variables.get("board")
        board_config = self.board_config(board)
        default_protocol = board_config.get("upload.protocol") or ""
        if variables.get("upload_protocol", default_protocol) == "isp":
            self.packages["tool-wchisp"]["optional"] = False
        if variables.get("upload_protocol", default_protocol) == "minichlink" or  "ch32v003fun" in frameworks or len(frameworks) == 0:
            self.packages["tool-minichlink"]["optional"] = False
            self.packages["tool-minichlink"]["version"] = Ch32vPlatform.minichlink_tool[sys_type]
        #elif variables.get("upload_protocol", default_protocol) == "wlink":
        # Always update the link to the tool-wlink tool, because for all uploads we want to have the "Enable SDI Print" available
        self.packages["tool-wlink"]["optional"] = False
        self.packages["tool-wlink"]["version"] = Ch32vPlatform.wlink_tool[sys_type]
        # mklittlefs, only when a filesystem image is actually being built.
        # Leaving it optional otherwise means the great majority of builds,
        # which have no data/ directory, never download it.
        #
        # uploadfs is listed as well as buildfs because it depends on the
        # image, so it needs the tool that makes one.
        if any(t in targets for t in ("buildfs", "uploadfs")):
            self.packages["tool-mklittlefs-rp2040-earlephilhower"]["optional"] = False
        build_core = variables.get("board_build.core", board_config.get("build.core", "arduino"))
        if "arduino" in frameworks:
            if build_core == "ch32v003":
                self.frameworks["arduino"]["package"] = "framework-arduinoch32v003"
            elif build_core == "ch32v":
                self.frameworks["arduino"]["package"] = "framework-arduinoch32v"
            elif build_core == "openwch":
               self.frameworks["arduino"]["package"] = "framework-arduino-openwch-ch32"
            elif build_core == "ch32h4":
                # The CH32H4 core. Without this case the board fell through to
                # the framework's default package, the CH32V003 core, and the
                # builder then found no framework-arduinoch32h4 to build.
                self.frameworks["arduino"]["package"] = "framework-arduinoch32h4"
        if "zephyr" in frameworks:
            for p in self.packages:
                if p in ("tool-cmake", "tool-dtc", "tool-ninja"):
                    self.packages[p]["optional"] = False
            if not IS_WINDOWS:
                self.packages["tool-gperf"]["optional"] = False
        return super().configure_default_packages(variables, targets)

    def _add_default_debug_tools(self, board):
        debug = board.manifest.get("debug", {})
        if "tools" not in debug:
            debug["tools"] = {}

        tools = (
            "wch-link",
            "minichlink",
        )
        openocd_reset_cmds = [
            "define pio_reset_halt_target",
            "   monitor reset halt",
            "end",
            "define pio_reset_run_target",
            "   monitor reset",
            "end",
        ]
        minichlink_reset_cmds = [
            "define pio_reset_halt_target",
            "end",
            "define pio_reset_run_target",
            "end",
        ]
        init_cmds = [
            "set mem inaccessible-by-default off",
            "set arch riscv:rv32",
            # compatible with only WCH's gdb version, decodes code generated with "xw" correctly
            "set disassembler-options xw",
            "set remotetimeout unlimited",
            "set breakpoint always-inserted on",
            "target extended-remote $DEBUG_PORT",
            "$INIT_BREAK",
            "$LOAD_CMDS",
        ]
        for tool in tools:
            if tool in debug["tools"]:
                continue
            if tool == "wch-link":
                server_args = [
                    "-s",
                    os.path.join(
                        self.get_package_dir("tool-openocd-riscv-wch") or "",
                        "bin"
                    ),
                    "-s",
                    os.path.join(
                        self.get_package_dir("tool-openocd-riscv-wch") or "",
                        "scripts"
                    )
                ]
                if debug.get("openocd_config", ""):
                    server_args.extend(["-f", debug.get("openocd_config")])
                else:
                    assert debug.get("openocd_target"), (
                        "Missing target configuration for %s" % board.id
                    )
                    # All tools are FTDI based
                    server_args.extend(
                        [
                            "-f",
                            "interface/ftdi/%s.cfg" % tool,
                            "-f",
                            "target/%s.cfg" % debug.get("openocd_target"),
                        ]
                    )
                # Ugly countermeasure. Usually this is "gdb_port pipe" but GCC12 has a bug
                # that prevents it from starting OpenOCD in pipe mode. Hence, we have to revert
                # to reserving a port number for the GDB communication. But we can still disable
                # all other ports.
                # GCC8 would not need this.
                server_args.extend([
                    "-c", "gdb_port 3333; tcl_port disabled; telnet_port disabled"
                ])
                debug_port = "localhost:3333"
                # for h41x dual core chips: enable " -c page_erase". We can see that based on the openocd_config ("wch-dual-core.cfg")
                if debug.get("openocd_config", "").find("wch-dual-core.cfg") != -1:
                    server_args.extend([
                        "-c", "page_erase"
                    ])
                    # check if we are v3f (core0) or v5f (core1)
                    # for debugging core 1 we have to connect to localhost:3334 instead of :3333
                    if board.manifest.get("build", {}).get("cpu_core", "v3f") == "v5f":
                        debug_port = "localhost:3334"
                debug["tools"][tool] = {
                    "init_cmds": openocd_reset_cmds + init_cmds,
                    "server": {
                        "package": "tool-openocd-riscv-wch",
                        "executable": "bin/openocd",
                        "arguments": server_args,
                    },
                    # reference opened port
                    "port": debug_port
                }
            elif tool == "minichlink":
                debug["tools"][tool] = {
                    "server": {
                        "package": "tool-minichlink",
                        "executable": "minichlink",
                        "arguments": [
                            "-b", # Reboot out of Halt
                            "-a", # Reboot into Halt
                            "-G"  # "Terminal + GDB"
                        ]
                    },
                    # The minichlink GDB server does not support the "load" command
                    # So, we have to tell PIO to preflash the binary using the regular upload command
                    "load_cmds": "preload",
                    "init_cmds": minichlink_reset_cmds + init_cmds,
                    "port": "localhost:3333", # default port of that tool
                    "read_pattern": "GDBServer Running",
                }
            debug["tools"][tool]["onboard"] = tool in debug.get("onboard_tools", [])
            debug["tools"][tool]["default"] = tool in debug.get("default_tools", [])
        board.manifest["debug"] = debug
        return board

    def configure_debug_session(self, debug_config):
        if debug_config.speed:
            if "openocd" in (debug_config.server or {}).get("executable", ""):
                debug_config.server["arguments"].extend(
                    ["-c", "adapter speed %s" % debug_config.speed]
                )

    def generate_sample_code(self, config, environment):
        # Generate sample code for the environment and framework
        frameworks = config.get(f"env:{environment}", "framework", None)
        if frameworks is None or len(frameworks) != 1 or (len(frameworks) == 1 and frameworks[0] == "arduino"):
            raise NotImplementedError()
        
        framework = frameworks[0]
        board = config.get("env:%s" % environment, "board")
        board_config = self.board_config(board)
        mcu = str(board_config.get("build.mcu", "")).lower()
        series = str(board_config.get("build.series", "")).lower()
        src_dir = config.get("platformio", "src_dir")
        
        # Generate code using the dedicated generator
        generator = self.SampleCodeGenerator()
        files = generator.generate_for_framework(framework, mcu, series)
        
        # Write generated files
        return generator.write_files(src_dir, files)
    
    # Nested code generation classes
    class ChipSeriesInfo:
        # Detects and stores chip series characteristics
        
        def __init__(self, mcu: str, series: str = ""):
            self.mcu = mcu.lower()
            self.series = series.lower()
            self.is_l10x = self.mcu.startswith("ch32l1")
            self.is_v00xx = self.mcu.startswith("ch32m0") or (
                self.mcu.startswith("ch32v00") and not self.mcu.startswith("ch32v003")
            )
            self.is_v4x7 = self.mcu.startswith("ch32v407") or self.mcu.startswith("ch32v467")
            self.is_ch6x = self.mcu.startswith("ch6")
            self.is_ch5x = self.mcu.startswith("ch5")
            self.is_ch56x = self.series == "ch56x"
            self.is_ch570_ch572 = self.series == "ch572"
            self.is_ch571_ch573 = self.series == "ch57x"
            self.is_ch585_ch584 = self.series == "ch585"
    
    class NoneOSCodeGenerator:
        # Generates NoneOS SDK sample code
        
        @staticmethod
        def get_gpio_config(chip_info) -> dict:
            # Returns GPIO config for the chip series
            if chip_info.is_ch6x:
                return {
                    "port": "GPIOA",
                    "pin": "GPIO_Pin_0",
                    "clock_enable": "RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE)",
                    "speed": "GPIO_Speed_50MHz"
                }
            else:
                return {
                    "port": "GPIOC",
                    "pin": "GPIO_Pin_1",
                    "clock_enable": (
                        "RCC_PB2PeriphClockCmd(RCC_PB2Periph_GPIOC, ENABLE)"
                        if chip_info.is_l10x or chip_info.is_v00xx or chip_info.is_v4x7
                        else "RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE)"
                    ),
                    "speed": (
                        "GPIO_Speed_High" if chip_info.is_v4x7
                        else "GPIO_Speed_30MHz" if chip_info.is_v00xx
                        else "GPIO_Speed_50MHz"
                    )
                }
        
        @staticmethod
        def generate_standard_ch_code(chip_info, header: str) -> str:
            # Generates standard CH32V main code (non-CH5x)
            gpio_cfg = Ch32vPlatform.NoneOSCodeGenerator.get_gpio_config(chip_info)
            
            return f"""
#include <{header}>
#include <debug.h>

#define BLINKY_GPIO_PORT {gpio_cfg['port']}
#define BLINKY_GPIO_PIN {gpio_cfg['pin']}
#define BLINKY_CLOCK_ENABLE {gpio_cfg['clock_enable']}

void NMI_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void HardFault_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));

int main(void) {{
    SystemCoreClockUpdate();
    Delay_Init();

    GPIO_InitTypeDef GPIO_InitStructure = {{0}};
    BLINKY_CLOCK_ENABLE;
    GPIO_InitStructure.GPIO_Pin = BLINKY_GPIO_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = {gpio_cfg['speed']};
    GPIO_Init(BLINKY_GPIO_PORT, &GPIO_InitStructure);

    uint8_t ledState = 0;
    while (1) {{
        GPIO_WriteBit(BLINKY_GPIO_PORT, BLINKY_GPIO_PIN, ledState);
        ledState ^= 1;
        Delay_Ms(1000);
    }}
    return 0;
}}

void NMI_Handler(void) {{}}
void HardFault_Handler(void)
{{
    while (1)
    {{
    }}
}}
            """
        
        @staticmethod
        def generate_ch5x_code(chip_info, header: str) -> str:
            # Generates CH5x specific main code with proper differentiation
            if chip_info.is_ch56x:
                # CH56x uses different initialization
                init_code = "SystemInit(FREQ_SYS);\n    Delay_Init(FREQ_SYS);"
                gpio_modecfg = "GPIO_Slowascent_PP_16mA"
            elif chip_info.is_ch570_ch572:
                # CH570/CH572 use HSE+PLL clock
                init_code = "SetSysClock(CLK_SOURCE_HSE_PLL_60MHz);"
                gpio_modecfg = "GPIO_ModeOut_PP_20mA"
            elif chip_info.is_ch585_ch584:
                init_code = "SetSysClock(CLK_SOURCE_HSI_PLL_78MHz);"
                gpio_modecfg = "GPIO_ModeOut_PP_20mA"
            else:
                # CH571/CH573/CH58x/CH59x use PLL clock (without HSE prefix)
                init_code = "SetSysClock(CLK_SOURCE_PLL_60MHz);"
                gpio_modecfg = "GPIO_ModeOut_PP_20mA"
            
            return f"""
#include <{header}>
#define BLINKY_GPIO_PIN  GPIO_Pin_8

int main(void)
{{
    {init_code}
    GPIOA_SetBits(BLINKY_GPIO_PIN);
    GPIOA_ModeCfg(BLINKY_GPIO_PIN, {gpio_modecfg});
    while(1) {{
        DelayMs(1000);
        GPIOA_InverseBits(BLINKY_GPIO_PIN);
    }}
}}
            """
        
        @staticmethod
        def generate(chip_info, header: str) -> str:
            # Generates appropriate main code for the chip series
            if chip_info.is_ch5x:
                return Ch32vPlatform.NoneOSCodeGenerator.generate_ch5x_code(chip_info, header)
            else:
                return Ch32vPlatform.NoneOSCodeGenerator.generate_standard_ch_code(chip_info, header)
    
    class FreeRTOSCodeGenerator:
        # Generates FreeRTOS sample code
        
        @staticmethod
        def generate(chip_info) -> tuple[str, str]:
            # Returns (main_code, freertos_config)
            if chip_info.is_ch5x or chip_info.is_ch6x:
                main_code = Ch32vPlatform.FreeRTOSCodeGenerator.generate_minimal_code(chip_info)
                freertos_config = Ch32vPlatform.FreeRTOSCodeGenerator.get_freertos_config_ch5x(chip_info)
            else:
                main_code = Ch32vPlatform.FreeRTOSCodeGenerator.generate_standard_code()
                freertos_config = Ch32vPlatform.FreeRTOSCodeGenerator.get_freertos_config()
            
            return main_code, freertos_config
        
        @staticmethod
        def generate_standard_code() -> str:
            # FreeRTOS code for standard chips (non-CH5x/CH6x)
            return """
#include "debug.h"
#include "FreeRTOS.h"
#include "task.h"

TaskHandle_t example_task_handle;
void example_task(void *pvParameters)
{
    while (1)
    {
        printf("Hello FreeRTOS!\\n");
        vTaskDelay(250);
    }
}

int main(void)
{
    SystemCoreClockUpdate();
    Delay_Init();
    USART_Printf_Init(115200);
    xTaskCreate((TaskFunction_t)example_task,
        (const char *)"example",
        (uint16_t)256,
        (void *)NULL,
        (UBaseType_t)5,
        (TaskHandle_t *)&example_task_handle);
    vTaskStartScheduler();
    while (1)
    {
        printf("shouldn't run at here!!\\n");
    }
}
            """
        
        @staticmethod
        def generate_minimal_code(chip_info=None) -> str:
            # Minimal FreeRTOS code for CH5x/CH6x chips
            if chip_info and (chip_info.is_ch5x or chip_info.is_ch6x):
                # CH5x/CH6x minimal code without debug.h
                return """
#include "FreeRTOS.h"
#include "task.h"

int main(void)
{
    vTaskStartScheduler();
}
            """
            else:
                # Default minimal code (shouldn't be reached in practice)
                return """
#include "debug.h"
#include "FreeRTOS.h"
#include "task.h"

int main(void)
{
    SystemCoreClockUpdate();
    Delay_Init();
    USART_Printf_Init(115200);
    vTaskStartScheduler();
}
            """
        
        @staticmethod
        def get_freertos_config() -> str:
            # FreeRTOS configuration header content
            return """
#ifndef FREERTOS_CONFIG_H
#define FREERTOS_CONFIG_H

/*-----------------------------------------------------------
 * Application specific definitions.
 *
 * These definitions should be adjusted for your particular hardware and
 * application requirements.
 *
 * THESE PARAMETERS ARE DESCRIBED WITHIN THE 'CONFIGURATION' SECTION OF THE
 * FreeRTOS API DOCUMENTATION AVAILABLE ON THE FreeRTOS.org WEB SITE.
 *
 * See http://www.freertos.org/a00110.html.
 *----------------------------------------------------------*/

/* See https://www.freertos.org/Using-FreeRTOS-on-RISC-V.html */

#include <debug.h>
/* don't have MTIME */
#define configMTIME_BASE_ADDRESS     ( 0 )
#define configMTIMECMP_BASE_ADDRESS  ( 0 )

#define configUSE_PREEMPTION            1
#define configUSE_IDLE_HOOK             0
#define configUSE_TICK_HOOK             0
#define configCPU_CLOCK_HZ              SystemCoreClock
#define configTICK_RATE_HZ              ( ( TickType_t ) 500 )
#define configMAX_PRIORITIES            ( 15 )
#define configMINIMAL_STACK_SIZE        ( ( unsigned short ) 256 ) /* Can be as low as 60 but some of the demo tasks that use this constant require it to be higher. */
#define configTOTAL_HEAP_SIZE           ( ( size_t ) ( 12 * 1024 ) )
#define configMAX_TASK_NAME_LEN         ( 16 )
#define configUSE_TRACE_FACILITY        0
#define configUSE_16_BIT_TICKS          0
#define configIDLE_SHOULD_YIELD         0
#define configUSE_MUTEXES               1
#define configQUEUE_REGISTRY_SIZE       8
#define configCHECK_FOR_STACK_OVERFLOW  0
#define configUSE_RECURSIVE_MUTEXES     1
#define configUSE_MALLOC_FAILED_HOOK    0
#define configUSE_APPLICATION_TASK_TAG  0
#define configUSE_COUNTING_SEMAPHORES   1
#define configGENERATE_RUN_TIME_STATS   0
#define configUSE_PORT_OPTIMISED_TASK_SELECTION 0

/* Co-routine definitions. */
#define configUSE_CO_ROUTINES             0
#define configMAX_CO_ROUTINE_PRIORITIES   ( 2 )

/* Software timer definitions. */
#define configUSE_TIMERS                1
#define configTIMER_TASK_PRIORITY       ( configMAX_PRIORITIES - 1 )
#define configTIMER_QUEUE_LENGTH        4
#define configTIMER_TASK_STACK_DEPTH    ( configMINIMAL_STACK_SIZE )



/* Set the following definitions to 1 to include the API function, or zero
to exclude the API function. */
#define INCLUDE_vTaskPrioritySet           1
#define INCLUDE_uxTaskPriorityGet          1
#define INCLUDE_vTaskDelete                1
#define INCLUDE_vTaskCleanUpResources      1
#define INCLUDE_vTaskSuspend               1
#define INCLUDE_vTaskDelayUntil            1
#define INCLUDE_vTaskDelay                 1
#define INCLUDE_eTaskGetState              1
#define INCLUDE_xTimerPendFunctionCall     1
#define INCLUDE_xTaskAbortDelay            1
#define INCLUDE_xTaskGetHandle             1
#define INCLUDE_xSemaphoreGetMutexHolder   1


/* Normal assert() semantics without relying on the provision of an assert.h
header file. */
#define configASSERT( x ) if( ( x ) == 0 ) { taskDISABLE_INTERRUPTS(); printf("err at line %d of file \\"%s\\". \\r\\n ",__LINE__,__FILE__); while(1); }

/* Map to the platform printf function. */
#define configPRINT_STRING( pcString )  printf( pcString )


#endif /* FREERTOS_CONFIG_H */
            """
        
        @staticmethod
        def get_freertos_config_ch5x(chip_info) -> str:
            # FreeRTOS configuration for CH5x series (no debug.h available)
            # Determine which header to include based on chip series
            if chip_info.is_ch56x:
                include_header = '#include "CH56x_common.h"'
            elif chip_info.series == "ch572":
                include_header = '#include "CH57x_common.h"'
            elif chip_info.series == "ch57x":
                include_header = '#include "CH57x_common.h"'
            elif chip_info.series == "ch58x" or chip_info.is_ch585_ch584:
                include_header = '#include "CH58x_common.h"'
            elif chip_info.series == "ch59x":
                include_header = '#include "CH59x_common.h"'
            else:
                include_header = '#include "CH57x_common.h"'  # default fallback
            
            return f"""
#ifndef FREERTOS_CONFIG_H
#define FREERTOS_CONFIG_H

{include_header}
#include <stdio.h>

/*-----------------------------------------------------------
 * Application specific definitions.
 *
 * These definitions should be adjusted for your particular hardware and
 * application requirements.
 *
 * THESE PARAMETERS ARE DESCRIBED WITHIN THE 'CONFIGURATION' SECTION OF THE
 * FreeRTOS API DOCUMENTATION AVAILABLE ON THE FreeRTOS.org WEB SITE.
 *
 * See http://www.freertos.org/a00110.html.
 *----------------------------------------------------------*/

/* See https://www.freertos.org/Using-FreeRTOS-on-RISC-V.html */

/* don't have MTIME */
#define configMTIME_BASE_ADDRESS         ( 0 )
#define configMTIMECMP_BASE_ADDRESS      ( 0 )

#define configUSE_PREEMPTION                    1
#define configUSE_TIME_SLICING                  0
#define configUSE_IDLE_HOOK                     0
#define configUSE_TICK_HOOK                     0
#define configCPU_CLOCK_HZ                      FREQ_SYS
#define configTICK_RATE_HZ                      ( ( TickType_t ) 500 )
#define configMAX_PRIORITIES                    ( 15 )
#define configMINIMAL_STACK_SIZE                ( ( unsigned short ) 128 )
#define configTOTAL_HEAP_SIZE                   ( ( size_t ) ( 12 * 1024 ) )
#define configMAX_TASK_NAME_LEN                 ( 16 )
#define configUSE_TRACE_FACILITY                0
#define configUSE_16_BIT_TICKS                  0
#define configIDLE_SHOULD_YIELD                 0
#define configUSE_MUTEXES                       1
#define configQUEUE_REGISTRY_SIZE               8
#define configCHECK_FOR_STACK_OVERFLOW          0
#define configUSE_RECURSIVE_MUTEXES             1
#define configUSE_MALLOC_FAILED_HOOK            0
#define configUSE_APPLICATION_TASK_TAG          0
#define configUSE_COUNTING_SEMAPHORES           1
#define configGENERATE_RUN_TIME_STATS           0
#define configUSE_PORT_OPTIMISED_TASK_SELECTION 0

/* Co-routine definitions. */
#define configUSE_CO_ROUTINES             0
#define configMAX_CO_ROUTINE_PRIORITIES   ( 2 )

/* Software timer definitions. */
#define configUSE_TIMERS                1
#define configTIMER_TASK_PRIORITY       ( configMAX_PRIORITIES - 1 )
#define configTIMER_QUEUE_LENGTH        4
#define configTIMER_TASK_STACK_DEPTH    ( configMINIMAL_STACK_SIZE )

/* Set the following definitions to 1 to include the API function, or zero
to exclude the API function. */
#define INCLUDE_vTaskPrioritySet           1
#define INCLUDE_uxTaskPriorityGet          1
#define INCLUDE_vTaskDelete                1
#define INCLUDE_vTaskCleanUpResources      1
#define INCLUDE_vTaskSuspend               1
#define INCLUDE_vTaskDelayUntil            1
#define INCLUDE_vTaskDelay                 1
#define INCLUDE_eTaskGetState              1
#define INCLUDE_xTimerPendFunctionCall     1
#define INCLUDE_xTaskAbortDelay            1
#define INCLUDE_xTaskGetHandle             1
#define INCLUDE_xSemaphoreGetMutexHolder   1

/* Normal assert() semantics without relying on the provision of an assert.h
header file. */
#define configASSERT( x ) if( ( x ) == 0 ) {{ taskDISABLE_INTERRUPTS(); printf("err at line %d of file \\"%s\\". \\r\\n ",__LINE__,__FILE__); while(1); }}

/* Map to the platform printf function. */
#define configPRINT_STRING( pcString )  printf( pcString )

#endif /* FREERTOS_CONFIG_H */
            """
          
    class SampleCodeGenerator:
        # Main entry point for sample code generation
        
        def generate_for_framework(self, framework: str, mcu: str, series: str = "") -> dict[str, str]:
            # Generates sample code for the framework
            chip_info = Ch32vPlatform.ChipSeriesInfo(mcu, series)
            
            if framework == "noneos-sdk":
                return self._generate_noneos(chip_info)
            elif framework == "freertos":
                return self._generate_freertos(chip_info)
            else:
                raise NotImplementedError(
                    f"Sample code generation is not implemented for the '{framework}' framework"
                )
        
        def _generate_noneos(self, chip_info) -> dict[str, str]:
            # Generates NoneOS SDK sample code
            header = self._get_noneos_header_for_mcu(chip_info)
            if header is None:
                raise NotImplementedError(
                    "Cannot determine NoneOS SDK header for the selected board"
                )
            
            main_code = Ch32vPlatform.NoneOSCodeGenerator.generate(chip_info, header)
            return {"main.c": main_code}
        
        def _generate_freertos(self, chip_info) -> dict[str, str]:
            # Generates FreeRTOS sample code
            main_code, freertos_config = Ch32vPlatform.FreeRTOSCodeGenerator.generate(chip_info)
            return {
                "main.c": main_code,
                "FreeRTOSConfig.h": freertos_config
            }
        
        @staticmethod
        def _get_noneos_header_for_mcu(chip_info) -> str:
            # Determines the NoneOS SDK header file based on MCU and series
            mcu = chip_info.mcu
            series = chip_info.series
            
            if mcu.startswith("ch32v00") or mcu.startswith("ch32m0"):
                if mcu.startswith("ch32v003"):
                    return "ch32v00x.h"
                else:
                    return "ch32v00X.h"
            elif mcu.startswith("ch32v10"):
                return "ch32v10x.h"
            elif mcu.startswith("ch32v20"):
                return "ch32v20x.h"
            elif mcu.startswith("ch32v30"):
                return "ch32v30x.h"
            elif mcu.startswith("ch32v407"):
                return "ch32v4x7.h"
            elif mcu.startswith("ch32v467"):
                return "ch32v4x7.h"
            elif mcu.startswith("ch32l1"):
                return "ch32l103.h"
            elif mcu.startswith("ch32x0"):
                return "ch32x035.h"
            elif mcu.startswith("ch641"):
                return "ch641.h"
            elif mcu.startswith("ch643"):
                return "ch643.h"
            elif mcu.startswith("ch5"):
                # For CH5x, use the series info to get correct header
                if series == "ch56x":
                    return "CH56x_common.h"
                elif series == "ch572":
                    return "CH57x_common.h"
                elif series == "ch57x":
                    return "CH57x_common.h"
                elif series == "ch58x" or series == "ch585":
                    return "CH58x_common.h"
                elif series == "ch59x":
                    return "CH59x_common.h"
                else:
                    # Fallback: construct from series
                    return series.upper() + "_common.h" if series else None
            return None
        
        def write_files(self, src_dir: str, files: dict[str, str]) -> bool:
            # Create source directory if needed
            if not os.path.isdir(src_dir):
                os.makedirs(src_dir)
            
            # Write all files
            for filename, content in files.items():
                file_path = os.path.join(src_dir, filename)
                with open(file_path, mode="w", encoding="utf8") as fp:
                    fp.write(content.strip())
            
            return True
