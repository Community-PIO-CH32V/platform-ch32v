#if defined(CH32V003)
#include <ch32v00x.h>
#elif defined (CH32VM00X) /* v00{2,4,5,6,7}, m007 */
#include <ch32v00X.h>
#elif defined(CH32V10X)
#include <ch32v10x.h>
#elif defined(CH32V20X)
#include <ch32v20x.h>
#elif defined(CH32V30X) || defined(CH32V31X)
#include <ch32v30x.h>
#elif defined (CH32X03X) /* both X033 and X035 */
#include <ch32x035.h>
#elif defined(CH32L10X)
#include <ch32l103.h>
#endif
#include <stdio.h>
#include "debug.h"

int main(void)
{
	#ifdef NVIC_PriorityGroup_2
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
#else
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
#endif
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