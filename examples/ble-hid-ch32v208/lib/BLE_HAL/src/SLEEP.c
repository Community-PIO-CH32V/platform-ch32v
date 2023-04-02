/********************************** (C) COPYRIGHT *******************************
 * File Name          : SLEEP.c
 * Author             : WCH
 * Version            : V1.2
 * Date               : 2022/01/18
 * Description        : Sleep configuration and its initialization
 *********************************************************************************
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * Attention: This software (modified or not) and binary are used for 
 * microcontroller manufactured by Nanjing Qinheng Microelectronics.
 *******************************************************************************/

/******************************************************************************/
/* Header file contains */
#include "HAL.h"

#define US_TO_TICK(us)                  (uint32_t)((us)/(1000000/((CAB_LSIFQ/2))))

#define SLEEP_PERIOD_MIN_US             200
#define SLEEP_PERIOD_MAX_TICK           0xFFD2393F
#define SLEEP_PERIOD_MIN_TICK           US_TO_TICK(SLEEP_PERIOD_MIN_US)
#define HESREADY_TICK                   US_TO_TICK(WAKE_UP_MAX_TIME_US)

/*******************************************************************************
 * @fn          BLE_LowPower
 *
 * @brief       启动睡眠
 *
 * @param   time    - 唤醒的时间点（RTC绝对值）
 *
 * @return      state.
 */
uint32_t BLE_LowPower(uint32_t time)
{
#if(defined(HAL_SLEEP)) && (HAL_SLEEP == TRUE)
    uint32_t current_time;
    uint32_t sleep_period;
    uint32_t wake_time;

    wake_time = time - HESREADY_TICK;

    __disable_irq();
    current_time = RTC_GetCounter();
    sleep_period = wake_time - current_time;

    if((sleep_period < SLEEP_PERIOD_MIN_TICK)
            || (sleep_period > SLEEP_PERIOD_MAX_TICK)) {
        __enable_irq();
        return 2;
    }

    RTC_SetTignTime(wake_time);
    __enable_irq();

  #if(DEBUG == DEBUG_UART1) // To use other serial ports to output printing information, you need to modify this line of code
    while(USART_GetFlagStatus(USART1, USART_FLAG_TC) == RESET)
    {
        __NOP();
    }
  #endif
    // LOW POWER-sleep
    if(!RTCTigFlag) {
        PWR_EnterSTOPMode_RAM_LV(PWR_Regulator_LowPower, PWR_STOPEntry_WFI);
        SystemInit();
    } else {
       return 3; 
    }

#endif
    return 0;
}

/*******************************************************************************
 * @fn      HAL_SleepInit
 *
 * @brief   Configure sleep Wake-up source   - RTC wake up, trigger mode
 *
 * @param   None.
 *
 * @return  None.
 */
void HAL_SleepInit(void)
{
#if(defined(HAL_SLEEP)) && (HAL_SLEEP == TRUE)
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_PWR, ENABLE);
    RTC_WaitForLastTask();

    RTC_ITConfig(RTC_IT_ALR, ENABLE);
    EXTI_InitTypeDef EXTI_InitStructure = {0};
    NVIC_InitTypeDef NVIC_InitStructure = {0};

    EXTI_InitStructure.EXTI_Line = EXTI_Line17;
    EXTI_InitStructure.EXTI_Mode = EXTI_Mode_Interrupt;
    EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Rising;
    EXTI_InitStructure.EXTI_LineCmd = ENABLE;
    EXTI_Init(&EXTI_InitStructure);

    NVIC_InitStructure.NVIC_IRQChannel = RTCAlarm_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 0;
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);
#endif
}
