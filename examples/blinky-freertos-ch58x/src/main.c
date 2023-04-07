/********************************** (C) COPYRIGHT *******************************
 * File Name          : main.c
 * Author             : WCH
 * Version            : V1.1
 * Date               : 2022/05/10
 * Description        : FreeRTOS例程，使用硬件压栈，中断嵌套可选，中断函数不再使用修饰
 *                      __attribute__((interrupt("WCH-Interrupt-fast")))，
 *                      中断函数直接按照普通函数定义，只使用HIGHCODE修饰即可。
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * SPDX-License-Identifier: Apache-2.0
 *******************************************************************************/

/******************************************************************************/
/* 头文件包含 */
#include "CH58x_common.h"
#include "FreeRTOS.h"
#include "task.h"
#include "semphr.h"
#include "stdarg.h"

/*********************************************************************
 * GLOBAL TYPEDEFS
 */
#define TASK1_TASK_PRIO     5
#define TASK1_STK_SIZE      256     /* 因在任务中使用了APP_Printf所以栈空间必须要大于APP_Printf中的buf_str的大小+configMINIMAL_STACK_SIZE */
#define TASK2_TASK_PRIO     5
#define TASK2_STK_SIZE      256
#define TASK3_TASK_PRIO     configMAX_PRIORITIES - 1
#define TASK3_STK_SIZE      256

#define BLINKY_GPIO_PIN  GPIO_Pin_8

/* Global Variable */
TaskHandle_t Task1Task_Handler;
TaskHandle_t Task2Task_Handler;
TaskHandle_t Task3Task_Handler;
SemaphoreHandle_t printMutex;
SemaphoreHandle_t xBinarySem;

/*********************************************************************
 * @fn      App_Printf
 *
 * @brief   printf can be used within freertos.
 *
 * @param  *fmt - printf params.
 *
 * @return  none
 */
__HIGH_CODE
void App_Printf(const char *fmt, ...)
{
    char  buf_str[128]; /* 需要注意在这里的内存空间是否足够打印 */
    va_list   v_args;

    va_start(v_args, fmt);
   (void)vsnprintf((char       *)&buf_str[0],
                   (size_t      ) sizeof(buf_str),
                   (char const *) fmt,
                                  v_args);
    va_end(v_args);

    /* 互斥量操作，不可在中断中使用 */
    xSemaphoreTake(printMutex, portMAX_DELAY);
    printf("%s", buf_str);
    xSemaphoreGive(printMutex);
}

/*********************************************************************
 * @fn      task1_task
 *
 * @brief   task1 program.
 *
 * @param  *pvParameters - Parameters point of task1
 *
 * @return  none
 */
__HIGH_CODE
void task1_task(void *pvParameters)
{
    while (1)
    {
        App_Printf("task1 entry 1\n");
        vTaskDelay(configTICK_RATE_HZ / 4);
        App_Printf("task1 entry 2\n");
        vTaskDelay(configTICK_RATE_HZ / 4);
    }
}

/*********************************************************************
 * @fn      task2_task
 *
 * @brief   task2 program.
 *
 * @param  *pvParameters - Parameters point of task2
 *
 * @return  none
 */
__HIGH_CODE
void task2_task(void *pvParameters)
{
    while (1)
    {
        GPIOA_InverseBits(BLINKY_GPIO_PIN);
        App_Printf("task2 entry 1\n");
        vTaskDelay(configTICK_RATE_HZ / 2);
        App_Printf("task2 entry 2\n");
        vTaskDelay(configTICK_RATE_HZ / 2);
    }
}

/*********************************************************************
 * @fn      task3_task
 *
 * @brief   task3 program.
 *
 * @param  *pvParameters - Parameters point of task3
 *
 * @return  none
 */
__HIGH_CODE
void task3_task(void *pvParameters)
{
    xBinarySem = xSemaphoreCreateBinary();
    if(xBinarySem != NULL)
    {
        GPIOA_ModeCfg(GPIO_Pin_12, GPIO_ModeIN_PU);
        GPIOA_ITModeCfg(GPIO_Pin_12, GPIO_ITMode_FallEdge);
        PFIC_EnableIRQ(GPIO_A_IRQn);
        while (1)
        {
            if(xSemaphoreTake(xBinarySem, portMAX_DELAY) == pdTRUE)
            {
                App_Printf("task3 sem get ok\n");
            }
            else
            {
                App_Printf("task3 sem get failed\n");
            }
        }
    }
    else
    {
        App_Printf("task3 sem init failed\n");
    }
}

/*********************************************************************
 * @fn      main
 *
 * @brief   main function.
 *
 * @param   none
 *
 * @return  none
 */
int main(void)
{
#if(defined(DCDC_ENABLE)) && (DCDC_ENABLE == TRUE)
    PWR_DCDCCfg(ENABLE);
#endif
    SetSysClock(CLK_SOURCE_PLL_60MHz);
#if(defined(HAL_SLEEP)) && (HAL_SLEEP == TRUE)
    GPIOA_ModeCfg(GPIO_Pin_All, GPIO_ModeIN_PU);
    GPIOB_ModeCfg(GPIO_Pin_All, GPIO_ModeIN_PU);
#endif
#ifdef DEBUG
    GPIOA_SetBits(bTXD1);
    GPIOA_ModeCfg(bTXD1, GPIO_ModeOut_PP_5mA);
    UART1_DefInit();
#endif
    /* for blinky */
    GPIOA_SetBits(BLINKY_GPIO_PIN);
    GPIOA_ModeCfg(BLINKY_GPIO_PIN, GPIO_ModeOut_PP_20mA);

    PRINT("start.\n");

    printMutex = xSemaphoreCreateMutex();
    if(printMutex == NULL)
    {
        PRINT("printMutex error\n");
        while(1);
    }

    /* create three task */
    xTaskCreate((TaskFunction_t)task3_task,
                (const char *)"task3",
                (uint16_t)TASK3_STK_SIZE,
                (void *)NULL,
                (UBaseType_t)TASK3_TASK_PRIO,
                (TaskHandle_t *)&Task3Task_Handler);

    xTaskCreate((TaskFunction_t)task2_task,
                (const char *)"task2",
                (uint16_t)TASK2_STK_SIZE,
                (void *)NULL,
                (UBaseType_t)TASK2_TASK_PRIO,
                (TaskHandle_t *)&Task2Task_Handler);

    xTaskCreate((TaskFunction_t)task1_task,
                (const char *)"task1",
                (uint16_t)TASK1_STK_SIZE,
                (void *)NULL,
                (UBaseType_t)TASK1_TASK_PRIO,
                (TaskHandle_t *)&Task1Task_Handler);

    vTaskStartScheduler();
    while (1)
    {
        PRINT("shouldn't run at here!!\n");
    }
}

/*********************************************************************
 * @fn      GPIOA_IRQHandler
 *
 * @brief   GPIOA_IRQHandler.
 *
 * @param   none
 *
 * @return  none
 */
__HIGH_CODE
void GPIOA_IRQHandler(void)
{
    /* 本函数可以作为在本工程FreeRTOS中的中断函数写法示例 */
    uint16_t flag;
    portBASE_TYPE xHigherPriorityTaskWoken;
    flag = GPIOA_ReadITFlagPort();
    if((flag & GPIO_Pin_12) != 0)
    {
        xSemaphoreGiveFromISR(xBinarySem, &xHigherPriorityTaskWoken);
        portYIELD_FROM_ISR(xHigherPriorityTaskWoken);   /* 根据需要发起切换请求 */
    }
    GPIOA_ClearITFlagBit(flag); /* 清除中断标志 */
}

/******************************** endfile @ main ******************************/
