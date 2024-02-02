/********************************** (C) COPYRIGHT *******************************
 * File Name          : CONFIG.h
 * Author             : WCH
 * Version            : V1.2
 * Date               : 2022/01/18
 * Description        : 配置说明及默认值，建议在工程配置里的预处理中修改当前值
 *********************************************************************************
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * Attention: This software (modified or not) and binary are used for 
 * microcontroller manufactured by Nanjing Qinheng Microelectronics.
 *******************************************************************************/

/******************************************************************************/
#ifndef __CONFIG_H
#define __CONFIG_H

#define	ID_CH592							0x92

#define CHIP_ID								ID_CH592

#ifdef CH59xBLE_ROM
#include "CH59xBLE_ROM.h"
#else
#include "CH59xBLE_LIB.h"
#endif

#include "CH59x_common.h"

/*********************************************************************
 【MAC】
 BLE_MAC                                    - 是否自定义蓝牙Mac地址 ( 默认:FALSE - 使用芯片Mac地址 )，需要在main.c修改Mac地址定义

 【DCDC】
 DCDC_ENABLE                                - 是否使能DCDC ( 默认:FALSE )

 【SLEEP】
 HAL_SLEEP                                  - 是否开启睡眠功能 ( 默认:FALSE )
 SLEEP_RTC_MIN_TIME                         - 非空闲模式下睡眠的最小时间（单位：一个RTC周期）
 SLEEP_RTC_MAX_TIME                         - 非空闲模式下睡眠的最大时间（单位：一个RTC周期）
 WAKE_UP_RTC_MAX_TIME                       - 等待32M晶振稳定时间（单位：一个RTC周期）
                                                                                                                            根据不同睡眠类型取值可分为： 睡眠模式/下电模式  - 45 (默认)
                                                                                                                                                                                                  暂停模式    - 45
                                                                                                                                                                                                  空闲模式    - 5
 【TEMPERATION】
 TEM_SAMPLE                                 - 是否打开根据温度变化校准的功能，单次校准耗时小于10ms( 默认:TRUE )
 
 【CALIBRATION】
 BLE_CALIBRATION_ENABLE                     - 是否打开定时校准的功能，单次校准耗时小于10ms( 默认:TRUE )
 BLE_CALIBRATION_PERIOD                     - 定时校准的周期，单位ms( 默认:120000 )
 
 【SNV】
 BLE_SNV                                    - 是否开启SNV功能，用于储存绑定信息( 默认:TRUE )
 BLE_SNV_ADDR                               - SNV信息保存地址，使用data flash最后512字节( 默认:0x77E00 )
 BLE_SNV_BLOCK                              - SNV信息保存块大小( 默认:256 )
 BLE_SNV_NUM                                - SNV信息保存数量( 默认:1 )

 【RTC】
 CLK_OSC32K                                 - RTC时钟选择，如包含主机角色必须使用外部32K( 0 外部(32768Hz)，默认:1：内部(32000Hz)，2：内部(32768Hz) )

 【MEMORY】
 BLE_MEMHEAP_SIZE                           - 蓝牙协议栈使用的RAM大小，不小于6K ( 默认:(1024*6) )

 【DATA】
 BLE_BUFF_MAX_LEN                           - 单个连接最大包长度( 默认:27 (ATT_MTU=23)，取值范围[27~516] )
 BLE_BUFF_NUM                               - 控制器缓存的包数量( 默认:5 )
 BLE_TX_NUM_EVENT                           - 单个连接事件最多可以发多少个数据包( 默认:1 )
 BLE_TX_POWER                               - 发射功率( 默认:LL_TX_POWEER_0_DBM (0dBm) )
 
 【MULTICONN】
 PERIPHERAL_MAX_CONNECTION                  - 最多可同时做多少从机角色( 默认:1 )
 CENTRAL_MAX_CONNECTION                     - 最多可同时做多少主机角色( 默认:3 )

 **********************************************************************/

/*********************************************************************
 * 默认配置值
 */
#ifndef BLE_MAC
#define BLE_MAC                             FALSE
#endif
#ifndef DCDC_ENABLE
#define DCDC_ENABLE                         FALSE
#endif
#ifndef HAL_SLEEP
#define HAL_SLEEP                           FALSE
#endif
#ifndef SLEEP_RTC_MIN_TIME                   
#define SLEEP_RTC_MIN_TIME                  US_TO_RTC(1000)
#endif
#ifndef SLEEP_RTC_MAX_TIME                   
#define SLEEP_RTC_MAX_TIME                  (RTC_MAX_COUNT - 1000 * 1000 * 30)
#endif
#ifndef WAKE_UP_RTC_MAX_TIME
#define WAKE_UP_RTC_MAX_TIME                US_TO_RTC(1600)
#endif
#ifndef HAL_KEY
#define HAL_KEY                             FALSE
#endif
#ifndef HAL_LED
#define HAL_LED                             FALSE
#endif
#ifndef TEM_SAMPLE
#define TEM_SAMPLE                          TRUE
#endif
#ifndef BLE_CALIBRATION_ENABLE
#define BLE_CALIBRATION_ENABLE              TRUE
#endif
#ifndef BLE_CALIBRATION_PERIOD
#define BLE_CALIBRATION_PERIOD              120000
#endif
#ifndef BLE_SNV
#define BLE_SNV                             TRUE
#endif
#ifndef BLE_SNV_ADDR
#define BLE_SNV_ADDR                        0x77E00-FLASH_ROM_MAX_SIZE
#endif
#ifndef BLE_SNV_BLOCK
#define BLE_SNV_BLOCK                       256
#endif
#ifndef BLE_SNV_NUM
#define BLE_SNV_NUM                         1
#endif
#ifndef CLK_OSC32K
#define CLK_OSC32K                          1   // 该项请勿在此修改，必须在工程配置里的预处理中修改，如包含主机角色必须使用外部32K
#endif
#ifndef BLE_MEMHEAP_SIZE
#define BLE_MEMHEAP_SIZE                    (1024*6)
#endif
#ifndef BLE_BUFF_MAX_LEN
#define BLE_BUFF_MAX_LEN                    27
#endif
#ifndef BLE_BUFF_NUM
#define BLE_BUFF_NUM                        5
#endif
#ifndef BLE_TX_NUM_EVENT
#define BLE_TX_NUM_EVENT                    1
#endif
#ifndef BLE_TX_POWER
#define BLE_TX_POWER                        LL_TX_POWEER_0_DBM
#endif
#ifndef PERIPHERAL_MAX_CONNECTION
#define PERIPHERAL_MAX_CONNECTION           1
#endif
#ifndef CENTRAL_MAX_CONNECTION
#define CENTRAL_MAX_CONNECTION              3
#endif

extern uint32_t MEM_BUF[BLE_MEMHEAP_SIZE / 4];
extern const uint8_t MacAddr[6];

#endif

