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
    wlink_tool = {
        # Windows
        "windows_amd64": "https://github.com/Community-PIO-CH32V/tool-wlink.git#windows",
        "windows_x86": "https://github.com/Community-PIO-CH32V/tool-wlink.git#windows",
        # No Windows ARM64 or ARM32 builds.
        # Linux
        "linux_x86_64": "https://github.com/Community-PIO-CH32V/tool-wlink.git#linux",
        #"linux_i686": "",
        #"linux_aarch64": "",
        #"linux_armv7l": "",
        #"linux_armv6l": "",
        # Mac (Intel and ARM are separate)
        "darwin_x86_64": "https://github.com/Community-PIO-CH32V/tool-wlink.git#mac_x64",
        "darwin_arm64": "https://github.com/Community-PIO-CH32V/tool-wlink.git#mac_arm64"
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
        build_core = variables.get("board_build.core", board_config.get("build.core", "arduino"))
        if "arduino" in frameworks:
            if build_core == "ch32v003":
                self.frameworks["arduino"]["package"] = "framework-arduinoch32v003"
            elif build_core == "ch32v":
                self.frameworks["arduino"]["package"] = "framework-arduinoch32v"
            elif build_core == "openwch":
               self.frameworks["arduino"]["package"] = "framework-arduino-openwch-ch32"
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
            "   load",
            "   monitor reset halt",
            "end",
            "define pio_reset_run_target",
            "   load",
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
                debug["tools"][tool] = {
                    "init_cmds": openocd_reset_cmds + init_cmds,
                    "server": {
                        "package": "tool-openocd-riscv-wch",
                        "executable": "bin/openocd",
                        "arguments": server_args,
                    },
                    # reference opened port
                    "port": "localhost:3333"
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
                    "port": "localhost:2000", # default port of that tool
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

    def get_noneos_header_for_mcu(self, mcu):
        header = None
        if mcu.startswith("ch32v00") or mcu.startswith("ch32m0"):
            if mcu.startswith("ch32v003"):
                header = "ch32v00x.h"
            else:
                header = "ch32v00X.h"
        elif mcu.startswith("ch32v10"):
            header = "ch32v10x.h"
        elif mcu.startswith("ch32v20"):
            header = "ch32v20x.h"
        elif mcu.startswith("ch32v30"):
            header = "ch32v30x.h"
        elif mcu.startswith("ch32l0"):
            header = "ch32l103.h"
        elif mcu.startswith("ch32x0"):
            header = "ch32x035.h"
        elif mcu.startswith("ch641"):
            header = "ch641.h"
        elif mcu.startswith("ch643"):
            header = "ch643.h"
        elif mcu.startswith("ch5"):
            header = mcu[0:len("ch5x")].upper() + "x_common.h"
        return header

    def generate_sample_code(self, config, environment):
        frameworks = config.get(f"env:{environment}", "framework", None)
        if frameworks is None or len(frameworks) != 1 or (len(frameworks) == 1 and frameworks[0] == "arduino"):
            raise NotImplementedError()
        # we've made sure this is a single framework project.
        framework = frameworks[0]
        main_content = ""
        is_cpp_project = False
        board = config.get("env:%s" % environment, "board")
        board_config = self.board_config(board)
        mcu = str(board_config.get("build.mcu", "")).lower()
        additional_files: list[tuple[str, str]] = []
        # commonly needed
        is_l10x = mcu.startswith("ch32l1")
        is_v00Xx = mcu.startswith("ch32m0") or (mcu.startswith("ch32v00") and not mcu.startswith("ch32v003"))
        is_ch6x = mcu.startswith("ch6")
        is_ch5x = mcu.startswith("ch5")
        if framework == "noneos-sdk":
            gpio_port = "GPIOC" if not is_ch6x else "GPIOA"
            gpio_pin = "GPIO_Pin_1" if not is_ch6x else "GPIO_Pin_0"
            gpio_clock_enable = ""
            if is_l10x or is_v00Xx:
                gpio_clock_enable = "RCC_PB2PeriphClockCmd(RCC_PB2Periph_GPIOC, ENABLE)"
            elif is_ch6x:
                gpio_clock_enable = "RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE)"
            else:
                gpio_clock_enable = "RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE)"
            hdr = self.get_noneos_header_for_mcu(mcu)
            if hdr is None:
                raise NotImplementedError(
                    "Cannot determine NoneOS SDK header for the selected board"
                )
            if not is_ch5x:
                main_content = """
#include <%s>
#include <debug.h>

#define BLINKY_GPIO_PORT %s
#define BLINKY_GPIO_PIN %s
#define BLINKY_CLOCK_ENABLE %s

void NMI_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void HardFault_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));

int main(void) {
    SystemCoreClockUpdate();
    Delay_Init();

    GPIO_InitTypeDef GPIO_InitStructure = {0};
    BLINKY_CLOCK_ENABLE;
    GPIO_InitStructure.GPIO_Pin = BLINKY_GPIO_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = %s;
    GPIO_Init(BLINKY_GPIO_PORT, &GPIO_InitStructure);

    uint8_t ledState = 0;
    while (1) {
        GPIO_WriteBit(BLINKY_GPIO_PORT, BLINKY_GPIO_PIN, ledState);
        ledState ^= 1;
        Delay_Ms(1000);
    }
    return 0;
}

void NMI_Handler(void) {}
void HardFault_Handler(void)
{
    while (1)
    {
    }
}
                """ % (
                    hdr,
                    gpio_port,
                    gpio_pin,
                    gpio_clock_enable,
                    "GPIO_Speed_30MHz" if is_v00Xx else "GPIO_Speed_50MHz"
                )
            else:
                is_ch56x = mcu.startswith("ch56")
                init_code = "SetSysClock(CLK_SOURCE_PLL_60MHz);" if not is_ch56x else "SystemInit(FREQ_SYS);\n    Delay_Init(FREQ_SYS);"
                gpio_modecfg = "GPIO_Slowascent_PP_16mA" if is_ch56x else "GPIO_ModeOut_PP_20mA"
                main_content = """
#include <%s>
#define BLINKY_GPIO_PIN  GPIO_Pin_8

int main(void)
{
    %s
    GPIOA_SetBits(BLINKY_GPIO_PIN);
    GPIOA_ModeCfg(BLINKY_GPIO_PIN, %s);
    while(1) {
        DelayMs(1000);
        GPIOA_InverseBits(BLINKY_GPIO_PIN);
    }
}
                """ % (
                    hdr,
                    init_code,
                    gpio_modecfg
                )
        elif framework == "freertos":
            if not is_ch5x and not is_ch6x:
                main_content = """
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
            else:
                main_content = """
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
            additional_files.append((
                "FreeRTOSConfig.h",
                """
#ifndef FREERTOS_CONFIG_H
#define FREERTOS_CONFIG_H
#include "debug.h"

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
            ))
        else:
            raise NotImplementedError(
                "Sample code generation is not implemented for the '%s' framework" % framework
            )

        src_dir = config.get("platformio", "src_dir")
        main_path = os.path.join(src_dir, "main.%s" % ("cpp" if is_cpp_project else "c"))
        if os.path.isfile(main_path):
            return None
        if not os.path.isdir(src_dir):
            os.makedirs(src_dir)
        with open(main_path, mode="w", encoding="utf8") as fp:
            fp.write(main_content.strip())
        for ap in additional_files:
            additional_file_path = os.path.join(src_dir, ap[0])
            with open(additional_file_path, mode="w", encoding="utf8") as fp:
                fp.write(ap[1].strip())
        return True
