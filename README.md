# CH32V: development platform for [PlatformIO](https://platformio.org)

[![Build Status](https://github.com/Community-PIO-CH32V/platform-ch32v/workflows/Examples/badge.svg)](https://github.com/Community-PIO-CH32V/platform-ch32v/actions)

CH32V series are industrial-grade general-purpose microcontrollers designed based on QingKe 32-bit RISC-V.
The whole series of products into the hardware stack area, fast interrupt entry and other designs, compared to the
standard greatly improved the interrupt response speed.

* [Home](https://registry.platformio.org/platforms/platformio/ch32v) (home page in the PlatformIO Registry)
* [Documentation](https://docs.platformio.org/page/platforms/ch32v.html) (advanced usage, packages, boards, frameworks, etc.)

# Usage

1. [Install PlatformIO](https://platformio.org)
2. Create PlatformIO project and configure a platform option in [platformio.ini](https://docs.platformio.org/page/projectconf.html) file:

## Stable version

```ini
[env:stable]
platform = ch32v
board = ...
...
```

## Development version

```ini
[env:development]
platform = https://github.com/Community-PIO-CH32V/platform-ch32v.git
board = ...
...
```

# Configuration

Please navigate to [documentation](https://docs.platformio.org/page/platforms/ch32v.html).
