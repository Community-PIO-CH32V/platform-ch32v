#include "debug.h"
#include "FreeRTOS.h"
#include "task.h"

/* Global define */
#define TASK1_TASK_PRIO 5
#define TASK1_STK_SIZE 256
#define TASK2_TASK_PRIO 5
#define TASK2_STK_SIZE 256

/* Task 1 and 2 will blink these LEDs respectively */
#define BLINKY_GPIO_PORT GPIOC
#define BLINKY_GPIO_PIN_1 GPIO_Pin_0
#define BLINKY_GPIO_PIN_2 GPIO_Pin_1
#if defined(CH32L10X) || defined(CH32V4X7)
#define BLINKY_CLOCK_ENABLE RCC_PB2PeriphClockCmd(RCC_PB2Periph_GPIOC, ENABLE)
#else
#define BLINKY_CLOCK_ENABLE RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE)
#endif

/* Global Variable */
TaskHandle_t Task1Task_Handler;
TaskHandle_t Task2Task_Handler;

void GPIO_Toggle_INIT(void)
{
    GPIO_InitTypeDef GPIO_InitStructure = {0};

    BLINKY_CLOCK_ENABLE;
    GPIO_InitStructure.GPIO_Pin = BLINKY_GPIO_PIN_1 | BLINKY_GPIO_PIN_2;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
#if defined(CH32V4X7)
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_High;
#else
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
#endif
    GPIO_Init(BLINKY_GPIO_PORT, &GPIO_InitStructure);
}

void task1_task(void *pvParameters)
{
    while (1)
    {
        printf("task1 entry\r\n");
        GPIO_SetBits(BLINKY_GPIO_PORT, BLINKY_GPIO_PIN_1);
        vTaskDelay(250);
        GPIO_ResetBits(BLINKY_GPIO_PORT, BLINKY_GPIO_PIN_1);
        vTaskDelay(250);
    }
}

void task2_task(void *pvParameters)
{
    while (1)
    {
        printf("task2 entry\r\n");
        GPIO_ResetBits(BLINKY_GPIO_PORT, BLINKY_GPIO_PIN_2);
        vTaskDelay(500);
        GPIO_SetBits(BLINKY_GPIO_PORT, BLINKY_GPIO_PIN_2);
        vTaskDelay(500);
    }
}

int main(void)
{
    #ifdef NVIC_PriorityGroup_2
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
#elif defined(NVIC_PriorityGroup_1)
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
#endif
    SystemCoreClockUpdate();
    Delay_Init();
    USART_Printf_Init(115200);
    Delay_Ms(1000); // give serial monitor time to open

    printf("SystemClk:%u\r\n", (unsigned)SystemCoreClock);
	#if defined(CH32V30X)
	printf("ChipID: %08x\r\n", (unsigned)DBGMCU_GetCHIPID());
	#else
	printf("DeviceID: %08x\r\n", (unsigned)DBGMCU_GetDEVID());
	#endif
    printf("FreeRTOS Kernel Version:%s\r\n", tskKERNEL_VERSION_NUMBER);

    GPIO_Toggle_INIT();
    /* create two task */
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
        printf("shouldn't run at here!!\n");
    }
}
