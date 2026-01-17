/********************************** (C) COPYRIGHT *******************************
 * File Name          : SLEEP.c
 * Author             : WCH
 * Version            : V1.2
 * Date               : 2022/01/18
 * Description        : 睡眠配置及其初始化
 *********************************************************************************
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * Attention: This software (modified or not) and binary are used for 
 * microcontroller manufactured by Nanjing Qinheng Microelectronics.
 *******************************************************************************/

/******************************************************************************/
/* 头文件包含 */
#include "HAL.h"

uint16_t LSIWakeup_MaxTime;

/*******************************************************************************
 * @fn          CH57x_LowPower
 *
 * @brief       启动睡眠
 *
 * @param       time  - 唤醒的时间点（RTC绝对值）
 *
 * @return      state.
 */
uint32_t CH57x_LowPower(uint32_t time)
{
#if(defined(HAL_SLEEP)) && (HAL_SLEEP == TRUE)
    volatile uint32_t i;
    uint32_t time_tign, time_sleep, time_curr;
    unsigned long irq_status;

    // 提前唤醒
    if (time <= LSIWakeup_MaxTime) {
        time_tign = time + (RTC_MAX_COUNT - LSIWakeup_MaxTime);
    } else {
        time_tign = time - LSIWakeup_MaxTime;
    }

    SYS_DisableAllIrq(&irq_status);
    time_curr = RTC_GetCycleLSI();
    // 检测睡眠时间
    if (time_tign < time_curr) {
        time_sleep = time_tign + (RTC_MAX_COUNT - time_curr);
    } else {
        time_sleep = time_tign - time_curr;
    }

    // 若睡眠时间小于最小睡眠时间或大于最大睡眠时间，则不睡眠
    if ((time_sleep < SLEEP_RTC_MIN_TIME) || 
        (time_sleep > SLEEP_RTC_MAX_TIME)) {
        SYS_RecoverIrq(irq_status);
        return 2;
    }

    RTC_SetTignTime(time_tign);
    SYS_RecoverIrq(irq_status);
#if(DEBUG == Debug_UART0) // 使用其他串口输出打印信息需要修改这行代码
    while((R8_UART_LSR & RB_LSR_TX_ALL_EMP) == 0)
    {
        __nop();
    }
#endif
    // LOW POWER-sleep模式
    if(!RTCTigFlag)
    {
        LowPower_Sleep(RB_PWR_RAM12K | RB_PWR_EXTEND | RB_XT_PRE_EN );
        HSECFG_Current(HSE_RCur_100); // 降为额定电流(低功耗函数中提升了HSE偏置电流)
        return 0;
    }
#endif
    return 3;
}

/*******************************************************************************
 * @fn          GET_WakeUpLSIMaxTime
 *
 * @brief       获取当前提前唤醒时间
 *
 * @param       none
 */
uint16_t GET_WakeUpLSIMaxTime(void)
{
    uint16_t pre_time;

    pre_time = RTC_TO_US(45)+200;
    pre_time = pre_time > 1600 ? pre_time:1600;
    pre_time = US_TO_RTC(pre_time);

    return pre_time;
}

/*******************************************************************************
 * @fn      HAL_SleepInit
 *
 * @brief   配置睡眠唤醒的方式   - RTC唤醒，触发模式
 *
 * @param   None.
 *
 * @return  None.
 */
void HAL_SleepInit(void)
{
#if(defined(HAL_SLEEP)) && (HAL_SLEEP == TRUE)
    sys_safe_access_enable();
    R8_SLP_WAKE_CTRL |= RB_SLP_RTC_WAKE; // RTC唤醒
    sys_safe_access_disable();
    sys_safe_access_enable();
    R8_RTC_MODE_CTRL |= RB_RTC_TRIG_EN;  // 触发模式
    sys_safe_access_disable();
    PFIC_EnableIRQ(RTC_IRQn);
    LSIWakeup_MaxTime = GET_WakeUpLSIMaxTime();
//    PRINT("Pre_time %d\n",LSIWakeup_MaxTime);
#endif
}
