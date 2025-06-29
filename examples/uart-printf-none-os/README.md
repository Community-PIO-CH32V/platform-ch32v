How to build PlatformIO based project
=====================================

1. [Install PlatformIO Core](https://docs.platformio.org/page/core.html)
2. Download [development platform with examples](https://github.com/Community-PIO-CH32V/platform-ch32v/archive/develop.zip)
3. Extract ZIP archive
4. Run these commands:

```shell
# Change directory to example
$ cd platform-ch32v/examples/uart-printf-none-os

# Build project
$ pio run

# Upload firmware
$ pio run --target upload

# Upload firmware for the specific environment
$ pio run -e ch32v307_evt --target upload

# Clean build files
$ pio run --target clean
```

Important Notes
---------------

For the WCH NoneOS SDK, you can usually select the `DEBUG` UART output port and override the default. For example, for CH32V00X (X != 3) we have in the `debug.h` header of the SDK:

```cpp
#define DEBUG_UART2_NoRemap   10  //Tx-PA7
#define DEBUG_UART2_Remap1    11  //Tx-PA4
#define DEBUG_UART2_Remap2    12  //Tx-PA2
#define DEBUG_UART2_Remap3    13  //Tx-PD2
#define DEBUG_UART2_Remap4    14  //Tx-PB0
#define DEBUG_UART2_Remap5    15  //Tx-PC4
#define DEBUG_UART2_Remap6    16  //Tx-PA6

#ifndef DEBUG
#define DEBUG   DEBUG_UART1_NoRemap
#endif
```

Meaning the default is on PA4. Other chips like CH32V003 use PD5 as the default output.

```cpp
/* UART Printf Definition */
#define DEBUG_UART1_NoRemap   1  //Tx-PD5
#define DEBUG_UART1_Remap1    2  //Tx-PD0
#define DEBUG_UART1_Remap2    3  //Tx-PD6
#define DEBUG_UART1_Remap3    4  //Tx-PC0

/* DEBUG UATR Definition */
#ifndef DEBUG
#define DEBUG   DEBUG_UART1_NoRemap
#endif
```

Or PA9 for CH32V30x series.

To override the default `DEBUG`, add a `build_flags` [docs](https://docs.platformio.org/en/latest/projectconf/sections/env/options/build/build_flags.html) expression to your `platformio.ini` like

```ini
build_flags =
  -D DEBUG=2
```