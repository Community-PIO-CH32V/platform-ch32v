How to build PlatformIO based project
=====================================

See <https://github.com/cnlohr/ch32v003fun/tree/master/examples/i2c_oled>

1. [Install PlatformIO Core](https://docs.platformio.org/page/core.html)
2. Download [development platform with examples](https://github.com/Community-PIO-CH32V/platform-ch32v/archive/develop.zip)
3. Extract ZIP archive
4. Run these commands:

```shell
# Change directory to example
$ cd platform-ch32v/examples/ch32v003fun-oled

# Build project
$ pio run

# Upload firmware
$ pio run --target upload

# Upload firmware for the specific environment
$ pio run -e ch32v003f4p6_evt_r0 --target upload

# Clean build files
$ pio run --target clean
```
