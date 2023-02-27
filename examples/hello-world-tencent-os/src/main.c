/********************************** (C) COPYRIGHT *******************************
 * File Name          : main.c
 * Author             : WCH
 * Version            : V1.0.0
 * Date               : 2021/06/06
 * Description        : Main program body.
 *********************************************************************************
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * Attention: This software (modified or not) and binary are used for
 * microcontroller manufactured by Nanjing Qinheng Microelectronics.
 *******************************************************************************/

#include "debug.h"
#include "tos_k.h"

#define TASK1_STK_SIZE 1024
k_task_t task1;
__aligned(4) uint8_t task1_stk[TASK1_STK_SIZE];

/* Global define */
#define TASK2_STK_SIZE 1024
k_task_t task2;
__aligned(4) uint8_t task2_stk[TASK2_STK_SIZE];

void task1_entry(void *arg)
{
    while (1)
    {
        printf("###I am task1\r\n");
        tos_task_delay(2000);
    }
}

void task2_entry(void *arg)
{
    while (1)
    {
        printf("***I am task2\r\n");
        tos_task_delay(1000);
    }
}

/*********************************************************************
 * @fn      main
 *
 * @brief   Main program.
 *
 * @return  none
 */
int main(void)
{
    USART_Printf_Init(115200);
    Delay_Init();
    Delay_Ms(1000); // wait for serial monitor to open (SysTick will be reconfigured afterwards, use tos_task_delay!!!)
    SystemCoreClockUpdate();
    printf("SystemClk:%lu\r\n", SystemCoreClock);
#if defined(CH32V30X)
    printf("ChipID: %08x\r\n", (unsigned)DBGMCU_GetCHIPID());
#else
    printf("DeviceID: %08x\r\n", (unsigned)DBGMCU_GetDEVID());
#endif
    printf("Welcome to TencentOS tiny(%s)\r\n", TOS_VERSION);
    tos_knl_init();
    tos_task_create(&task1, "task1", task1_entry, NULL, 3, task1_stk, TASK1_STK_SIZE, 0); // Create task1
    tos_task_create(&task2, "task2", task2_entry, NULL, 3, task2_stk, TASK2_STK_SIZE, 0); // Create task2
    tos_knl_start();

    printf("should not run at here!\r\n");

    while (1)
    {
        asm("nop");
    }
}

void NMI_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void HardFault_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));

void NMI_Handler(void)
{
}
void HardFault_Handler(void)
{
    while (1)
    {
    }
}