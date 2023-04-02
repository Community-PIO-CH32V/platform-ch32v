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
#include "wchble.h"
#endif

#include "ch32v20x.h"

/*********************************************************************
 ��MAC��
 BLE_MAC                                    - �Ƿ��Զ�������Mac��ַ ( Ĭ��:FALSE - ʹ��оƬMac��ַ )����Ҫ��main.c�޸�Mac��ַ����

 ��SLEEP��
 HAL_SLEEP                                  - �Ƿ���˯�߹��� ( Ĭ��:FALSE )
 WAKE_UP_MAX_TIME_US                        - ��ǰ����ʱ�䣬��ϵͳʱ���ȶ�����Ҫʱ��
                                                                                                                                        ��ͣģʽ    - 45
                                                                                                                                       ����ģʽ    - 5
 
 ��TEMPERATION��
 TEM_SAMPLE                                 - �Ƿ�򿪸����¶ȱ仯У׼�Ĺ��ܣ�����У׼��ʱС��10ms( Ĭ��:TRUE )
 
 ��CALIBRATION��
 BLE_CALIBRATION_ENABLE                     - �Ƿ�򿪶�ʱУ׼�Ĺ��ܣ�����У׼��ʱС��10ms( Ĭ��:TRUE )
 BLE_CALIBRATION_PERIOD                     - ��ʱУ׼�����ڣ���λms( Ĭ��:120000 )
 
 ��SNV��
 BLE_SNV                                    - �Ƿ���SNV���ܣ����ڴ������Ϣ( Ĭ��:TRUE )
 BLE_SNV_ADDR                               - SNV��Ϣ�����ַ��ʹ��data flash���( Ĭ��:0x77E00 )
 BLE_SNV_NUM                                - SNV��Ϣ�洢�����������ڿɴ洢�İ�����( Ĭ��:3 )
                                            - ���������SNVNum����������Ҫ��Ӧ�޸�Lib_Write_Flash�����ڲ�����flash��С����СΪSNVBlock*SNVNum

 ��RTC��
 CLK_OSC32K                                 - RTCʱ��ѡ�������������ɫ����ʹ���ⲿ32K( 0 �ⲿ(32768Hz)��Ĭ��:1���ڲ�(32000Hz)��2���ڲ�(32768Hz) )

 ��MEMORY��
 BLE_MEMHEAP_SIZE                           - ����Э��ջʹ�õ�RAM��С����С��6K ( Ĭ��:(1024*6) )

 ��DATA��
 BLE_BUFF_MAX_LEN                           - ����������������( Ĭ��:27 (ATT_MTU=23)��ȡֵ��Χ[27~251] )
 BLE_BUFF_NUM                               - ����������İ�����( Ĭ��:5 )
 BLE_TX_NUM_EVENT                           - ���������¼������Է����ٸ����ݰ�( Ĭ��:1 )
 BLE_TX_POWER                               - ���书��( Ĭ��:LL_TX_POWEER_0_DBM (0dBm) )
 
 ��MULTICONN��
 PERIPHERAL_MAX_CONNECTION                  - ����ͬʱ�����ٴӻ���ɫ( Ĭ��:1 )
 CENTRAL_MAX_CONNECTION                     - ����ͬʱ������������ɫ( Ĭ��:3 )

 **********************************************************************/

/*********************************************************************
 * Ĭ������ֵ
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
#define CLK_OSC32K                          1   // ���������ڴ��޸ģ������ڹ����������Ԥ�������޸ģ������������ɫ����ʹ���ⲿ32K
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

