#if defined(CH32V00X)
#include <ch32v00X.h>
#endif
#include <stdio.h>
#include "debug.h"

// Look into datasheet which GPIO pin maps to which analog channel
// E.g., PA2 = A0 (PA2 has "ADC_IN0" alternate function)
// Special channels: ADC_Channel_Vrefint and ADC_Channel_OPA
#define ADC_CHANNEL_TO_USE ADC_Channel_0
#define ADC_GPIO_BANK GPIOA
#define ADC_GPIO_PIN GPIO_Pin_2
#define ADC_GPIO_CLOCK RCC_PB2Periph_GPIOA

void ADC_Function_Init(void)
{
    ADC_InitTypeDef ADC_InitStructure = {0};
    GPIO_InitTypeDef GPIO_InitStructure = {0};

    RCC_PB2PeriphClockCmd(ADC_GPIO_CLOCK, ENABLE);
    RCC_PB2PeriphClockCmd(RCC_PB2Periph_ADC1, ENABLE);

    // Determines clock for ADC.
    // At PCLK2 = 48MHz, ADCCLOCK = PCLK2 / 8 = 6MHz
    RCC_ADCCLKConfig(RCC_PCLK2_Div8);

    GPIO_InitStructure.GPIO_Pin = ADC_GPIO_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AIN;
    GPIO_Init(ADC_GPIO_BANK, &GPIO_InitStructure);

    ADC_DeInit(ADC1);
    ADC_InitStructure.ADC_Mode = ADC_Mode_Independent;
    ADC_InitStructure.ADC_ScanConvMode = DISABLE;
    ADC_InitStructure.ADC_ContinuousConvMode = DISABLE;
    ADC_InitStructure.ADC_ExternalTrigConv = ADC_ExternalTrigConv_None;
    ADC_InitStructure.ADC_DataAlign = ADC_DataAlign_Right;
    ADC_InitStructure.ADC_NbrOfChannel = 1;
    ADC_Init(ADC1, &ADC_InitStructure);

    ADC_Cmd(ADC1, ENABLE);

    ADC_BufferCmd(ADC1, ENABLE); // enable buffer
}

u16 Get_ADC_Val(u8 ch)
{
    u16 val = 0;
    ADC_RegularChannelConfig(ADC1, ch, 1, ADC_SampleTime_CyclesMode7);
    ADC_SoftwareStartConvCmd(ADC1, ENABLE);
    while (!ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC))
        ;
    val = ADC_GetConversionValue(ADC1);
    return val;
}

u16 Get_ADC_Average(u8 ch, u8 times)
{
    u32 temp_val = 0;
    u8 t;
    u16 val;

    for (t = 0; t < times; t++)
    {
        temp_val += Get_ADC_Val(ch);
        Delay_Ms(5);
    }

    val = temp_val / times;

    return val;
}

int main(void)
{
    u16 ADC_val;
    s32 val_mv;

    SystemCoreClockUpdate();
    Delay_Init();
    USART_Printf_Init(115200);
    Delay_Ms(1000); // give serial monitor time to open
    printf("SystemClk:%u\r\n", (unsigned)SystemCoreClock);
    printf("DeviceID: %08x\r\n", (unsigned)DBGMCU_GetDEVID());

    ADC_Function_Init();
    while (1)
    {
        ADC_val = Get_ADC_Average(ADC_CHANNEL_TO_USE, 10);
        Delay_Ms(500);
        val_mv = (ADC_val * 3300 / 4096); // Assuming VCC = 3300mV, not really calibrated
        printf("ADC Value (channel %d): %04d = %ld mV \r\n", ADC_CHANNEL_TO_USE, ADC_val, val_mv);
        Delay_Ms(2);
    }
    return 0;
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