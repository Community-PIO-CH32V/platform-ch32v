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

#ifdef CLK_OSC32K
#if (CLK_OSC32K==1)
#define FREQ_RTC    32000
#else
#define FREQ_RTC    32768
#endif
#endif /* CLK_OSC32K */


#define CLK_PER_US                  (1.0 / ((1.0 / FREQ_RTC) * 1000 * 1000))
#define CLK_PER_MS                  (CLK_PER_US * 1000)

#define US_PER_CLK                  (1.0 / CLK_PER_US)
#define MS_PER_CLK                  (US_PER_CLK / 1000.0)

#define RTC_TO_US(clk)              ((uint32_t)((clk) * US_PER_CLK + 0.5))
#define RTC_TO_MS(clk)              ((uint32_t)((clk) * MS_PER_CLK + 0.5))

#define US_TO_RTC(us)               ((uint32_t)((us) * CLK_PER_US + 0.5))
#define MS_TO_RTC(ms)               ((uint32_t)((ms) * CLK_PER_MS + 0.5))

extern volatile uint32_t RTCTigFlag;

/**
 * @brief   Initialize time Service.
 */
void HAL_TimeInit(void);

/**
 * @brief   配置RTC触发时间
 *
 * @param   time    - 触发时间.
 */
extern void RTC_SetTignTime(uint32_t time);

#ifdef __cplusplus
}
#endif

#endif
