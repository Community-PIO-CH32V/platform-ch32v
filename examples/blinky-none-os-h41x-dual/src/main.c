#include <ch32h417.h>
#include <debug.h>

void blink_gpioc(uint16_t pin, unsigned ms_delay) {
    GPIO_InitTypeDef  GPIO_InitStructure={0};
    GPIO_InitStructure.GPIO_Pin = pin;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_Very_High;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_Init(GPIOC, &GPIO_InitStructure);
    uint8_t ledState = 0;
    while(1) {
        Delay_Ms(ms_delay);
        GPIO_WriteBit(GPIOC, pin, (ledState ? Bit_SET : Bit_RESET));
        ledState ^= 1;
    }
}

/* both cores will execute this function, but the V3F wakes up first */
int main(void) {
#if defined(Core_V3F)
    SystemInit(); /* V3F's version of this code will init both V3F and V5F clock. V5F version not available. */
#endif
    SystemAndCoreClockUpdate(); /* V3F and V5F will both discover current clock settings and update variables */
    Delay_Init(); /* initializes each core's own SysTick */
    /* V3F: DEBUG_UART1, TX = PA9, V5F: DEBUG_UART8, TX = PB4 */
    USART_Printf_Init(115200); /* initializes a different UART for each core */

    Delay_Ms(1000);

    printf("SystemClk:%d\r\n", (int) SystemClock);
#if defined(Core_V3F)
    printf("V3F SystemCoreClk:%d\r\n", (int) SystemCoreClock);
#elif defined(Core_V5F)
    printf("V5F SystemCoreClk:%d\r\n", (int) SystemCoreClock);
#endif
    Delay_Ms(500);

    /* this does a runtime check for which code to execute (so techincally both cores have the same code in their firmware for this block, one always useless) */
    /* we could equally do a compile-time check with Core_V3F and Core_V5F, this demonstrates both. */
    if (NVIC_GetCurrentCoreID() == 0) { // V3F
        /* V3F starts up first, enables GPIO C clock, needed by both V3F and V5F */
        RCC_HB2PeriphClockCmd(RCC_HB2Periph_GPIOC, ENABLE);
        printf("Running on V3F\r\n");
        NVIC_WakeUp_V5F(Core_V5F_StartAddr); //wake up V5. Address must be synced with used flash address in linker script for V5F
        HSEM_ITConfig(HSEM_ID0, ENABLE);
        NVIC->SCTLR |= 1<<4;
        RCC_HB1PeriphClockCmd(RCC_HB1Periph_PWR,ENABLE);
        PWR_EnterSTOPMode(PWR_Regulator_ON, PWR_STOPEntry_WFE);
        HSEM_ClearFlag(HSEM_ID0);
        printf("V3F wake up\r\n");
        blink_gpioc(GPIO_Pin_0, 1000); // blink PC0 on V3F slowly
    } else {
        printf("Running on V5F\r\n");
        /* notify V3F that the V5F woke up */
        HSEM_FastTake(HSEM_ID0);
        HSEM_ReleaseOneSem(HSEM_ID0, 0);
        blink_gpioc(GPIO_Pin_1, 333); // blink PC1 on V5F quickly
    }
}