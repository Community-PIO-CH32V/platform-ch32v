#if defined(CH56X)
#include <CH56x_common.h>
#elif defined(CH57X)
#include <CH57x_common.h>
#elif defined(CH58X)
#include <CH58x_common.h>
#endif

/* code hardcoded for GPIO bank A at the moment */
#define BLINKY_GPIO_PIN  GPIO_Pin_8

int main(void)
{
    #if defined(CH56X)
    SystemInit(FREQ_SYS);
    Delay_Init(FREQ_SYS);
    #else
    SetSysClock(CLK_SOURCE_PLL_60MHz);
    #endif
    GPIOA_SetBits(BLINKY_GPIO_PIN);
    GPIOA_ModeCfg(BLINKY_GPIO_PIN,
    #if defined(CH56X)
        GPIO_Slowascent_PP_16mA
    #else
        GPIO_ModeOut_PP_20mA
    #endif
    );
    while(1) {
        DelayMs(1000);
        GPIOA_InverseBits(BLINKY_GPIO_PIN);
    }
}
