#if defined(CH32V003)
#include <ch32v00x.h>
#elif defined (CH32V00Xx) /* v00{2,4,5,6,7}, m007 */
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
#elif defined(CH32H41X)
#include <ch32h417.h>
#endif
#include <debug.h>

#define BLINKY_GPIO_PORT GPIOC
#define BLINKY_GPIO_PIN GPIO_Pin_1
#if defined(CH32L10X) || defined (CH32V00Xx) // l10x, v00{2,4,5,6,7}, m007
#define BLINKY_CLOCK_ENABLE RCC_PB2PeriphClockCmd(RCC_PB2Periph_GPIOC, ENABLE)
#elif defined(CH32H41X)
#define BLINKY_CLOCK_ENABLE RCC_HB2PeriphClockCmd(RCC_HB2Periph_GPIOC, ENABLE);
#else
#define BLINKY_CLOCK_ENABLE RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE)
#endif

void NMI_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void HardFault_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void Delay_Init(void);
void Delay_Ms(uint32_t n);

int main(void)
{
#ifdef NVIC_PriorityGroup_2
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
#elif defined(NVIC_PriorityGroup_1)
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
#endif
#if defined(CH32H41X)
	SystemInit();
	SystemAndCoreClockUpdate();
#else
	SystemCoreClockUpdate();
#endif
	Delay_Init();

	GPIO_InitTypeDef GPIO_InitStructure = {0};

	BLINKY_CLOCK_ENABLE;
	GPIO_InitStructure.GPIO_Pin = BLINKY_GPIO_PIN;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
	#if defined (CH32V00Xx) // all series have 50Mhz setting except v00X != v003..
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
	#elif defined(CH32H41X)
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_High;
	#else
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	#endif
	GPIO_Init(BLINKY_GPIO_PORT, &GPIO_InitStructure);

	uint8_t ledState = 0;
	while (1)
	{
		GPIO_WriteBit(BLINKY_GPIO_PORT, BLINKY_GPIO_PIN, ledState);
		ledState ^= 1; // invert for the next run
		Delay_Ms(100);
	}
}

void NMI_Handler(void) {}
void HardFault_Handler(void)
{
	while (1)
	{
	}
}
