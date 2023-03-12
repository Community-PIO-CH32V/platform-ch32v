Info
====

This example implements a USB-to-UART bridge from CH32V307EVT/EXAM/USB/USBFS/DEVICE/SimulateCDC.

Meaning:
1. All data received on the USB serial will be written to USART2, TX = PA3
2. All data received on the USART serial (RX = PA2) will be written to the USB serial

In this screenshot, COM5 is the USB-CDC of the CH32V307 and COM6 is a FT232 converter connected onto the USART2.

![bridge](usb_serial_bridge.png)

How to build PlatformIO based project
=====================================

1. [Install PlatformIO Core](https://docs.platformio.org/page/core.html)
2. Download [development platform with examples](https://github.com/Community-PIO-CH32V/platform-ch32v/archive/develop.zip)
3. Extract ZIP archive
4. Run these commands:

```shell
# Change directory to example
$ cd platform-ch32v/examples/usb-cdc-wch32v307-none-os

# Build project
$ pio run

# Upload firmware
$ pio run --target upload

# Upload firmware for the specific environment
$ pio run -e ch32v307_evt --target upload

# Clean build files
$ pio run --target clean
```
