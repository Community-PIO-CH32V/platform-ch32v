/********************************** (C) COPYRIGHT *******************************
 * File Name          : KEY.h
 * Author             : WCH
 * Version            : V1.0
 * Date               : 2016/04/12
 * Description        :
 *********************************************************************************
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * Attention: This software (modified or not) and binary are used for 
 * microcontroller manufactured by Nanjing Qinheng Microelectronics.
 *******************************************************************************/

/******************************************************************************/
#ifndef __KEY_H
#define __KEY_H

#ifdef __cplusplus
extern "C" {
#endif

/**************************************************************************************************
 *                                              MACROS
 **************************************************************************************************/
#define HAL_KEY_POLLING_VALUE    100

/* Switches (keys) */
#define HAL_KEY_SW_1             0x01  // key1
#define HAL_KEY_SW_2             0x02  // key2
#define HAL_KEY_SW_3             0x04  // key3
#define HAL_KEY_SW_4             0x08  // key4

/* Key definition */

/* 1 - KEY */
#define KEY1_PCENR               (RCC_APB2Periph_GPIOB)
#define KEY2_PCENR               ()
#define KEY3_PCENR               ()
#define KEY4_PCENR               ()

#define KEY1_GPIO                (GPIOB)
#define KEY2_GPIO                ()
#define KEY3_GPIO                ()
#define KEY4_GPIO                ()

#define KEY1_BV                  BV(13)
#define KEY2_BV                  ()
#define KEY3_BV                  ()
#define KEY4_BV                  ()

#define KEY1_IN                  (GPIO_ReadInputDataBit(KEY1_GPIO, KEY1_BV)==0)
#define KEY2_IN                  ()
#define KEY3_IN                  ()
#define KEY4_IN                  ()

#define HAL_PUSH_BUTTON1()       (KEY1_IN) //Add custom button
#define HAL_PUSH_BUTTON2()       (0)
#define HAL_PUSH_BUTTON3()       (0)
#define HAL_PUSH_BUTTON4()       (0)

/**************************************************************************************************
 * TYPEDEFS
 **************************************************************************************************/
typedef void (*halKeyCBack_t)(uint8_t keys);

typedef struct
{
    uint8_t keys; // keys
} keyChange_t;

/**************************************************************************************************
 *                                             GLOBAL VARIABLES
 **************************************************************************************************/

/*********************************************************************
 * FUNCTIONS
 */

/**
 * @brief   Initialize the Key Service
 */
void HAL_KeyInit(void);

/**
 * @brief   This is for internal used by hal_driver
 */
void HAL_KeyPoll(void);

/**
 * @brief   Configure the Key serivce
 *
 * @param   cback - pointer to the CallBack function
 */
void HalKeyConfig(const halKeyCBack_t cback);

/**
 * @brief   Read the Key callback
 */
void HalKeyCallback(uint8_t keys);

/**
 * @brief   Read the Key status
 */
uint8_t HalKeyRead(void);

/**************************************************************************************************
**************************************************************************************************/

#ifdef __cplusplus
}
#endif

#endif
