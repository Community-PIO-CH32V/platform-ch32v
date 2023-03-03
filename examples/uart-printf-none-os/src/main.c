#if defined(CH32V00X)
#include <ch32v00x.h>
#elif defined(CH32V10X)
#include <ch32v10x.h>
#elif defined(CH32V20X)
#include <ch32v20x.h>
#elif defined(CH32V30X)
#include <ch32v30x.h>
#endif
#include <stdio.h>
#include "debug.h"

int main(void)
{
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
	SystemCoreClockUpdate();
	Delay_Init();
	USART_Printf_Init(115200);
	Delay_Ms(1000); // give serial monitor time to open
	printf("SystemClk: %u\r\n", (unsigned)SystemCoreClock);
	#if defined(CH32V30X)
	printf("ChipID: %08x\r\n", (unsigned)DBGMCU_GetCHIPID());
	#else
	printf("DeviceID: %08x\r\n", (unsigned)DBGMCU_GetDEVID());
	#endif
	printf("This is printf example\r\n");

	while (1)
	{
		Delay_Ms(1000);
		printf("Program over, press reset button\r\n");
	}
}

void NMI_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void NMI_Handler(void) {}
void HardFault_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void HardFault_Handler(void)
{
	while (1)
	{
	}
}