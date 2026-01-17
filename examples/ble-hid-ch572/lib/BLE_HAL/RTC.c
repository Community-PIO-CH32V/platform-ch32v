/********************************** (C) COPYRIGHT *******************************
 * File Name          : RTC.c
 * Author             : WCH
 * Version            : V1.2
 * Date               : 2022/01/18
 * Description        : RTC配置及其初始化
 *********************************************************************************
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * Attention: This software (modified or not) and binary are used for 
 * microcontroller manufactured by Nanjing Qinheng Microelectronics.
 *******************************************************************************/

/******************************************************************************/
/* 头文件包含 */
#include "HAL.h"

/*********************************************************************
 * CONSTANTS
 */

/***************************************************
 * Global variables
 */
volatile uint32_t RTCTigFlag;

#define US_TO_TICK(us)                  (uint32_t)((us)/(1000000/(CAB_LSIFQ)))
#define SLEEP_WAIT_HSE_TIME             US_TO_TICK(2400)
#define RTC_MAX_COUNT                   0xA8C00000
uint32_t lsiFrq;

/*******************************************************************************
 * @fn      RTC_SetTignTime
 *
 * @brief   配置RTC触发时间
 *
 * @param   time    - 触发时间.
 *
 * @return  None.
 */
void RTC_SetTignTime(uint32_t time)
{
    sys_safe_access_enable();
    R32_RTC_TRIG = time;
    sys_safe_access_disable();
    RTCTigFlag = 0;
}

/*******************************************************************************
 * @fn          RTC_IRQHandler
 *
 * @brief       RTC中断处理
 *
 * @param       None.
 */
__INTERRUPT
__HIGH_CODE
void RTC_IRQHandler( void )
{
    R8_RTC_FLAG_CTRL =(RB_RTC_TMR_CLR|RB_RTC_TRIG_CLR);
    RTCTigFlag = 1;
}

__HIGH_CODE
static uint32_t SYS_GetClockValue(void)
{
    uint32_t volatile rtc_count;
    do{
        rtc_count = R32_RTC_CNT_LSI;
    }while( rtc_count != R32_RTC_CNT_LSI);
    return rtc_count;
}

__HIGH_CODE
static void SYS_SetPendingIRQ(void)
{
    PFIC_SetPendingIRQ( RTC_IRQn );
}

/*******************************************************************************
 * @fn          BLE_ClockConfig
 *
 * @brief       BLE_ClockConfig
 *
 * @param       conf.
 */
bleClockConfig_t BLE_ClockConfig(uint32_t lsifreq)
{
    bleClockConfig_t conf;

    conf.ClockAccuracy = 2500;
    conf.ClockFrequency = lsifreq;
    conf.ClockMaxCount = RTC_MAX_COUNT;
    conf.getClockValue = SYS_GetClockValue;
    conf.SetPendingIRQ = SYS_SetPendingIRQ;

    return conf;
}

/*******************************************************************************
 * @fn      HAL_Time0Init
 *
 * @brief   系统定时器初始化
 *
 * @param   None.
 *
 * @return  None.
 */
void HAL_TimeInit(void)
{
  bleClockConfig_t conf;
  
  sys_safe_access_enable();
  R8_LSI_CONFIG |= RB_CLK_LSI_PON;
  sys_safe_access_disable();

  lsiFrq = RTC_InitClock( Count_1024 );

  PRINT("lsiFrq = %d\n",lsiFrq);

  RTC_InitTime( 2021,1,28,0,0,0 );

  conf = BLE_ClockConfig(lsiFrq);
  TMOS_TimerInit( &conf );

  sys_safe_access_enable();
  __nop();__nop();
  R8_RTC_MODE_CTRL  |= RB_RTC_TRIG_EN;  // 触发模式
  sys_safe_access_disable();
  PFIC_EnableIRQ(RTC_IRQn);
}

/******************************** endfile @ time ******************************/
