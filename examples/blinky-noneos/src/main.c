#if defined(CH32V00X)
#include <ch32v00x.h>
#elif defined(CH32V10X)
#include <ch32v10x.h>
#elif defined(CH32V20X)
#include <ch32v20x.h>
#elif defined(CH32V30X)
#include <ch32v30x.h>
#endif

#define BLINKY_GPIO_PORT GPIOA
#define BLINKY_GPIO_PIN GPIO_Pin_1
#define BLINKY_CLOCK_ENABLE RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE)

void NMI_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void HardFault_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void Delay_Init(void);
void Delay_Ms(uint32_t n);

int main(void)
{
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
	SystemCoreClockUpdate();
	Delay_Init();

	GPIO_InitTypeDef GPIO_InitStructure = {0};

	BLINKY_CLOCK_ENABLE;
	GPIO_InitStructure.GPIO_Pin = BLINKY_GPIO_PIN;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(BLINKY_GPIO_PORT, &GPIO_InitStructure);

	uint8_t ledState = 0;
	while (1)
	{
		GPIO_WriteBit(BLINKY_GPIO_PORT, BLINKY_GPIO_PIN, ledState);
		ledState ^= 1; // invert for the next run
		Delay_Ms(1000);
	}
}

/* The CH32V10X impelmentation brings its own sepcial debug.h/c implementation with it */
/* All the others are the same as here. Use only this one if possible to minimize code size */
#ifndef CH32V10X
static uint8_t p_us = 0;
static uint16_t p_ms = 0;

void Delay_Init(void)
{
	p_us = SystemCoreClock / 8000000;
	p_ms = (uint16_t)p_us * 1000;
}

void Delay_Ms(uint32_t n)
{
	uint32_t i;

	SysTick->SR &= ~(1 << 0);
	i = (uint32_t)n * p_ms;

	SysTick->CMP = i;
	SysTick->CTLR |= (1 << 4);
	SysTick->CTLR |= (1 << 5) | (1 << 0);

	while ((SysTick->SR & (1 << 0)) != (1 << 0))
		;
	SysTick->CTLR &= ~(1 << 0);
}
#endif

void NMI_Handler(void) {}
void HardFault_Handler(void)
{
	while (1)
	{
	}
}
