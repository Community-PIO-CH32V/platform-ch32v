/********************************** (C) COPYRIGHT *******************************
 * File Name          : RTC.h
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
#ifndef __RTC_H
#define __RTC_H

#ifdef __cplusplus
extern "C" {
#endif


extern volatile uint32_t RTCTigFlag;

/**
 * @brief   Initialize time Service.
 */
void HAL_TimeInit(void);

/**
 * @brief   Configure RTC trigger time
 *
 * @param   time    - Trigger time.
 */
extern void RTC_SetTignTime(uint32_t time);

#ifdef __cplusplus
}
#endif

#endif
