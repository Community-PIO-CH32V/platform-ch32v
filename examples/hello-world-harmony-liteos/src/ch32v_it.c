#include "ch32v_it.h"
#include "los_interrupt.h"

void NMI_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void HardFault_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));

void NMI_Handler(void)
{
    GET_INT_SP();
    HalIntEnter();
    while(1)
    {

    }

    HalIntExit();
    FREE_INT_SP();
}

void HardFault_Handler(void)
{

  GET_INT_SP();
  HalIntEnter();

  printf("mcause:%08x\r\n", (unsigned) __get_MCAUSE());
  printf("mtval:%08x\r\n", (unsigned) __get_MTVAL());
  printf("mepc:%08x\r\n", (unsigned) __get_MEPC());

  while (1)
  {
  }
  HalIntExit();
  FREE_INT_SP();
}