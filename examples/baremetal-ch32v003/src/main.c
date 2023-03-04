// Could be defined here, or in the processor defines.
#define SYSTEM_CORE_CLOCK 48000000

#include "ch32v00x.h"
#include <stdio.h>

#define APB_CLOCK SYSTEM_CORE_CLOCK

// Blinky pin is PC1!

int main()
{
	SystemInit48HSI();

	// Enable GPIOC.
	RCC->APB2PCENR |= RCC_APB2Periph_GPIOC;

	// GPIO C1 Push-Pull, 10MHz Slew Rate Setting
	GPIOC->CFGLR &= ~(0xf<<(4*1));
	GPIOC->CFGLR |= (GPIO_Speed_10MHz | GPIO_CNF_OUT_PP)<<(4*1);

	while(1)
	{
		GPIOC->BSHR = 1 << 1;	 // Turn on GPIOC1
		Delay_Ms( 100 );
		GPIOC->BCR = 1 << 1;    // Turn off GPIOC1
		Delay_Ms( 100 );
	}
}
