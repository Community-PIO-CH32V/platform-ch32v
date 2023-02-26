How to build PlatformIO based project
=====================================

1. [Install PlatformIO Core](https://docs.platformio.org/page/core.html)
2. Download [development platform with examples](https://github.com/Community-PIO-CH32V/platform-ch32v/archive/develop.zip)
3. Extract ZIP archive
4. Run these commands:

```shell
# Change directory to example
$ cd platform-ch32v/examples/webserver-ch32v307-none-os

# Build project
$ pio run

# Upload firmware
$ pio run --target upload

# Upload firmware for the specific environment
$ pio run -e ch32v307_evt --target upload

# Clean build files
$ pio run --target clean
```

## Description

This example is supposed to be run on a CH32V307 evaluation board with on-board ethernet jack, like the [CH32V307-EVT](https://www.aliexpress.com/item/1005004449629983.html).

This example opens both a webserver and runs a TCP client with configurable IP and target port in parallel. 

## Wireup

Since the MAC is on the MCU, the MCU needs to control the Ethernet LEDs. It does so on its GPIO pins PC0 and PC1. The development board has "ELED1" and "ELED2" pins. If you want the Ethernet LEDs to function properly, connect ELED1 to PC0 (LINK) and ELED2 to PC1 (DATA).

Further, you need connect an Ethernet cable to your board.

![wireup](board.jpg)

## Configuration

**The IPs and MAC addresses are hardcoded in this example and might not fit your network.** Edit the `lib/HTTP/HTTPS.c` file in regards to variable
```cpp
u8 Basic_Default[BASIC_CFG_LEN] = {
0x57, 0xAB,
01, 02, 03, 04, 05, 06, 192, 168, 0, 10, 255, 255, 255, 0, 192, 168, 0, 1};
```

As the `HTTPS.h` header shows, the contents of this buffer can be decoded as
```cpp
typedef struct Basic_Cfg   //Basic configuration parameters
{
	u8 flag[2];  //Configuration information verification code: 0x57,0xab
	u8 mac[6];
	u8 ip[4];
	u8 mask[4];
	u8 gateway[4];
} *Basic_Cfg;
```
So this configures 192.168.0.10 as the board's IP and 192.168.0.1 as the gateway.

DHCP code examples are also available in the SDK.

## Expected output

On the UART (at 115200 baud), the chip should hopefully detect a connected link:
```
WEB SERVER
SystemClk:96000000
ChipID:30700518
net version:16
ip:
192.168.0.10.
mac addr:38 3b 26 3e d7 90
WCHNET_LibInit Success
SocketIdForListen 0
desport: 1000, srcport: 1000
desip:192.168.0.100
mode 1
__AMAC=1.2.3.4.5.6
__ASIP=192.168.0.10
__AMSK=255.255.255.0
__AGAT=192.168.0.1
PHY Link Success
```
After that, http://192.168.0.10/ can be visited.

![login](login.png)

The login credentials are by default `admin:123`, changable in the `HTTPS.c`.

After that, the main page should load.

![info](info.png)

*Note: The info may only load partially the first few tries. Modern browser like to access the website concurrently, which is not optimal for an embedded device that is overwhelmed.*