#include "ch32fun.h"
#include <stdio.h>

#if defined(CH32H41x)
#define MODE_OUTPUT GPIO_CNF_OUT_PP, GPIO_Speed_180MHz
#else
#define MODE_OUTPUT GPIO_Speed_10MHz | GPIO_CNF_OUT_PP
#endif

int main()
{
	SystemInit();

	// Enable GPIOs
	funGpioInitAll();
	
	funPinMode( PD0, MODE_OUTPUT );
	funPinMode( PD4, MODE_OUTPUT );
	funPinMode( PD6, MODE_OUTPUT );
	funPinMode( PC0, MODE_OUTPUT );

	while(1)
	{
		funDigitalWrite( PD0, FUN_HIGH );
		funDigitalWrite( PD4, FUN_HIGH );
		funDigitalWrite( PD6, FUN_HIGH );
		funDigitalWrite( PC0, FUN_HIGH );
		Delay_Ms( 250 );
		funDigitalWrite( PD0, FUN_LOW );
		funDigitalWrite( PD4, FUN_LOW );
		funDigitalWrite( PD6, FUN_LOW );
		funDigitalWrite( PC0, FUN_LOW );
		Delay_Ms( 250 );
	}
}
