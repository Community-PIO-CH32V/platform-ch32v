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

"""
Arduino

Arduino Wiring-based Framework allows writing cross-platform software to
control devices attached to a wide range of Arduino boards to create all
kinds of creative coding, interactive objects, spaces or physical experiences.

https://github.com/AlexanderMandera/arduino-wch32v003
https://github.com/Community-PIO-CH32V/ArduinoCore-CH32V
"""

import sys
from os.path import join, isfile

from SCons.Script import DefaultEnvironment, SConscript

env = DefaultEnvironment()
mcu = env.BoardConfig().get("build.mcu")
core = env.BoardConfig().get("build.core", "")

# https://github.com/AlexanderMandera/arduino-wch32v003
if core == "ch32v003":
    build_script = join(
        env.PioPlatform().get_package_dir("framework-arduinoch32v003"),
        "tools", "platformio-build.py")
# https://github.com/Community-PIO-CH32V/ArduinoCore-CH32V
elif core == "ch32v":
    build_script = join(
        env.PioPlatform().get_package_dir("framework-arduinoch32v"),
        "tools", "platformio-build.py")
# https://github.com/openwch/arduino_core_ch32
elif core == "openwch":
    build_script = join(
        env.PioPlatform().get_package_dir("framework-arduino-openwch-ch32"),
        "tools", "platformio-build.py")
else:
    sys.stderr.write("Error: Don't know which Arduino core to use for %s!\n" % mcu)
    env.Exit(1)

if not isfile(build_script):
    sys.stderr.write("Error: Missing PlatformIO build script %s!\n" % build_script)
    env.Exit(1)

SConscript(build_script)