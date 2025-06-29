#if defined(CH641)
#include <ch641.h>
#elif defined(CH643)
#include <ch643.h>
#endif
#include "debug.h"

#define BLINKY_GPIO_PORT GPIOA
#define BLINKY_GPIO_PIN  GPIO_Pin_0
#define BLINKY_CLOCK_ENABLE RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE)

int main(void)
{
    u8 i = 0;
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
    SystemCoreClockUpdate();
    Delay_Init();
    USART_Printf_Init(115200);
    printf("SystemClk:%d\r\n", (int) SystemCoreClock);
    printf( "ChipID:%08x\r\n", (unsigned) DBGMCU_GetCHIPID() );
    printf("GPIO Toggle TEST\r\n");

    GPIO_InitTypeDef GPIO_InitStructure = {0};
    BLINKY_CLOCK_ENABLE;
    GPIO_InitStructure.GPIO_Pin = BLINKY_GPIO_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(BLINKY_GPIO_PORT, &GPIO_InitStructure);

    while(1) {
        Delay_Ms(1000);
        GPIO_WriteBit(BLINKY_GPIO_PORT, BLINKY_GPIO_PIN, (i == 0) ? (i = Bit_SET) : (i = Bit_RESET)); 
    }
}
