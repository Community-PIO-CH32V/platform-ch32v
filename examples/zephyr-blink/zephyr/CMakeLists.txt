# SPDX-License-Identifier: Apache-2.0

# not working at all, doesn't find the new board...
#set(ZEPHYR_EXTRA_MODULES ${CMAKE_CURRENT_LIST_DIR}/zephyrboards)

cmake_minimum_required(VERSION 3.13.1)
include($ENV{ZEPHYR_BASE}/cmake/app/boilerplate.cmake NO_POLICY_SCOPE)
project(blinky)

target_sources(app PRIVATE ../src/main.c)