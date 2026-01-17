#include "ch32fun.h"
#include <stdio.h>

// use defines to make more meaningful names for our GPIO pins
#define PIN_1 PA4
#define PIN_K PA5
#define PIN_BOB PA8
#define PIN_KEVIN PA9

int main()
{
	SystemInit();

	funGpioInitAll(); // no-op on ch5xx

	funPinMode( PIN_1,     GPIO_CFGLR_OUT_10Mhz_PP ); // Set PIN_1 to output
	funPinMode( PIN_K,     GPIO_CFGLR_OUT_10Mhz_PP ); // Set PIN_K to output
	funPinMode( PIN_BOB,   GPIO_CFGLR_OUT_10Mhz_PP ); // Set PIN_BOB to output
	funPinMode( PIN_KEVIN, GPIO_CFGLR_OUT_10Mhz_PP ); // Set PIN_KEVIN to output


	while(1)
	{
		funDigitalWrite( PIN_1,     FUN_HIGH ); // Turn on PIN_1
		funDigitalWrite( PIN_K,     FUN_HIGH ); // Turn on PIN_K
		funDigitalWrite( PIN_BOB,   FUN_HIGH ); // Turn on PIN_BOB
		funDigitalWrite( PIN_KEVIN, FUN_HIGH ); // Turn on PIN_KEVIN
		Delay_Ms( 250 );
		funDigitalWrite( PIN_1,     FUN_LOW );  // Turn off PIN_1
		funDigitalWrite( PIN_K,     FUN_LOW );  // Turn off PIN_K
		funDigitalWrite( PIN_BOB,   FUN_LOW );  // Turn off PIN_BOB
		funDigitalWrite( PIN_KEVIN, FUN_LOW );  // Turn off PIN_KEVIN
		Delay_Ms( 250 );
	}
}
