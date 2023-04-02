/********************************** (C) COPYRIGHT *******************************
 * File Name          : CONFIG.h
 * Author             : WCH
 * Version            : V1.2
 * Date               : 2022/01/18
 * Description        : Configuration description and default value, 
 *                      it is recommended to modify the current value in the 
 *                      pre-processing of the engineering configuration
 *********************************************************************************
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * Attention: This software (modified or not) and binary are used for 
 * microcontroller manufactured by Nanjing Qinheng Microelectronics.
 *******************************************************************************/

/******************************************************************************/
#ifndef __CONFIG_H
#define __CONFIG_H

#define	ID_CH32V208							0x0208

#define CHIP_ID								ID_CH32V208

#ifdef WCHBLE_ROM
#include "WCHBLE_ROM.H"
#else
#include "wchble.H"
#endif

#include "ch32v20x.h"

/*********************************************************************
 【MAC】
 BLE_MAC                                    - 是否自定义蓝牙Mac地址 ( 默认:FALSE - 使用芯片Mac地址 )，需要在main.c修改Mac地址定义

 【SLEEP】
 HAL_SLEEP                                  - 是否开启睡眠功能 ( 默认:FALSE )
 WAKE_UP_MAX_TIME_US                        - 提前唤醒时间，即系统时钟稳定所需要时间
                                                                                                                                        暂停模式    - 45
                                                                                                                                       空闲模式    - 5
 
 【TEMPERATION】
 TEM_SAMPLE                                 - 是否打开根据温度变化校准的功能，单次校准耗时小于10ms( 默认:TRUE )
 
 【CALIBRATION】
 BLE_CALIBRATION_ENABLE                     - 是否打开定时校准的功能，单次校准耗时小于10ms( 默认:TRUE )
 BLE_CALIBRATION_PERIOD                     - 定时校准的周期，单位ms( 默认:120000 )
 
 【SNV】
 BLE_SNV                                    - 是否开启SNV功能，用于储存绑定信息( 默认:TRUE )
 BLE_SNV_ADDR                               - SNV信息保存地址，使用data flash最后( 默认:0x77E00 )
 BLE_SNV_NUM                                - SNV信息存储扇区数量等于可存储的绑定数量( 默认:3 )
                                            - 如果配置了SNVNum参数，则需要对应修改Lib_Write_Flash函数内擦除的flash大小，大小为SNVBlock*SNVNum

 【RTC】
 CLK_OSC32K                                 - RTC时钟选择，如包含主机角色必须使用外部32K( 0 外部(32768Hz)，默认:1：内部(32000Hz)，2：内部(32768Hz) )

 【MEMORY】
 BLE_MEMHEAP_SIZE                           - 蓝牙协议栈使用的RAM大小，不小于6K ( 默认:(1024*6) )

 【DATA】
 BLE_BUFF_MAX_LEN                           - 单个连接最大包长度( 默认:27 (ATT_MTU=23)，取值范围[27~251] )
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
#ifndef HAL_SLEEP
#define HAL_SLEEP                           FALSE
#endif
#ifndef WAKE_UP_MAX_TIME_US
#define WAKE_UP_MAX_TIME_US                 2400
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
#define BLE_SNV_ADDR                        0x08077C00
#endif
#ifndef BLE_SNV_NUM
#define BLE_SNV_NUM                         3
#endif
#ifndef CLK_OSC32K
#define CLK_OSC32K                          1   // 该项请勿在此修改，必须在工程配置里的预处理中修改，如包含主机角色必须使用外部32K
#endif
#ifndef BLE_MEMHEAP_SIZE
#define BLE_MEMHEAP_SIZE                    (1024*7)
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

