How to build PlatformIO based project
=====================================

Note: You **must** upload both the V3F (master) and V5F (slave) firmware!

Each core will independently blink its own GPIO pin and produce its own debug output.

1. [Install PlatformIO Core](https://docs.platformio.org/page/core.html)
2. Download [development platform with examples](https://github.com/Community-PIO-CH32V/platform-ch32v/archive/develop.zip)
3. Extract ZIP archive
4. Run these commands:

```shell
# Change directory to example
$ cd platform-ch32v/examples/blinky-none-os-h41x-dual

# Build project
$ pio run

# Upload firmware
$ pio run --target upload

# Upload firmware for the specific environment
$ pio run -e genericCH32H417QEU6_V3F --target upload
$ pio run -e genericCH32H417QEU6_V5F --target upload

# Clean build files
$ pio run --target clean
```
