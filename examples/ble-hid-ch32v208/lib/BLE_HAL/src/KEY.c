/********************************** (C) COPYRIGHT *******************************
 * File Name          : KEY.c
 * Author             : WCH
 * Version            : V1.2
 * Date               : 2022/01/18
 * Description        :
 *********************************************************************************
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * Attention: This software (modified or not) and binary are used for 
 * microcontroller manufactured by Nanjing Qinheng Microelectronics.
 *******************************************************************************/

/******************************************************************************/
/* Header file contains */
#include "HAL.h"

/**************************************************************************************************
 *                                        GLOBAL VARIABLES
 **************************************************************************************************/

static uint8_t halKeySavedKeys; /* Keep the last state of the button to query whether there is a key value change */

/**************************************************************************************************
 *                                        FUNCTIONS - Local
 **************************************************************************************************/
static halKeyCBack_t pHalKeyProcessFunction; /* callback function */

/**************************************************************************************************
 * @fn      HAL_KeyInit
 *
 * @brief   Initilize Key Service
 *
 * @param   none
 *
 * @return  None
 **************************************************************************************************/
void HAL_KeyInit(void)
{
    /* Initialize previous key to 0 */
    halKeySavedKeys = 0;
    /* Initialize callback function */
    pHalKeyProcessFunction = NULL;

    RCC_APB2PeriphClockCmd(KEY1_PCENR, ENABLE);
    GPIO_InitTypeDef GPIO_InitStructure;
    GPIO_InitStructure.GPIO_Pin = KEY1_BV;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;
    GPIO_Init(KEY1_GPIO, &GPIO_InitStructure);
}

/**************************************************************************************************
 * @fn      HalKeyConfig
 *
 * @brief   Configure the Key serivce
 *
 * @param   cback - pointer to the CallBack function
 *
 * @return  None
 **************************************************************************************************/
void HalKeyConfig(halKeyCBack_t cback)
{
    /* Register the callback fucntion */
    pHalKeyProcessFunction = cback;
    tmos_start_task(halTaskID, HAL_KEY_EVENT, HAL_KEY_POLLING_VALUE); /* Kick off polling */
}

/**************************************************************************************************
 * @fn      HalKeyRead
 *
 * @brief   Read the current value of a key
 *
 * @param   None
 *
 * @return  keys - current keys status
 **************************************************************************************************/
uint8_t HalKeyRead(void)
{
    uint8_t keys = 0;

    if(HAL_PUSH_BUTTON1())
    { //Read button 1
        keys |= HAL_KEY_SW_1;
    }
    if(HAL_PUSH_BUTTON2())
    { //Read button 1
        keys |= HAL_KEY_SW_2;
    }
    if(HAL_PUSH_BUTTON3())
    { //Read button 1
        keys |= HAL_KEY_SW_3;
    }
    if(HAL_PUSH_BUTTON4())
    { //Read button 1
        keys |= HAL_KEY_SW_4;
    }
    return keys;
}

/**************************************************************************************************
 * @fn      HAL_KeyPoll
 *
 * @brief   Called by hal_driver to poll the keys
 *
 * @param   None
 *
 * @return  None
 **************************************************************************************************/
void HAL_KeyPoll(void)
{
    uint8_t keys = 0;
    if(HAL_PUSH_BUTTON1())
    {
        keys |= HAL_KEY_SW_1;
    }
    if(HAL_PUSH_BUTTON2())
    {
        keys |= HAL_KEY_SW_2;
    }
    if(HAL_PUSH_BUTTON3())
    {
        keys |= HAL_KEY_SW_3;
    }
    if(HAL_PUSH_BUTTON4())
    {
        keys |= HAL_KEY_SW_4;
    }
    if(keys == halKeySavedKeys)
    { /* Exit - since no keys have changed */
        return;
    }
    halKeySavedKeys = keys; /* Store the current keys for comparation next time */
    /* Invoke Callback if new keys were depressed */
    if(keys && (pHalKeyProcessFunction))
    {
        (pHalKeyProcessFunction)(keys);
    }
}

/******************************** endfile @ key ******************************/
