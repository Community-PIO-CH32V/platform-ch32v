/********************************** (C) COPYRIGHT *******************************
 * File Name          : HAL.h
 * Author             : WCH
 * Version            : V1.0
 * Date               : 2016/05/05
 * Description        :
 *********************************************************************************
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * Attention: This software (modified or not) and binary are used for 
 * microcontroller manufactured by Nanjing Qinheng Microelectronics.
 *******************************************************************************/

/******************************************************************************/
#ifndef __HAL_H
#define __HAL_H

#ifdef __cplusplus
extern "C" {
#endif

#include "config.h"
#include "RTC.h"
#include "SLEEP.h"
#include "KEY.h"
#include "LED.h"

/* hal task Event */
#define LED_BLINK_EVENT       0x0001
#define HAL_KEY_EVENT         0x0002
#define HAL_REG_INIT_EVENT    0x2000
#define HAL_TEST_EVENT        0x4000

/*********************************************************************
 * GLOBAL VARIABLES
 */
extern tmosTaskID halTaskID;

/*********************************************************************
 * GLOBAL FUNCTIONS
 */

/**
 * @brief   Hardware initialization
 */
extern void HAL_Init(void);

/**
 * @brief   HAL processing
 *
 * @param   task_id - The TMOS assigned task ID.
 * @param   events - events to process.  This is a bit map and can
 *                   contain more than one event.
 */
extern tmosEvents HAL_ProcessEvent(tmosTaskID task_id, tmosEvents events);

/**
 * @brief   Initialization of the BLE library
 */
extern void WCHBLE_Init(void);

/**
 * @brief   Get the internal temperature sampling value. 
 *          If the ADC interrupt sampling is used, 
 *          the interrupt is temporarily shielded in this function.
 *
 * @return  Internal temperature sampling value.
 */
extern uint16_t HAL_GetInterTempValue(void);

/**
 * @brief   Internal 32K calibration
 */
extern void Lib_Calibration_LSI(void);

/*********************************************************************
*********************************************************************/

#ifdef __cplusplus
}
#endif

#endif
