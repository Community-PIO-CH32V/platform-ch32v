# CH32V: development platform for [PlatformIO](https://platformio.org)

[![Build Status](https://github.com/Community-PIO-CH32V/platform-ch32v/workflows/Examples/badge.svg)](https://github.com/Community-PIO-CH32V/platform-ch32v/actions)

CH32V series are industrial-grade general-purpose microcontrollers designed based on QingKe 32-bit RISC-V. The whole series of products into the hardware stack area, fast interrupt entry and other designs, compared to the standard greatly improved the interrupt response speed.

This repository is a PlatformIO platform. Just like [platform-ststm32](https://github.com/platformio/platform-ststm32/) etc., it enables the PlatformIO core to work with W.CH CH32V chips. This means in all the IDEs that PlatformIO supports ([VSCode, CLion, etc.](https://docs.platformio.org/en/latest/integration/ide/index.html)), developing and debugging firmwares for CH32V chips is easily possible.

# Media
![vscode debugging](docs/debugging_ch32v003.png)

![platform](docs/platform.png)

# Support
- chips
    - [x] CH32V003 (QingKe V2A)
    - [x] CH32V103 (QingKe V3A)
    - [x] CH32V203 (QingKe V4B)
    - [x] CH32V208 (QingKe V4C)
    - [x] CH32V303 (QingKe V4F)
    - [x] CH32V305 (QingKe V4F)
    - [x] CH32V307 (QingKe V4F)
- frameworks
    - [x] None OS ("Simple Peripheral Library" / native SDK)
    - [x] FreeRTOS
    - [x] (Huawei) Harmony LiteOS
    - [x] RT-Thread
    - [x] TencentOS Lite-M

# Installation

1. [Install PlatformIO](https://platformio.org)
2. Create PlatformIO project and configure a platform option in [platformio.ini](https://docs.platformio.org/page/projectconf.html) file:


## Development version

```ini
[env:development]
platform = https://github.com/Community-PIO-CH32V/platform-ch32v.git
board = ...
...
```

# Configuration

The configuration in regards to the builder scripts etc. are still in progress.